# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    vehicle_serial = fields.Char(
        help="Serial of the vehicle reported in the NF-e (nSerie). The "
        "serial number (lot name) is the chassis (VIN).",
    )
    vehicle_engine_number = fields.Char(string="Engine Number")

    def _prepare_nfe40_veicprod_vals(self):
        """Values of the NF-e new vehicle group of this serial number: the
        vehicle model of the product completed with the vehicle data."""
        self.ensure_one()
        model = self.product_id.nfe40_veicProd
        vals = model.copy_data()[0] if model else {}
        vals.update(
            {
                "nfe40_chassi": self.name,
                "nfe40_nSerie": self.vehicle_serial,
                "nfe40_nMotor": self.vehicle_engine_number,
            }
        )
        return vals
