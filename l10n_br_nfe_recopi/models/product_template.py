# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    recopi_paper = fields.Boolean(
        string="Immune Paper (RECOPI)",
        help="The NF-e items of this product carry the RECOPI number of the "
        "document.",
    )
