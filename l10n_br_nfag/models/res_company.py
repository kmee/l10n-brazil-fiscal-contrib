# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models

from ..constants.nfag import (
    NFAG_ENVIRONMENT_DEFAULT,
    NFAG_ENVIRONMENTS,
    NFAG_QRCODE_URL_DEFAULT,
)


class ResCompany(spec_models.SpecModel):
    _name = "res.company"
    _inherit = ["res.company", "nfag.10.emit"]

    nfag_environment = fields.Selection(
        selection=NFAG_ENVIRONMENTS,
        string="NFAg Environment",
        default=NFAG_ENVIRONMENT_DEFAULT,
    )

    nfag_qrcode_url = fields.Char(
        string="NFAg QR Code URL",
        default=NFAG_QRCODE_URL_DEFAULT,
        help="Address of the NFAg query by QR Code, as published on the "
        "services page of the NFAg portal.",
    )

    nfag10_CNPJ = fields.Char(related="partner_id.nfag10_CNPJ")

    nfag10_IE = fields.Char(related="partner_id.nfag10_IE")

    nfag10_xNome = fields.Char(related="partner_id.nfag10_xNome")

    nfag10_xFant = fields.Char(related="partner_id.name")

    nfag10_enderEmit = fields.Many2one(comodel_name="res.partner", related="partner_id")
