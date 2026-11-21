# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models

from ..constants.nf3e import (
    NF3E_ENVIRONMENT_DEFAULT,
    NF3E_ENVIRONMENTS,
    NF3E_QRCODE_URL_DEFAULT,
)


class ResCompany(spec_models.SpecModel):
    _name = "res.company"
    _inherit = ["res.company", "nf3e.10.emit"]

    nf3e_environment = fields.Selection(
        selection=NF3E_ENVIRONMENTS,
        string="NF3e Environment",
        default=NF3E_ENVIRONMENT_DEFAULT,
    )

    nf3e_qrcode_url = fields.Char(
        string="NF3e QR Code URL",
        default=NF3E_QRCODE_URL_DEFAULT,
        help="Address of the NF3e query by QR Code of the tax authority of the "
        "company state, as published on the NF3e portal.",
    )

    nf3e10_CNPJ = fields.Char(related="partner_id.nf3e10_CNPJ")

    nf3e10_IE = fields.Char(related="partner_id.nf3e10_IE")

    nf3e10_xNome = fields.Char(related="partner_id.nf3e10_xNome")

    nf3e10_xFant = fields.Char(related="partner_id.name")

    nf3e10_enderEmit = fields.Many2one(comodel_name="res.partner", related="partner_id")
