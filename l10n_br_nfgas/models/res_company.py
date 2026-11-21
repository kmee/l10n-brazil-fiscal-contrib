# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models

from ..constants import NFGAS_ENVIRONMENT_DEFAULT, NFGAS_ENVIRONMENTS


class ResCompany(spec_models.SpecModel):
    _name = "res.company"
    _inherit = ["res.company", "nfgas.10.emit"]

    nfgas_environment = fields.Selection(
        selection=NFGAS_ENVIRONMENTS,
        string="NFGas Environment",
        default=NFGAS_ENVIRONMENT_DEFAULT,
    )

    nfgas10_CNPJ = fields.Char(related="partner_id.nfgas10_CNPJ")

    nfgas10_IE = fields.Char(related="partner_id.nfgas10_IE")

    nfgas10_xNome = fields.Char(related="partner_id.nfgas10_xNome")

    nfgas10_xFant = fields.Char(related="partner_id.name")

    nfgas10_enderEmit = fields.Many2one(
        comodel_name="res.partner", related="partner_id"
    )
