# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    MODELO_FISCAL_NFCE,
)
from odoo.addons.l10n_br_nfe.models.document import filter_processador_edoc_nfe


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _document_check(self):
        result = super()._document_check()
        for record in self.filtered(filter_processador_edoc_nfe):
            if record.issuer == DOCUMENT_ISSUER_COMPANY:
                record._check_nfe40_veicprod()
        return result

    def _check_nfe40_veicprod(self):
        """Refuse to issue an NF-e the SEFAZ would reject because of the new
        vehicle group of its items."""
        self.ensure_one()
        lines = self.fiscal_line_ids.filtered("nfe40_veicProd")
        if not lines:
            return
        # rule J01-10 (rejection 736), NT 2013/005
        if self.document_type_id.code == MODELO_FISCAL_NFCE:
            raise UserError(_("The NFC-e does not accept the new vehicle group."))
        errors = []
        for line in lines:
            missing = line.nfe40_veicProd._nfe40_missing_fields()
            if missing:
                errors.append(
                    _(
                        "%(item)s: %(fields)s.",
                        item=line.product_id.display_name or line.name,
                        fields=", ".join(missing),
                    )
                )
        if errors:
            raise UserError(
                _(
                    "The NF-e new vehicle data (veicProd) is incomplete, these "
                    "fields are required:\n%(errors)s",
                    errors="\n".join(errors),
                )
            )
