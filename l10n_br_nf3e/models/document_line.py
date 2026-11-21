# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models

from ..constants.nf3e import NF3E_ICMS_GROUP_BY_CST


class NF3eLine(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document.line"
    _inherit = ["l10n_br_fiscal.document.line", "nf3e.10.det"]

    _nf3e10_odoo_module = (
        "odoo.addons.l10n_br_nf3e_spec.models.v1_0.nf3e_tipos_basico_v1_00"
    )
    _nf3e10_stacking_mixin = "nf3e.10.det"
    # the ICMS groups are a choice exported by the tag hooks below, and the
    # items of a former NF3e (detItemAnt) are not supported yet
    _nf3e10_stacking_skip_paths = (
        "nf3e10_det_NFdet_id",
        "nf3e10_detItemAnt",
        "nf3e10_ICMS00",
        "nf3e10_ICMS10",
        "nf3e10_ICMS20",
        "nf3e10_ICMS40",
        "nf3e10_ICMS51",
        "nf3e10_ICMS60",
        "nf3e10_ICMS90",
    )

    nf3e_document_type = fields.Char(related="document_id.document_type")

    ##########################
    # NF3e tag: det
    ##########################

    nf3e10_nItem = fields.Char(compute="_compute_nf3e10_nItem")

    def _compute_nf3e10_nItem(self):
        for line in self:
            lines = list(line.document_id.fiscal_line_ids)
            line.nf3e10_nItem = str(lines.index(line) + 1 if line in lines else 1)

    ##########################
    # NF3e tag: prod
    ##########################

    nf3e10_cProd = fields.Char(related="product_id.default_code")
    nf3e10_xProd = fields.Char(related="name")
    nf3e10_CFOP = fields.Char(string="CFOP Code", related="cfop_id.code")
    nf3e10_qFaturada = fields.Float(compute="_compute_nf3e10_prod")
    nf3e10_vItem = fields.Monetary(compute="_compute_nf3e10_prod")
    nf3e10_vProd = fields.Monetary(compute="_compute_nf3e10_prod")

    @api.depends("quantity", "price_unit", "price_gross")
    def _compute_nf3e10_prod(self):
        for line in self:
            line.nf3e10_qFaturada = line.quantity
            line.nf3e10_vItem = line.price_unit
            # MOC NF3e 1.00a, rule G110: vProd = vItem x qFaturada
            line.nf3e10_vProd = line.price_gross

    ##########################
    # NF3e tag: imposto
    ##########################

    def _nf3e_icms_group(self):
        return NF3E_ICMS_GROUP_BY_CST.get(self.icms_cst_id.code)

    def _nf3e_export_icms(self, group, export_dict):
        if self._nf3e_icms_group() != group:
            return
        export_dict.update(
            {
                "CST": self.icms_cst_id.code,
                "vBC": self.icms_base,
                "pICMS": self.icms_percent,
                "vICMS": self.icms_value,
                "pRedBC": self.icms_reduction,
                "vBCST": self.icmsst_base,
                "pICMSST": self.icmsst_percent,
                "vICMSST": self.icmsst_value,
                "vBCSTRet": self.icmsst_wh_base,
                "pICMSSTRet": self.icmsst_wh_percent,
                "vICMSSTRet": self.icmsst_wh_value,
            }
        )
        if self.icmsfcp_value:
            export_dict["pFCP"] = self.icmsfcp_percent
            export_dict["vFCP"] = self.icmsfcp_value
        if self.icmsfcpst_value:
            export_dict["pFCPST"] = self.icmsfcpst_percent
            export_dict["vFCPST"] = self.icmsfcpst_value
        if self.icms_tax_benefit_code:
            export_dict["cBenef"] = self.icms_tax_benefit_code

    def _export_tag_nf3e_10_icms00(self, xsd_fields, class_obj, export_dict):
        self._nf3e_export_icms("ICMS00", export_dict)

    def _export_tag_nf3e_10_icms10(self, xsd_fields, class_obj, export_dict):
        self._nf3e_export_icms("ICMS10", export_dict)

    def _export_tag_nf3e_10_icms20(self, xsd_fields, class_obj, export_dict):
        self._nf3e_export_icms("ICMS20", export_dict)

    def _export_tag_nf3e_10_icms40(self, xsd_fields, class_obj, export_dict):
        self._nf3e_export_icms("ICMS40", export_dict)

    def _export_tag_nf3e_10_icms51(self, xsd_fields, class_obj, export_dict):
        self._nf3e_export_icms("ICMS51", export_dict)

    def _export_tag_nf3e_10_icms60(self, xsd_fields, class_obj, export_dict):
        self._nf3e_export_icms("ICMS60", export_dict)

    def _export_tag_nf3e_10_icms90(self, xsd_fields, class_obj, export_dict):
        self._nf3e_export_icms("ICMS90", export_dict)

    def _export_tag_nf3e_10_pis(self, xsd_fields, class_obj, export_dict):
        if self.pis_cst_id:
            export_dict.update(
                {
                    "CST": self.pis_cst_id.code,
                    "vBC": self.pis_base,
                    "pPIS": self.pis_percent,
                    "vPIS": self.pis_value,
                }
            )

    def _export_tag_nf3e_10_cofins(self, xsd_fields, class_obj, export_dict):
        if self.cofins_cst_id:
            export_dict.update(
                {
                    "CST": self.cofins_cst_id.code,
                    "vBC": self.cofins_base,
                    "pCOFINS": self.cofins_percent,
                    "vCOFINS": self.cofins_value,
                }
            )

    def _export_tag_nf3e_10_rettrib(self, xsd_fields, class_obj, export_dict):
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
                    "vBCIRRF": self.irpj_wh_base,
                    "vIRRF": self.irpj_wh_value,
                }
            )

    ##########################
    # NF3e tag: IBSCBS
    ##########################

    def _export_tag_nf3e_10_ibscbs(self, xsd_fields, class_obj, export_dict):
        """IBSCBS group of the item (NT 2025.001 RTC v1.14a)."""
        if not self.ibs_cst_id:
            return
        export_dict["CST"] = self.ibs_cst_id.code
        export_dict["cClassTrib"] = self.tax_classification_id.code
        # the credit reversal choice (gEstornoCred) is not supported yet
        if "nf3e10_gEstornoCred" in xsd_fields:
            xsd_fields.remove("nf3e10_gEstornoCred")

    def _export_tag_nf3e_10_gibscbs(self, xsd_fields, class_obj, export_dict):
        export_dict["vBC"] = self.ibs_base or self.cbs_base
        export_dict["vIBS"] = self.ibs_value

    def _export_tag_nf3e_10_gibsuf(self, xsd_fields, class_obj, export_dict):
        export_dict["pIBSUF"] = self.ibs_percent
        export_dict["vIBSUF"] = self.ibs_value

    def _export_tag_nf3e_10_gibsuf_gred(self, xsd_fields, class_obj, export_dict):
        if self.ibs_reduction:
            export_dict["pRedAliq"] = self.ibs_reduction
            export_dict["pAliqEfet"] = self.ibs_percent * (1 - self.ibs_reduction / 100)

    def _export_tag_nf3e_10_gibsmun(self, xsd_fields, class_obj, export_dict):
        export_dict["pIBSMun"] = 0.0
        export_dict["vIBSMun"] = 0.0

    def _export_tag_nf3e_10_gcbs(self, xsd_fields, class_obj, export_dict):
        export_dict["pCBS"] = self.cbs_percent
        export_dict["vCBS"] = self.cbs_value

    def _export_tag_nf3e_10_gcbs_gred(self, xsd_fields, class_obj, export_dict):
        if self.cbs_reduction:
            export_dict["pRedAliq"] = self.cbs_reduction
            export_dict["pAliqEfet"] = self.cbs_percent * (1 - self.cbs_reduction / 100)
