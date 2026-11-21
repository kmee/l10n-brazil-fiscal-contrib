# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from erpbrasil.base.misc import punctuation_rm

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models

from ...constants.nfeabi import NFEABI_ENVIRONMENT_DEFAULT, NFEABI_ENVIRONMENTS


class ResCompany(spec_models.SpecModel):
    _name = "res.company"
    _inherit = ["res.company", "nfeabi.10.temit"]

    nfeabi_environment = fields.Selection(
        selection=NFEABI_ENVIRONMENTS,
        string="NF-e ABI Environment",
        default=NFEABI_ENVIRONMENT_DEFAULT,
    )

    nfeabi_qrcode_url = fields.Char(
        string="NF-e ABI QR Code URL",
        help="Address of the NF-e ABI query by QR Code published on the NF-e "
        "ABI portal for the environment of the company, without the '?' "
        "(NT 2026.001, item 5.2).",
    )

    nfeabi_key_query_url = fields.Char(
        string="NF-e ABI Key Query URL",
        help="Address of the NF-e ABI query by access key printed on the "
        "DANFE-ABI (tag urlChave, NT 2026.001, item 5.1).",
    )

    nfeabi_technical_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="NF-e ABI Technical Responsible",
        help="Company that develops the NF-e ABI issuing system (group "
        "infRespTec). When empty, the company itself is informed, as the MOC "
        "NF-e ABI (Visão Geral, item 2.2.5) asks for systems developed by the "
        "issuer.",
    )

    nfeabi10_CNPJ = fields.Char(compute="_compute_nfeabi_emit")
    nfeabi10_CPF = fields.Char(compute="_compute_nfeabi_emit")
    nfeabi10_xNome = fields.Char(compute="_compute_nfeabi_emit")
    nfeabi10_xFant = fields.Char(related="partner_id.name")
    nfeabi10_enderEmit = fields.Many2one(
        comodel_name="res.partner", related="partner_id"
    )

    @api.depends("partner_id.cnpj_cpf_stripped", "partner_id.legal_name")
    def _compute_nfeabi_emit(self):
        for company in self:
            values = company.partner_id._nfeabi_identification()
            company.nfeabi10_CNPJ = values["CNPJ"]
            company.nfeabi10_CPF = values["CPF"]
            company.nfeabi10_xNome = values["xNome"]

    def _nfeabi_technical_responsible(self):
        """Values of the infRespTec group (MOC NF-e ABI 1.00a, ZD01)."""
        self.ensure_one()
        partner = self.nfeabi_technical_partner_id or self.partner_id
        return {
            "CNPJ": partner.cnpj_cpf_stripped,
            "xContato": partner.legal_name or partner.name,
            "email": partner.email,
            "fone": punctuation_rm(partner.phone or "").replace(" ", ""),
        }
