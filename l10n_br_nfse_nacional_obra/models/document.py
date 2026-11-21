# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from erpbrasil.base.misc import punctuation_rm
from nfelib.nfse.bindings.v1_0.tipos_complexos_v1_01 import (
    TcenderExtSimples,
    TcenderObraEvento,
)

from odoo import api, fields, models


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    nfse_obra_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Construction Site",
        compute="_compute_nfse_obra_partner_id",
        store=True,
        readonly=False,
        help="Address of the construction work of the NFS-e (infoObra group).",
    )
    # l10n_br_nfse field, reported as cObra by the NFS-e Nacional
    civil_construction_code = fields.Char(
        compute="_compute_civil_construction_code",
        store=True,
        readonly=False,
    )
    nfse_obra_cib = fields.Char(
        string="Construction Site CIB",
        size=8,
        compute="_compute_nfse_obra_cib",
        store=True,
        readonly=False,
    )
    nfse_obra_insc_imob_fisc = fields.Char(
        string="Construction Site Real Estate Registration",
        size=30,
        compute="_compute_nfse_obra_insc_imob_fisc",
        store=True,
        readonly=False,
    )

    @api.depends("partner_shipping_id")
    def _compute_nfse_obra_partner_id(self):
        for doc in self:
            doc.nfse_obra_partner_id = doc.partner_shipping_id

    def _compute_nfse_obra_code(self, field_name, partner_field):
        # one compute per field, so a value given on create protects only it
        for doc in self:
            doc[field_name] = doc.nfse_obra_partner_id[partner_field] or doc[field_name]

    @api.depends("nfse_obra_partner_id.nfse_cno")
    def _compute_civil_construction_code(self):
        self._compute_nfse_obra_code("civil_construction_code", "nfse_cno")

    @api.depends("nfse_obra_partner_id.nfse_cib")
    def _compute_nfse_obra_cib(self):
        self._compute_nfse_obra_code("nfse_obra_cib", "nfse_cib")

    @api.depends("nfse_obra_partner_id.nfse_insc_imob_fisc")
    def _compute_nfse_obra_insc_imob_fisc(self):
        self._compute_nfse_obra_code("nfse_obra_insc_imob_fisc", "nfse_insc_imob_fisc")

    def _nfse_obra_values(self):
        """Values of the infoObra group (TCInfoObra): the work is identified
        by its CNO, by its CIB or, lacking both, by its address."""
        self.ensure_one()
        values = {}
        if self.civil_construction_code:
            values["cObra"] = self.civil_construction_code.strip()
        elif self.nfse_obra_cib:
            values["cCIB"] = self.nfse_obra_cib.strip()
        elif self.nfse_obra_partner_id:
            values["end"] = self._nfse_obra_address(self.nfse_obra_partner_id)
        else:
            return {}
        if self.nfse_obra_insc_imob_fisc:
            values["inscImobFisc"] = self.nfse_obra_insc_imob_fisc.strip()
        return values

    @api.model
    def _nfse_obra_address(self, partner):
        """TCEnderObraEvento of a partner: the CEP for a Brazilian address,
        the endExt group for an address abroad."""
        values = {
            "xLgr": partner.street_name or partner.street or None,
            "nro": partner.street_number or None,
            "xCpl": partner.street2 or None,
            "xBairro": partner.district or None,
        }
        if partner.country_id and partner.country_id.code != "BR":
            values["endExt"] = TcenderExtSimples(
                cEndPost=partner.zip or None,
                xCidade=partner.city_id.name or partner.city or None,
                xEstProvReg=partner.state_id.name or None,
            )
        else:
            values["CEP"] = punctuation_rm(partner.zip or "") or None
        return TcenderObraEvento(**values)
