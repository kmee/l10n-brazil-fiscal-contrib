# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    nfe40_veicProd = fields.Many2one(
        comodel_name="nfe.40.veicprod",
        string="New Vehicle Model",
        help="Data shared by the vehicles of this model (color, engine, "
        "weights, RENAVAM codes...). The chassis, serial and engine number "
        "of each vehicle come from its serial number.",
    )
