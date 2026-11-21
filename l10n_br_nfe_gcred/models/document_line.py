# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, api, fields, models
from odoo.tools import float_round

from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_ISSUER_COMPANY


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    nfe40_gCred = fields.One2many(
        compute="_compute_nfe40_gCred",
        store=True,
        readonly=False,
    )

    @api.depends("product_id", "icms_base")
    def _compute_nfe40_gCred(self):
        """Keep the presumed credit of the product up to date on the line,
        leaving the other credits typed on the line untouched."""
        for line in self:
            product = line.product_id.with_company(line.company_id)
            code = product.nfe_cred_presumido_code
            if not code or line.document_id.issuer != DOCUMENT_ISSUER_COMPANY:
                line.nfe40_gCred = line.nfe40_gCred
                continue
            percent = product.nfe_cred_presumido_percent
            vals = {
                "nfe40_cCredPresumido": code,
                "nfe40_pCredPresumido": percent,
                "nfe40_vCredPresumido": float_round(
                    line.icms_base * percent / 100, precision_digits=2
                ),
            }
            credit = line.nfe40_gCred.filtered(
                lambda g, code=code: g.nfe40_cCredPresumido == code
            )[:1]
            line.nfe40_gCred = (
                [Command.update(credit.id, vals)] if credit else [Command.create(vals)]
            )
