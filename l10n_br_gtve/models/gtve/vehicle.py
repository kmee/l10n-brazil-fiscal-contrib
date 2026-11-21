# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class GTVeVehicle(spec_models.SpecModel):
    _name = "l10n_br_gtve.vehicle"
    _inherit = "cte.40.infveiculo"
    _description = "Vehicle of the GTV-e"
    _rec_name = "cte40_placa"

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        required=True,
        ondelete="cascade",
        index=True,
    )

    cte40_placa = fields.Char(string="License Plate", required=True)

    cte40_UF = fields.Selection(string="State")

    cte40_RNTRC = fields.Char(string="RNTRC")
