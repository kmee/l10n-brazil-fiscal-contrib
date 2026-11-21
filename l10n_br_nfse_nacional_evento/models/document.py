# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from erpbrasil.base.misc import punctuation_rm
from nfelib.nfse.bindings.v1_0.tipos_complexos_v1_01 import (
    TcenderecoSimples,
    TcenderExtSimples,
)

from odoo import api, fields, models


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    nfse_event_name = fields.Char(
        string="Event Description",
        size=255,
        help="Description of the artistic, cultural, sports or other event "
        "the service is related to (atvEvento group of the NFS-e Nacional).",
    )
    nfse_event_date_start = fields.Date(string="Event Start")
    nfse_event_date_end = fields.Date(string="Event End")
    nfse_event_code = fields.Char(
        string="Municipal Event Code",
        size=30,
        help="Event identification given by the municipal tax administration. "
        "When informed, the NFS-e reports it instead of the venue address.",
    )
    nfse_event_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Event Venue",
        compute="_compute_nfse_event_partner_id",
        store=True,
        readonly=False,
    )

    @api.depends("partner_shipping_id")
    def _compute_nfse_event_partner_id(self):
        for doc in self:
            doc.nfse_event_partner_id = doc.partner_shipping_id

    def _nfse_event_values(self):
        """Values of the atvEvento group (TCAtvEvento), or an empty dict when
        the document has no event."""
        self.ensure_one()
        if not self.nfse_event_name:
            return {}
        values = {
            "xNome": self.nfse_event_name.strip(),
            "dtIni": self.nfse_event_date_start
            and fields.Date.to_string(self.nfse_event_date_start),
            "dtFim": self.nfse_event_date_end
            and fields.Date.to_string(self.nfse_event_date_end),
        }
        if self.nfse_event_code:
            values["idAtvEvt"] = self.nfse_event_code.strip()
        elif self.nfse_event_partner_id:
            values["end"] = self._nfse_event_address(self.nfse_event_partner_id)
        return values

    @api.model
    def _nfse_event_address(self, partner):
        """TCEnderecoSimples of a partner: the CEP for a Brazilian address,
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
        return TcenderecoSimples(**values)
