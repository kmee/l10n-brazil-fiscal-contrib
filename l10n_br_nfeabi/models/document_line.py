# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from ..constants.nfeabi import MODELO_FISCAL_NFEABI

IBSCBS_DOMAINS = ("ibs", "cbs")


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    def _prepare_tax_fields(self, compute_result):
        """In the NF-e ABI the IBS and CBS base is the one of the declarant
        (vBC), after the adjustment and social reducers of the real estate
        regime (LC 214/2025, arts. 257 to 259; NT 2026.001, rules U14), not
        the line amount: rebase the IBS and CBS computed by the engine."""
        document = self.document_id
        if document.document_type_id.code == MODELO_FISCAL_NFEABI:
            self._nfeabi_rebase_ibscbs(compute_result, document._nfeabi_ibscbs_base())
        return super()._prepare_tax_fields(compute_result)

    def _nfeabi_rebase_ibscbs(self, compute_result, base):
        currency = self.company_id.currency_id
        for domain in IBSCBS_DOMAINS:
            tax = compute_result.get("taxes", {}).get(domain)
            if not tax or tax.get("base_type") != "percent":
                continue
            old_value = tax.get("tax_value", 0.0)
            reduction = tax.get("percent_reduction", 0.0) or 0.0
            tax["base"] = currency.round(base * (1 - abs(reduction) / 100))
            tax["tax_value"] = currency.round(
                tax["base"] * tax.get("percent_amount", 0.0) / 100
            )
            if tax.get("tax_include"):
                amount_key = "amount_included"
            else:
                amount_key = "amount_not_included"
            compute_result[amount_key] = (
                compute_result.get(amount_key, 0.0) + tax["tax_value"] - old_value
            )
