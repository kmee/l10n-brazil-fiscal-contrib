# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

GNRE_ENVIRONMENTS = [
    ("1", "Produção"),
    ("2", "Homologação"),
]


class ResCompany(models.Model):
    _inherit = "res.company"

    gnre_environment = fields.Selection(
        selection=GNRE_ENVIRONMENTS,
        string="Ambiente da GNRE",
        default="2",
        help="Portal GNRE de testes (homologação) ou de produção.",
    )
