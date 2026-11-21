# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from erpbrasil.base.misc import punctuation_rm

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class ResPartner(spec_models.SpecModel):
    _name = "res.partner"
    _inherit = ["res.partner", "nf3e.10.dest", "nf3e.10.tendeemi"]

    nf3e10_CNPJ = fields.Char(compute="_compute_nf3e_data", store=False)
    nf3e10_CPF = fields.Char(compute="_compute_nf3e_data", store=False)
    nf3e10_xNome = fields.Char(compute="_compute_nf3e_data", store=False)
    nf3e10_IE = fields.Char(compute="_compute_nf3e_data", store=False)
    nf3e10_indIEDest = fields.Selection(related="ind_ie_dest")
    nf3e10_enderDest = fields.Many2one(
        comodel_name="res.partner", compute="_compute_nf3e_data", store=False
    )

    nf3e10_xLgr = fields.Char(compute="_compute_nf3e_address", store=False)
    nf3e10_nro = fields.Char(compute="_compute_nf3e_address", store=False)
    nf3e10_xCpl = fields.Char(compute="_compute_nf3e_address", store=False)
    nf3e10_xBairro = fields.Char(compute="_compute_nf3e_address", store=False)
    nf3e10_cMun = fields.Char(compute="_compute_nf3e_address", store=False)
    nf3e10_xMun = fields.Char(compute="_compute_nf3e_address", store=False)
    nf3e10_CEP = fields.Char(compute="_compute_nf3e_address", store=False)
    nf3e10_UF = fields.Selection(compute="_compute_nf3e_address", store=False)
    nf3e10_fone = fields.Char(compute="_compute_nf3e_address", store=False)
    nf3e10_email = fields.Char(compute="_compute_nf3e_address", store=False)

    @api.depends("is_company", "vat", "legal_name", "name", "l10n_br_ie_code")
    def _compute_nf3e_data(self):
        for rec in self:
            document = rec.cnpj_cpf_stripped or False
            rec.nf3e10_CNPJ = document if document and rec.is_company else False
            rec.nf3e10_CPF = document if document and not rec.is_company else False
            rec.nf3e10_xNome = rec.legal_name or rec.name
            rec.nf3e10_IE = punctuation_rm(rec.l10n_br_ie_code or "") or False
            rec.nf3e10_enderDest = rec

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
    def _compute_nf3e_address(self):
        for rec in self:
            rec.nf3e10_xLgr = rec.street_name
            rec.nf3e10_nro = rec.street_number
            rec.nf3e10_xCpl = rec.street2
            rec.nf3e10_xBairro = rec.district
            rec.nf3e10_cMun = rec.city_id.ibge_code
            rec.nf3e10_xMun = rec.city_id.name
            rec.nf3e10_CEP = punctuation_rm(rec.zip or "") or False
            rec.nf3e10_UF = rec.state_id.code
            rec.nf3e10_fone = punctuation_rm(rec.phone or "").replace(" ", "") or False
            rec.nf3e10_email = rec.email
