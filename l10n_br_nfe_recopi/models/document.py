# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    MODELO_FISCAL_NFCE,
)
from odoo.addons.l10n_br_nfe.models.document import filter_processador_edoc_nfe


def _recopi_check_digit(digits):
    """Modulo 11 with weights 1 to N from the right (MOC 7.0, Visao Geral,
    section 8.5)."""
    total = sum(int(digit) * weight for weight, digit in enumerate(reversed(digits), 1))
    remainder = total % 11
    return "0" if remainder < 2 else str(11 - remainder)


def is_valid_recopi_number(number, today):
    """Rule LB01-30 (rejection 350): aaaammddHHMMSSffffDD, a valid date and
    time from 2013 to today and two check digits."""
    if not number or len(number) != 20 or not number.isdigit():
        return False
    try:
        timestamp = datetime.strptime(number[:14], "%Y%m%d%H%M%S")
    except ValueError:
        return False
    if not 2013 <= timestamp.year <= today.year or timestamp.date() > today:
        return False
    first = _recopi_check_digit(number[:18])
    second = _recopi_check_digit(number[:18] + first)
    return number[18:] == first + second


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    recopi_number = fields.Char(
        string="RECOPI Number",
        size=20,
        copy=False,
        help="Number given by the RECOPI system to this immune paper "
        "operation, reported in the items of immune paper products.",
    )

    @api.constrains("recopi_number")
    def _check_recopi_number(self):
        today = fields.Date.context_today(self)
        for record in self.filtered("recopi_number"):
            if not is_valid_recopi_number(record.recopi_number, today):
                raise ValidationError(_("The RECOPI number is not valid."))

    def _document_check(self):
        result = super()._document_check()
        for record in self.filtered(filter_processador_edoc_nfe):
            if record.issuer == DOCUMENT_ISSUER_COMPANY:
                record._check_nfe40_nRECOPI()
        return result

    def _check_nfe40_nRECOPI(self):
        self.ensure_one()
        lines = self.fiscal_line_ids.filtered("nfe40_nRECOPI")
        if not lines:
            return
        # rule LB01-10 (rejection 348), NT 2013/005
        if self.document_type_id.code == MODELO_FISCAL_NFCE:
            raise UserError(_("The NFC-e does not accept the RECOPI number."))
        today = fields.Date.context_today(self)
        invalid = lines.filtered(
            lambda line: not is_valid_recopi_number(line.nfe40_nRECOPI, today)
        )
        if invalid:
            raise UserError(
                _(
                    "The RECOPI number of these items is not valid "
                    "(rejection 350):\n%(items)s",
                    items="\n".join(
                        line.product_id.display_name or line.name for line in invalid
                    ),
                )
            )
