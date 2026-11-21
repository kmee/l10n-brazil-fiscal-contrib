# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    arma_type = fields.Selection(
        selection=[("0", "Permitted use"), ("1", "Restricted use")],
        string="Firearm Type",
        help="Set it on firearms: their NF-e items carry one firearm group "
        "per serial number shipped.",
    )
    arma_description = fields.Char(
        string="Firearm Description",
        size=256,
        help="Full description of the firearm: caliber, brand, capacity, "
        "action type, length and other details that identify it.",
    )
