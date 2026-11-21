# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    nfe40_obsItem = fields.Many2one(
        comodel_name="nfe.40.obsitem",
        string="NF-e Item Observations",
        help="Observations of the taxpayer (obsCont) and of the tax authority "
        "(obsFisco) reported in the NF-e items of this product.",
    )
