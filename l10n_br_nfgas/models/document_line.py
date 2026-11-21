# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models

from ..constants import NFGAS_CCLASS, NFGAS_ICMS_GROUP_BY_CST


class NFGasLine(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document.line"
    _inherit = ["l10n_br_fiscal.document.line", "nfgas.10.det"]

    _nfgas10_odoo_module = (
        "odoo.addons.l10n_br_nfgas_spec.models.v1_0.nfgas_tipos_basico_v1_00"
    )
    _nfgas10_stacking_mixin = "nfgas.10.det"
    # the ICMS groups are a choice exported by the tag hooks below, and the
    # aggregator billing (gAgregadora, tpFat 3) and the ICMS of a prepayment
    # are not supported yet
    _nfgas10_stacking_skip_paths = (
        "nfgas10_det_infNFGas_id",
        "nfgas10_gAgregadora",
        "nfgas10_gICMSPrevistoPagtoAntecip",
        "nfgas10_ICMS00",
        "nfgas10_ICMS10",
        "nfgas10_ICMS20",
        "nfgas10_ICMS40",
        "nfgas10_ICMS51",
        "nfgas10_ICMS60",
        "nfgas10_ICMS70",
        "nfgas10_ICMS90",
    )

    nfgas_document_type = fields.Char(
        string="NFGas Document Type Code", related="document_id.document_type"
    )

    nfgas_meter_id = fields.Many2one(
        comodel_name="l10n_br_nfgas.meter",
        string="NFGas Meter",
        domain="[('nfgas10_gMed_infNFGas_id', '=', document_id)]",
        help="Metering equipment of the measured quantity (gMedicao).",
    )

    ##########################
    # NFGas tag: det
    ##########################

    nfgas10_nItem = fields.Char(compute="_compute_nfgas10_nItem")

    def _compute_nfgas10_nItem(self):
        for line in self:
            lines = list(line.document_id.fiscal_line_ids)
            line.nfgas10_nItem = str(lines.index(line) + 1 if line in lines else 1)

    ##########################
    # NFGas tag: prod
    ##########################

    nfgas10_cProd = fields.Char(compute="_compute_nfgas10_prod")
    nfgas10_xProd = fields.Char(related="name")
    nfgas10_cClass = fields.Selection(selection=NFGAS_CCLASS)
    nfgas10_CFOP = fields.Char(string="CFOP Code", related="cfop_id.code")
    nfgas10_uMed = fields.Selection(default="1")
    nfgas10_qFaturada = fields.Float(compute="_compute_nfgas10_prod")
    nfgas10_vItem = fields.Monetary(compute="_compute_nfgas10_prod")
    nfgas10_vProd = fields.Monetary(compute="_compute_nfgas10_prod")

    @api.depends("product_id", "quantity", "price_unit", "price_gross")
    def _compute_nfgas10_prod(self):
        for line in self:
            line.nfgas10_cProd = line.product_id.default_code or str(
                line.product_id.id or ""
            )
            line.nfgas10_qFaturada = line.quantity
            line.nfgas10_vItem = line.price_unit
            # MOC NFGas 1.00g, Anexo I, rule G58: vProd = vItem x qFaturada
            # (the fatorPCS and fatorPTZ factors are not supported yet)
            line.nfgas10_vProd = line.price_gross

    def _export_tag_nfgas_10_gmedicao(self, xsd_fields, class_obj, export_dict):
        if self.nfgas_meter_id:
            export_dict["nMed"] = self.nfgas_meter_id.nfgas10_nMed

    def _export_tag_nfgas_10_gmedida(self, xsd_fields, class_obj, export_dict):
        meter = self.nfgas_meter_id
        export_dict["uMed"] = "1"
        export_dict["vMed"] = meter.nfgas10_vMedAtu - meter.nfgas10_vMedAnt

    ##########################
    # NFGas tag: imposto
    ##########################

    nfgas10_orig = fields.Selection(compute="_compute_nfgas10_orig")

    @api.depends("icms_cst_id", "icms_origin")
    def _compute_nfgas10_orig(self):
        for line in self:
            line.nfgas10_orig = line.icms_origin if line._nfgas_icms_group() else False

    def _nfgas_icms_group(self):
        return NFGAS_ICMS_GROUP_BY_CST.get(self.icms_cst_id.code)

    def _nfgas_export_icms(self, group, export_dict):
        if self._nfgas_icms_group() != group:
            return
        export_dict.update(
            {
                "CST": self.icms_cst_id.code,
                "vBC": self.icms_base,
                "pICMS": self.icms_percent,
                "vICMS": self.icms_value,
                "pRedBC": self.icms_reduction,
            }
        )
        if self.icmsfcp_value:
            export_dict["pFCP"] = self.icmsfcp_percent
            export_dict["vFCP"] = self.icmsfcp_value
        if self.icms_tax_benefit_code:
            export_dict["cBenef"] = self.icms_tax_benefit_code

    def _export_tag_nfgas_10_icms00(self, xsd_fields, class_obj, export_dict):
        self._nfgas_export_icms("ICMS00", export_dict)

    def _export_tag_nfgas_10_icms20(self, xsd_fields, class_obj, export_dict):
        self._nfgas_export_icms("ICMS20", export_dict)

    def _export_tag_nfgas_10_icms40(self, xsd_fields, class_obj, export_dict):
        if self._nfgas_icms_group() == "ICMS40":
            export_dict["CST"] = self.icms_cst_id.code
            if self.icms_tax_benefit_code:
                export_dict["cBenef"] = self.icms_tax_benefit_code

    def _export_tag_nfgas_10_icms90(self, xsd_fields, class_obj, export_dict):
        self._nfgas_export_icms("ICMS90", export_dict)
        if self._nfgas_icms_group() == "ICMS90" and not self.icms_value:
            for key in ("vBC", "pICMS", "vICMS", "pRedBC"):
                export_dict.pop(key, None)

    def _export_tag_nfgas_10_pis(self, xsd_fields, class_obj, export_dict):
        if self.pis_cst_id:
            export_dict.update(
                {
                    "CST": self.pis_cst_id.code,
                    "vBC": self.pis_base,
                    "pPIS": self.pis_percent,
                    "vPIS": self.pis_value,
                }
            )

    def _export_tag_nfgas_10_cofins(self, xsd_fields, class_obj, export_dict):
        if self.cofins_cst_id:
            export_dict.update(
                {
                    "CST": self.cofins_cst_id.code,
                    "vBC": self.cofins_base,
                    "pCOFINS": self.cofins_percent,
                    "vCOFINS": self.cofins_value,
                }
            )

    def _export_tag_nfgas_10_rettrib(self, xsd_fields, class_obj, export_dict):
        if (
            self.pis_wh_value
            or self.cofins_wh_value
            or self.csll_wh_value
            or self.irpj_wh_value
        ):
            export_dict.update(
                {
                    "vRetPIS": self.pis_wh_value,
                    "vRetCofins": self.cofins_wh_value,
                    "vRetCSLL": self.csll_wh_value,
                    "vIRRF": self.irpj_wh_value,
                }
            )

    ##########################
    # NFGas tag: IBSCBS
    ##########################

    def _export_tag_nfgas_10_ibscbs(self, xsd_fields, class_obj, export_dict):
        """IBSCBS group of the item (1-1 in the NFGas, MOC 1.00g, Anexo I)."""
        if not self.ibs_cst_id:
            return
        export_dict["CST"] = self.ibs_cst_id.code
        export_dict["cClassTrib"] = self.tax_classification_id.code
        # the credit reversal (gEstornoCred) is not supported yet
        if "nfgas10_gEstornoCred" in xsd_fields:
            xsd_fields.remove("nfgas10_gEstornoCred")

    def _export_tag_nfgas_10_gibscbs(self, xsd_fields, class_obj, export_dict):
        export_dict["vBC"] = self.ibs_base or self.cbs_base
        export_dict["vIBS"] = self.ibs_value

    def _export_tag_nfgas_10_gibsuf(self, xsd_fields, class_obj, export_dict):
        export_dict["pIBSUF"] = self.ibs_percent
        export_dict["vIBSUF"] = self.ibs_value

    def _export_tag_nfgas_10_gibsuf_gred(self, xsd_fields, class_obj, export_dict):
        if self.ibs_reduction:
            export_dict["pRedAliq"] = self.ibs_reduction
            export_dict["pAliqEfet"] = self.ibs_percent * (1 - self.ibs_reduction / 100)

    def _export_tag_nfgas_10_gibsmun(self, xsd_fields, class_obj, export_dict):
        export_dict["pIBSMun"] = 0.0
        export_dict["vIBSMun"] = 0.0

    def _export_tag_nfgas_10_gcbs(self, xsd_fields, class_obj, export_dict):
        export_dict["pCBS"] = self.cbs_percent
        export_dict["vCBS"] = self.cbs_value

    def _export_tag_nfgas_10_gcbs_gred(self, xsd_fields, class_obj, export_dict):
        if self.cbs_reduction:
            export_dict["pRedAliq"] = self.cbs_reduction
            export_dict["pAliqEfet"] = self.cbs_percent * (1 - self.cbs_reduction / 100)
