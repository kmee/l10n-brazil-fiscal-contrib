# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    bpe_environment = fields.Selection(
        selection=[("1", "Production"), ("2", "Homologation")],
        string="BP-e Environment",
        default="2",
    )
