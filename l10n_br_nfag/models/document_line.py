# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models

from ..constants.nfag import NFAG_COFINS_CST, NFAG_PIS_CST


class NFAgLine(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document.line"
    _inherit = ["l10n_br_fiscal.document.line", "nfag.10.det"]

    _nfag10_odoo_module = (
        "odoo.addons.l10n_br_nfag_spec.models.v1_0.nfag_tipos_basico_v1_00"
    )
    _nfag10_stacking_mixin = "nfag.10.det"
    # the IBSCBS group is exported by the tag hooks below; the tariffs
    # (gTarif), the judicial process (gProcRef) and the aggregating NFAg
    # (gAgregadora) are not supported yet
    _nfag10_stacking_skip_paths = (
        "nfag10_det_infNFAg_id",
        "nfag10_gTarif",
        "nfag10_gProcRef",
        "nfag10_gAgregadora",
        "nfag10_IBSCBS",
    )

    nfag_document_type = fields.Char(
        string="NFAg Document Type Code", related="document_id.document_type"
    )

    nfag10_det_infNFAg_id = fields.Many2one(related="document_id")

    ##########################
    # NFAg tag: det
    ##########################

    nfag10_nItem = fields.Char(compute="_compute_nfag10_nItem")

    def _compute_nfag10_nItem(self):
        for line in self:
            lines = list(line.document_id.fiscal_line_ids)
            line.nfag10_nItem = str(lines.index(line) + 1 if line in lines else 1)

    def _nfag_sign(self):
        """Items whose cClass starts with 5 are deducted from the total (MOC
        NFAg 1.00l, Visão Geral, classificação de produtos)."""
        self.ensure_one()
        return -1 if (self.nfag10_cClass or "").startswith("5") else 1

    def _export_fields_nfag_10_det(self, xsd_fields, class_obj, export_dict):
        # the aggregating NFAg item (gAgregadora) is the other branch of the
        # det choice; it is not supported yet
        for field_name in ("nfag10_gAgregadora", "nfag10_gProcRef"):
            if field_name in xsd_fields:
                xsd_fields.remove(field_name)

    ##########################
    # NFAg tag: prod
    ##########################

    nfag10_cProd = fields.Char(related="product_id.default_code")
    nfag10_xProd = fields.Char(related="name")
    nfag10_qFaturada = fields.Float(compute="_compute_nfag10_prod")
    nfag10_vItem = fields.Monetary(compute="_compute_nfag10_prod")
    nfag10_vProd = fields.Monetary(compute="_compute_nfag10_prod")

    @api.depends("quantity", "price_unit", "price_gross")
    def _compute_nfag10_prod(self):
        for line in self:
            line.nfag10_qFaturada = line.quantity
            line.nfag10_vItem = line.price_unit
            # MOC NFAg 1.00l, Anexo I, rule G70: vProd = vItem x qFaturada
            line.nfag10_vProd = line.price_gross

    def _export_fields_nfag_10_prod(self, xsd_fields, class_obj, export_dict):
        # not supported yet: the pollution factor (it changes vProd, rule G70),
        # the net values of NT 2026.004 and the return indicator (it needs the
        # key of the former NFAg, rule G47)
        for field_name in (
            "nfag10_fatorPoluicao",
            "nfag10_vItemLiq",
            "nfag10_vProdLiq",
            "nfag10_indDevolucao",
        ):
            if field_name in xsd_fields:
                xsd_fields.remove(field_name)

    ##########################
    # NFAg tag: imposto
    ##########################

    def _export_tag_nfag_10_pis(self, xsd_fields, class_obj, export_dict):
        if self.pis_cst_id.code in NFAG_PIS_CST:
            export_dict.update(
                {
                    "CST": self.pis_cst_id.code,
                    "vBC": self.pis_base,
                    "pPIS": self.pis_percent,
                    "vPIS": self.pis_value,
                }
            )

    def _export_tag_nfag_10_cofins(self, xsd_fields, class_obj, export_dict):
        if self.cofins_cst_id.code in NFAG_COFINS_CST:
            export_dict.update(
                {
                    "CST": self.cofins_cst_id.code,
                    "vBC": self.cofins_base,
                    "pCOFINS": self.cofins_percent,
                    "vCOFINS": self.cofins_value,
                }
            )

    def _export_tag_nfag_10_rettrib(self, xsd_fields, class_obj, export_dict):
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
    # NFAg tag: IBSCBS
    ##########################

    def _export_tag_nfag_10_ibscbs(self, xsd_fields, class_obj, export_dict):
        """IBSCBS group of the item, required in the NFAg (MOC 1.00l)."""
        if not self.ibs_cst_id:
            return
        export_dict["CST"] = self.ibs_cst_id.code
        export_dict["cClassTrib"] = self.tax_classification_id.code
        # the credit reversal (gEstornoCred) is not supported yet
        if "nfag10_gEstornoCred" in xsd_fields:
            xsd_fields.remove("nfag10_gEstornoCred")

    def _export_tag_nfag_10_gibscbs(self, xsd_fields, class_obj, export_dict):
        export_dict["vBC"] = self.ibs_base or self.cbs_base
        # vIBS = vIBSUF + vIBSMun (rule G102), with the municipal IBS at zero
        export_dict["vIBS"] = self.ibs_value

    def _export_tag_nfag_10_gibsuf(self, xsd_fields, class_obj, export_dict):
        export_dict["pIBSUF"] = self.ibs_percent
        export_dict["vIBSUF"] = self.ibs_value

    def _export_tag_nfag_10_gibsuf_gred(self, xsd_fields, class_obj, export_dict):
        if self.ibs_reduction:
            export_dict["pRedAliq"] = self.ibs_reduction
            export_dict["pAliqEfet"] = self.ibs_percent * (1 - self.ibs_reduction / 100)

    def _export_tag_nfag_10_gibsmun(self, xsd_fields, class_obj, export_dict):
        export_dict["pIBSMun"] = 0.0
        export_dict["vIBSMun"] = 0.0

    def _export_tag_nfag_10_gcbs(self, xsd_fields, class_obj, export_dict):
        export_dict["pCBS"] = self.cbs_percent
        export_dict["vCBS"] = self.cbs_value

    def _export_tag_nfag_10_gcbs_gred(self, xsd_fields, class_obj, export_dict):
        if self.cbs_reduction:
            export_dict["pRedAliq"] = self.cbs_reduction
            export_dict["pAliqEfet"] = self.cbs_percent * (1 - self.cbs_reduction / 100)
