# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from erpbrasil.base.misc import punctuation_rm
from nfelib.nfse.bindings.v1_0.tipos_complexos_v1_01 import (
    TcenderImovel,
    TcrtcunidadesImobiliarias,
    TcrtcvaloresBcimoveis,
)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# TSAjusteBCLocImoveis, leiaute 1.04.01 (NT 009)
ADJUSTMENT_TYPES = [
    ("01", "Taxes included in the rent"),
    ("02", "Fees included in the rent"),
    ("03", "Condominium fee included in the rent"),
    ("04", "Social reducer"),
    ("99", "Other amounts included in the rent"),
]


class RealEstateUnit(models.Model):
    _name = "l10n_br_nfse_nacional.real.estate.unit"
    _description = "NFS-e Nacional Real Estate Unit"
    _order = "document_id, id"

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="NFS-e",
        required=True,
        ondelete="cascade",
        index=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Property Address",
        help="Address reported when the unit has no CIB.",
    )
    cib = fields.Char(
        string="CIB",
        size=8,
        help="Brazilian Real Estate Registry code (Cadastro Imobiliario "
        "Brasileiro) of the unit: 7 characters and the check digit.",
    )
    insc_imob_fisc = fields.Char(
        string="Municipal Real Estate Registration",
        size=30,
    )
    adjustment_ids = fields.One2many(
        comodel_name="l10n_br_nfse_nacional.real.estate.adjustment",
        inverse_name="unit_id",
        string="Tax Base Adjustments",
        copy=True,
    )

    @api.constrains("cib", "partner_id")
    def _check_identification(self):
        for unit in self:
            if not unit.cib and not unit.partner_id:
                raise ValidationError(
                    _("Inform the CIB or the address of the real estate unit.")
                )

    def _nfse_binding(self):
        """gUnidImob element (TCRTCUnidadesImobiliarias): the unit is
        identified by its CIB or, lacking it, by its address."""
        self.ensure_one()
        values = {
            "inscImobFisc": self.insc_imob_fisc or None,
            "gAjusteBCLocImoveis": [a._nfse_binding() for a in self.adjustment_ids],
        }
        if self.cib:
            values["cCIB"] = self.cib.strip()
        else:
            partner = self.partner_id
            values["end"] = TcenderImovel(
                CEP=punctuation_rm(partner.zip or "") or None,
                xLgr=partner.street_name or partner.street or None,
                nro=partner.street_number or None,
                xCpl=partner.street2 or None,
                xBairro=partner.district or None,
            )
        return TcrtcunidadesImobiliarias(**values)


class RealEstateAdjustment(models.Model):
    _name = "l10n_br_nfse_nacional.real.estate.adjustment"
    _description = "NFS-e Nacional Real Estate Tax Base Adjustment"
    _order = "unit_id, id"

    unit_id = fields.Many2one(
        comodel_name="l10n_br_nfse_nacional.real.estate.unit",
        string="Real Estate Unit",
        required=True,
        ondelete="cascade",
        index=True,
    )
    currency_id = fields.Many2one(related="unit_id.document_id.currency_id")
    adjustment_type = fields.Selection(
        selection=ADJUSTMENT_TYPES,
        required=True,
        help="Amount included in the rent that is not part of the IBS/CBS base.",
    )
    description = fields.Char(size=150)
    amount = fields.Monetary(required=True)

    @api.constrains("adjustment_type", "description")
    def _check_description(self):
        """Rules E0949 and E0954 (Anexo VI, leiaute 1.04.01 of NT 009)."""
        for adjustment in self:
            if adjustment.adjustment_type == "99" and not adjustment.description:
                raise ValidationError(
                    _("E0949: the adjustment type 99 needs a description.")
                )
            if adjustment.adjustment_type != "99" and adjustment.description:
                raise ValidationError(
                    _("E0954: only the adjustment type 99 takes a description.")
                )

    def _nfse_binding(self):
        """gAjusteBCLocImoveis element (TCRTCValoresBCImoveis)."""
        self.ensure_one()
        return TcrtcvaloresBcimoveis(
            tpAjusteBCLocImoveis=self.adjustment_type,
            xTpAjusteBCLocImoveis=self.description or None,
            vAjusteBCLocImoveis=f"{self.amount:.2f}",
        )
