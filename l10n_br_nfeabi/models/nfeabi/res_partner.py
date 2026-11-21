# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from erpbrasil.base.misc import punctuation_rm

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models

BRAZIL_BC_CODE = "1058"


class ResPartner(spec_models.SpecModel):
    """Address (TEndereco) of the issuer, the transmitters and the acquirers."""

    _name = "res.partner"
    _inherit = ["res.partner", "nfeabi.10.tendereco"]

    nfeabi10_xLgr = fields.Char(compute="_compute_nfeabi_address", store=False)
    nfeabi10_nro = fields.Char(compute="_compute_nfeabi_address", store=False)
    nfeabi10_xCpl = fields.Char(compute="_compute_nfeabi_address", store=False)
    nfeabi10_xBairro = fields.Char(compute="_compute_nfeabi_address", store=False)
    nfeabi10_cMun = fields.Char(compute="_compute_nfeabi_address", store=False)
    nfeabi10_xMun = fields.Char(compute="_compute_nfeabi_address", store=False)
    nfeabi10_UF = fields.Char(compute="_compute_nfeabi_address", store=False)
    nfeabi10_CEP = fields.Char(compute="_compute_nfeabi_address", store=False)
    nfeabi10_cPais = fields.Char(compute="_compute_nfeabi_address", store=False)
    nfeabi10_xPais = fields.Char(compute="_compute_nfeabi_address", store=False)
    nfeabi10_fone = fields.Char(compute="_compute_nfeabi_address", store=False)

    @api.depends(
        "street_name",
        "street_number",
        "street2",
        "district",
        "city_id",
        "state_id",
        "zip",
        "country_id",
        "phone",
    )
    def _compute_nfeabi_address(self):
        for rec in self:
            rec.nfeabi10_xLgr = rec.street_name
            rec.nfeabi10_nro = rec.street_number
            rec.nfeabi10_xCpl = rec.street2
            rec.nfeabi10_xBairro = rec.district
            rec.nfeabi10_cMun = rec.city_id.ibge_code
            rec.nfeabi10_xMun = rec.city_id.name
            rec.nfeabi10_UF = rec.state_id.code
            rec.nfeabi10_CEP = punctuation_rm(rec.zip or "") or False
            rec.nfeabi10_cPais = rec.country_id.bc_code or False
            # MOC NF-e ABI 1.00a, C15 and C16: 1058=Brasil
            rec.nfeabi10_xPais = (
                "Brasil"
                if rec.country_id.bc_code == BRAZIL_BC_CODE
                else rec.country_id.name or False
            )
            rec.nfeabi10_fone = (
                punctuation_rm(rec.phone or "").replace(" ", "") or False
            )

    def _nfeabi_identification(self):
        """CNPJ or CPF and name of the partner, for the choice of the layout."""
        self.ensure_one()
        document = self.cnpj_cpf_stripped or False
        return {
            "CNPJ": document if document and self.is_company else False,
            "CPF": document if document and not self.is_company else False,
            "xNome": self.legal_name or self.name,
        }
