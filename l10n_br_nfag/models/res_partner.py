# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from erpbrasil.base.misc import punctuation_rm

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class ResPartner(spec_models.SpecModel):
    _name = "res.partner"
    _inherit = ["res.partner", "nfag.10.dest", "nfag.10.tendeemi"]

    nfag10_CNPJ = fields.Char(compute="_compute_nfag_data", store=False)
    nfag10_CPF = fields.Char(compute="_compute_nfag_data", store=False)
    nfag10_xNome = fields.Char(compute="_compute_nfag_data", store=False)
    nfag10_IE = fields.Char(compute="_compute_nfag_data", store=False)
    nfag10_enderDest = fields.Many2one(
        comodel_name="res.partner", compute="_compute_nfag_data", store=False
    )

    nfag10_xLgr = fields.Char(compute="_compute_nfag_address", store=False)
    nfag10_nro = fields.Char(compute="_compute_nfag_address", store=False)
    nfag10_xCpl = fields.Char(compute="_compute_nfag_address", store=False)
    nfag10_xBairro = fields.Char(compute="_compute_nfag_address", store=False)
    nfag10_cMun = fields.Char(compute="_compute_nfag_address", store=False)
    nfag10_xMun = fields.Char(compute="_compute_nfag_address", store=False)
    nfag10_CEP = fields.Char(compute="_compute_nfag_address", store=False)
    nfag10_UF = fields.Selection(compute="_compute_nfag_address", store=False)
    nfag10_fone = fields.Char(compute="_compute_nfag_address", store=False)
    nfag10_email = fields.Char(compute="_compute_nfag_address", store=False)

    @api.depends("is_company", "vat", "legal_name", "name", "l10n_br_ie_code")
    def _compute_nfag_data(self):
        for rec in self:
            document = rec.cnpj_cpf_stripped or False
            rec.nfag10_CNPJ = document if document and rec.is_company else False
            rec.nfag10_CPF = document if document and not rec.is_company else False
            rec.nfag10_xNome = rec.legal_name or rec.name
            rec.nfag10_IE = punctuation_rm(rec.l10n_br_ie_code or "") or False
            rec.nfag10_enderDest = rec

    @api.depends(
        "street_name",
        "street_number",
        "street2",
        "district",
        "city_id",
        "state_id",
        "zip",
        "phone",
        "email",
    )
    def _compute_nfag_address(self):
        for rec in self:
            rec.nfag10_xLgr = rec.street_name
            rec.nfag10_nro = rec.street_number
            rec.nfag10_xCpl = rec.street2
            rec.nfag10_xBairro = rec.district
            rec.nfag10_cMun = rec.city_id.ibge_code
            rec.nfag10_xMun = rec.city_id.name
            rec.nfag10_CEP = punctuation_rm(rec.zip or "") or False
            rec.nfag10_UF = rec.state_id.code
            rec.nfag10_fone = punctuation_rm(rec.phone or "").replace(" ", "") or False
            rec.nfag10_email = rec.email
