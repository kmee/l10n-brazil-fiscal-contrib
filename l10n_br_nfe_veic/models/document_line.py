# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    def _nfe40_fill_veicprod(self, lots):
        """Build the new vehicle group from the serial number shipped. The
        group describes a single vehicle, so an item with several serial
        numbers is left untouched."""
        self.ensure_one()
        if len(lots) != 1 or not lots.product_id.nfe40_veicProd:
            return
        self.nfe40_veicProd = self.env["nfe.40.veicprod"].create(
            lots._prepare_nfe40_veicprod_vals()
        )
