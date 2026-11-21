# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    MODELO_FISCAL_NFCE,
)
from odoo.addons.l10n_br_nfe.models.document import filter_processador_edoc_nfe

# leiauteNFe_v4.00.xsd: <forDia maxOccurs="31"> and <deduc maxOccurs="10">
FORDIA_MAX_OCCURS = 31
DEDUC_MAX_OCCURS = 10


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _document_check(self):
        result = super()._document_check()
        for record in self.filtered(filter_processador_edoc_nfe):
            if record.issuer == DOCUMENT_ISSUER_COMPANY and record.nfe40_cana:
                record._check_nfe40_cana()
        return result

    def _check_nfe40_cana(self):
        """Refuse to issue an NF-e with a sugarcane group the SEFAZ would
        reject: an NFC-e (rule ZC01-10 of the MOC), no daily supply, more
        than 31 daily supplies or more than 10 deductions."""
        self.ensure_one()
        cana = self.nfe40_cana
        errors = []
        if self.document_type == MODELO_FISCAL_NFCE:
            errors.append(_("The NFC-e does not accept the sugarcane group."))
        if not 1 <= len(cana.nfe40_forDia) <= FORDIA_MAX_OCCURS:
            errors.append(
                _(
                    "The sugarcane group needs 1 to %(max)s daily supplies.",
                    max=FORDIA_MAX_OCCURS,
                )
            )
        if len(cana.nfe40_deduc) > DEDUC_MAX_OCCURS:
            errors.append(
                _(
                    "The sugarcane group accepts at most %(max)s deductions.",
                    max=DEDUC_MAX_OCCURS,
                )
            )
        if errors:
            raise UserError(
                _(
                    "The NF-e sugarcane acquisition data (cana) is invalid:\n"
                    "%(errors)s",
                    errors="\n".join(errors),
                )
            )
