# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    nfe40_comb = fields.Many2one(
        comodel_name="nfe.40.comb",
        string="Fuel (ANP)",
        help="ANP product code and fuel details copied to the fuel group of "
        "the NF-e items of this product.",
    )
