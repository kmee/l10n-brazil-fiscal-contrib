# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    nfse_cno = fields.Char(
        string="CNO/CEI",
        size=30,
        help="Construction work registration (Cadastro Nacional de Obras, or "
        "the former CEI) of this address, reported as cObra in the NFS-e "
        "Nacional.",
    )
    nfse_cib = fields.Char(
        string="CIB",
        size=8,
        help="Brazilian Real Estate Registry code (Cadastro Imobiliario "
        "Brasileiro) of this address: 7 characters and the check digit.",
    )
    nfse_insc_imob_fisc = fields.Char(
        string="Municipal Real Estate Registration",
        size=30,
        help="Registration given by the municipality to identify the "
        "construction work or the property for the IPTU.",
    )
