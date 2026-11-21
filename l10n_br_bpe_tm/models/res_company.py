# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    bpe_tm_tar = fields.Char(
        string="BP-e TM TAR",
        size=20,
        help="Termo de Autorizacao de Servico Regular (emit/TAR of the BP-e TM): "
        "registration of the company with the state regulatory agency or the "
        "ANTT, required in the road modal (NT BP-e 2020.002, rule H26).",
    )
