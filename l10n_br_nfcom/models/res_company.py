# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.l10n_br_nfcom_spec.models.v1_0.tipos_geral_nfcom_v1_00 import TAMB


class ResCompany(models.Model):
    _inherit = "res.company"

    nfcom_environment = fields.Selection(
        selection=TAMB,
        string="NFCom Environment",
        default="2",
        help="1 - Production, 2 - Homologation.",
    )
