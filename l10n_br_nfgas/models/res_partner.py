# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from erpbrasil.base.misc import punctuation_rm

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class ResPartner(spec_models.SpecModel):
    _name = "res.partner"
    _inherit = ["res.partner", "nfgas.10.dest", "nfgas.10.tendeemi"]

    nfgas10_CNPJ = fields.Char(compute="_compute_nfgas_data", store=False)
    nfgas10_CPF = fields.Char(compute="_compute_nfgas_data", store=False)
    nfgas10_xNome = fields.Char(compute="_compute_nfgas_data", store=False)
    nfgas10_IE = fields.Char(compute="_compute_nfgas_data", store=False)
    nfgas10_enderDest = fields.Many2one(
        comodel_name="res.partner", compute="_compute_nfgas_data", store=False
    )

    nfgas10_xLgr = fields.Char(compute="_compute_nfgas_address", store=False)
    nfgas10_nro = fields.Char(compute="_compute_nfgas_address", store=False)
    nfgas10_xCpl = fields.Char(compute="_compute_nfgas_address", store=False)
    nfgas10_xBairro = fields.Char(compute="_compute_nfgas_address", store=False)
    nfgas10_cMun = fields.Char(compute="_compute_nfgas_address", store=False)
    nfgas10_xMun = fields.Char(compute="_compute_nfgas_address", store=False)
    nfgas10_CEP = fields.Char(compute="_compute_nfgas_address", store=False)
    nfgas10_UF = fields.Selection(compute="_compute_nfgas_address", store=False)
    nfgas10_fone = fields.Char(compute="_compute_nfgas_address", store=False)
    nfgas10_email = fields.Char(compute="_compute_nfgas_address", store=False)

    @api.depends("is_company", "vat", "legal_name", "name", "l10n_br_ie_code")
    def _compute_nfgas_data(self):
        for rec in self:
            document = rec.cnpj_cpf_stripped or False
            rec.nfgas10_CNPJ = document if document and rec.is_company else False
            rec.nfgas10_CPF = document if document and not rec.is_company else False
            rec.nfgas10_xNome = rec.legal_name or rec.name
            rec.nfgas10_IE = punctuation_rm(rec.l10n_br_ie_code or "") or False
            rec.nfgas10_enderDest = rec

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
    def _compute_nfgas_address(self):
        for rec in self:
            rec.nfgas10_xLgr = rec.street_name
            rec.nfgas10_nro = rec.street_number
            rec.nfgas10_xCpl = rec.street2
            rec.nfgas10_xBairro = rec.district
            rec.nfgas10_cMun = rec.city_id.ibge_code
            rec.nfgas10_xMun = rec.city_id.name
            rec.nfgas10_CEP = punctuation_rm(rec.zip or "") or False
            rec.nfgas10_UF = rec.state_id.code
            rec.nfgas10_fone = punctuation_rm(rec.phone or "").replace(" ", "") or False
            rec.nfgas10_email = rec.email
