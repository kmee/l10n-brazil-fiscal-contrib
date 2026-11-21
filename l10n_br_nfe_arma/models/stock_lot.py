# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    arma_barrel_number = fields.Char(
        string="Barrel Serial Number",
        size=15,
        help="Serial number of the barrel of the firearm, reported in the "
        "NF-e (nCano). The serial number (lot name) is the firearm serial.",
    )

    def _prepare_nfe40_arma_vals(self):
        """Values of the NF-e firearm group of this serial number."""
        self.ensure_one()
        product = self.product_id
        return {
            "nfe40_tpArma": product.arma_type,
            "nfe40_nSerie": self.name,
            "nfe40_nCano": self.arma_barrel_number,
            "nfe40_descr": product.arma_description,
        }
