# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from ..constants import DCE_ISSUER_OWN, DCE_ISSUER_TYPES


class ResCompany(models.Model):
    _inherit = "res.company"

    dce_environment = fields.Selection(
        selection=[("1", "Production"), ("2", "Homologation")],
        string="DC-e Environment",
        default="2",
    )

    dce_issuer_type = fields.Selection(
        selection=DCE_ISSUER_TYPES,
        string="DC-e Issuer Type",
        default=DCE_ISSUER_OWN,
        help="Own issuer: the company declares the goods it sends. Marketplace "
        "or carrier: the company issues the DC-e on behalf of the sender.",
    )

    dce_marketplace_site = fields.Char(
        string="DC-e Marketplace Site",
        help="Address of the marketplace site (Marketplace/Site of the DC-e).",
    )
