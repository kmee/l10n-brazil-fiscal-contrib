# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, models


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    def _nfe40_fill_arma(self, lots):
        """Build one firearm group per serial number shipped."""
        self.ensure_one()
        lots = lots.filtered(lambda lot: lot.product_id.arma_type)
        if not lots:
            return
        self.nfe40_arma = [Command.clear()] + [
            Command.create(lot._prepare_nfe40_arma_vals()) for lot in lots
        ]
