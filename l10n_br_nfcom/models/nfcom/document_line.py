# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields

from odoo.addons.l10n_br_fiscal.constants.fiscal import TAX_FRAMEWORK_SIMPLES_ALL
from odoo.addons.l10n_br_nfcom_spec.models.v1_0.nfcom_tipos_basico_v1_00 import (
    TUMEDITEM,
)
from odoo.addons.spec_driven_model.models import spec_models

ICMS_TAGS = ("ICMS00", "ICMS20", "ICMS40", "ICMS51", "ICMS90", "ICMSSN")
# ICMS group of the item by CST (MOC NFCom 1.00a, Anexo I, grupo imposto)
ICMS_TAG_BY_CST = {
    "00": "ICMS00",
    "20": "ICMS20",
    "40": "ICMS40",
    "41": "ICMS40",
    "51": "ICMS51",
    "90": "ICMS90",
}


def format_decimal(value):
    """Values of 2 to 8 decimal places (vItem and vProd of the item)."""
    text = f"{value:.8f}".rstrip("0")
    integer, decimals = text.split(".")
    return f"{integer}.{decimals.ljust(2, '0')}"


class NFComLine(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document.line"
    _inherit = ["l10n_br_fiscal.document.line", "nfcom.10.det"]

    _nfcom10_odoo_module = (
        "odoo.addons.l10n_br_nfcom_spec.models.v1_0.nfcom_tipos_basico_v1_00"
    )
    _nfcom10_stacking_mixin = "nfcom.10.det"
    # the ICMS groups share the same tags (CST, vBC...): they are exported
    # by their tag hooks instead of being stacked in the line.
    _nfcom10_stacking_skip_paths = (
        "nfcom10_det_infNFCom_id",
        *(f"nfcom10_{tag}" for tag in ICMS_TAGS),
    )

    DET_TREE = """
+ <det>
    + <prod>
    + <imposto>
        - <ICMS00> <ICMS20> <ICMS40> <ICMS51> <ICMS90> <ICMSSN> tag hooks
        - <PIS> <COFINS> tag hooks
        - <IBSCBS> tag hooks
    - <gProcRef>
    - <gRessarc>"""

    nfcom10_det_infNFCom_id = fields.Many2one(
        related="document_id", string="Fiscal Document"
    )

    nfcom_cclass = fields.Char(
        string="NFCom Item Classification",
        size=7,
        compute="_compute_nfcom_product_data",
        store=True,
        readonly=False,
    )

    nfcom_umed = fields.Selection(
        selection=TUMEDITEM,
        string="NFCom Unit of Measure",
        compute="_compute_nfcom_product_data",
        store=True,
        readonly=False,
    )

    nfcom_amount_item = fields.Monetary(
        string="NFCom Item Amount",
        compute="_compute_nfcom_amount_item",
        help="Unit price x quantity - discount + other expenses (vProd).",
    )

    @api.depends("product_id")
    def _compute_nfcom_product_data(self):
        for line in self:
            line.nfcom_cclass = line.product_id.nfcom_cclass
            line.nfcom_umed = line.product_id.nfcom_umed or "4"

    @api.depends("price_unit", "quantity", "discount_value", "other_value")
    def _compute_nfcom_amount_item(self):
        for line in self:
            line.nfcom_amount_item = (
                line.price_unit * line.quantity - line.discount_value + line.other_value
            )

    ##########################
    # NFCom tag: prod
    ##########################

    nfcom10_cProd = fields.Char(compute="_compute_nfcom10_prod")

    nfcom10_xProd = fields.Char(related="name")

    nfcom10_cClass = fields.Char(related="nfcom_cclass")

    nfcom10_CFOP = fields.Char(related="cfop_id.code")

    nfcom10_uMed = fields.Selection(related="nfcom_umed")

    nfcom10_qFaturada = fields.Float(related="quantity")

    nfcom10_vItem = fields.Char(compute="_compute_nfcom10_prod")

    nfcom10_vDesc = fields.Monetary(related="discount_value")

    nfcom10_vOutro = fields.Monetary(related="other_value")

    nfcom10_vProd = fields.Char(compute="_compute_nfcom10_prod")

    @api.depends("product_id", "price_unit", "nfcom_amount_item")
    def _compute_nfcom10_prod(self):
        for line in self:
            line.nfcom10_cProd = line.product_id.default_code or str(
                line.product_id.id or ""
            )
            line.nfcom10_vItem = format_decimal(line.price_unit)
            line.nfcom10_vProd = format_decimal(line.nfcom_amount_item)

    ##########################
    # NFCom tag: imposto
    ##########################

    def _nfcom_icms_tag(self):
        if self.document_id.company_id.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
            return "ICMSSN"
        return ICMS_TAG_BY_CST.get(self.icms_cst_id.code)

    def _nfcom_export_icms(self, tag, export_dict, values):
        if self._nfcom_icms_tag() == tag:
            export_dict.update(values)

    def _nfcom_icms_fcp(self):
        if not self.icmsfcp_value:
            return {}
        return {"pFCP": self.icmsfcp_percent, "vFCP": self.icmsfcp_value}

    def _nfcom_icms_benefit(self):
        if not self.icms_tax_benefit_code:
            return {}
        return {"cBenef": self.icms_tax_benefit_code}

    def _export_tag_nfcom_10_icms00(self, xsd_fields, class_obj, export_dict):
        self._nfcom_export_icms(
            "ICMS00",
            export_dict,
            {
                "CST": "00",
                "vBC": self.icms_base,
                "pICMS": self.icms_percent,
                "vICMS": self.icms_value,
                **self._nfcom_icms_fcp(),
            },
        )

    def _export_tag_nfcom_10_icms20(self, xsd_fields, class_obj, export_dict):
        self._nfcom_export_icms(
            "ICMS20",
            export_dict,
            {
                "CST": "20",
                "pRedBC": self.icms_reduction,
                "vBC": self.icms_base,
                "pICMS": self.icms_percent,
                "vICMS": self.icms_value,
                **self._nfcom_icms_benefit(),
                **self._nfcom_icms_fcp(),
            },
        )

    def _export_tag_nfcom_10_icms40(self, xsd_fields, class_obj, export_dict):
        self._nfcom_export_icms(
            "ICMS40",
            export_dict,
            {"CST": self.icms_cst_id.code, **self._nfcom_icms_benefit()},
        )

    def _export_tag_nfcom_10_icms51(self, xsd_fields, class_obj, export_dict):
        self._nfcom_export_icms(
            "ICMS51", export_dict, {"CST": "51", **self._nfcom_icms_benefit()}
        )

    def _export_tag_nfcom_10_icms90(self, xsd_fields, class_obj, export_dict):
        self._nfcom_export_icms(
            "ICMS90",
            export_dict,
            {
                "CST": "90",
                "vBC": self.icms_base,
                "pICMS": self.icms_percent,
                "vICMS": self.icms_value,
                **self._nfcom_icms_benefit(),
                **self._nfcom_icms_fcp(),
            },
        )

    def _export_tag_nfcom_10_icmssn(self, xsd_fields, class_obj, export_dict):
        self._nfcom_export_icms("ICMSSN", export_dict, {"CST": "90", "indSN": "1"})

    def _export_tag_nfcom_10_pis(self, xsd_fields, class_obj, export_dict):
        if self.pis_cst_id:
            export_dict.update(
                {
                    "CST": self.pis_cst_id.code,
                    "vBC": self.pis_base,
                    "pPIS": self.pis_percent,
                    "vPIS": self.pis_value,
                }
            )

    def _export_tag_nfcom_10_cofins(self, xsd_fields, class_obj, export_dict):
        if self.cofins_cst_id:
            export_dict.update(
                {
                    "CST": self.cofins_cst_id.code,
                    "vBC": self.cofins_base,
                    "pCOFINS": self.cofins_percent,
                    "vCOFINS": self.cofins_value,
                }
            )

    ##########################
    # NFCom tag: IBSCBS
    # (NT 2025.001 RTC)
    ##########################

    def _export_tag_nfcom_10_ibscbs(self, xsd_fields, class_obj, export_dict):
        if not self.tax_classification_id:
            return
        cst = (self.ibs_cst_id or self.cbs_cst_id).code
        if cst:
            export_dict["CST"] = cst
        export_dict["cClassTrib"] = self.tax_classification_id.code
        if not (self.ibs_base or self.cbs_base) and "nfcom10_gIBSCBS" in xsd_fields:
            xsd_fields.remove("nfcom10_gIBSCBS")

    def _export_tag_nfcom_10_gibscbs(self, xsd_fields, class_obj, export_dict):
        export_dict["vBC"] = self.ibs_base or self.cbs_base
        export_dict["vIBS"] = self.ibs_value

    def _export_tag_nfcom_10_gibsuf(self, xsd_fields, class_obj, export_dict):
        export_dict["pIBSUF"] = self.ibs_percent
        export_dict["vIBSUF"] = self.ibs_value

    def _export_tag_nfcom_10_gibsuf_gred(self, xsd_fields, class_obj, export_dict):
        if self.ibs_reduction:
            export_dict["pRedAliq"] = self.ibs_reduction
            export_dict["pAliqEfet"] = self.ibs_percent * (1 - self.ibs_reduction / 100)

    def _export_tag_nfcom_10_gibsmun(self, xsd_fields, class_obj, export_dict):
        export_dict["pIBSMun"] = 0.0
        export_dict["vIBSMun"] = 0.0

    def _export_tag_nfcom_10_gcbs(self, xsd_fields, class_obj, export_dict):
        export_dict["pCBS"] = self.cbs_percent
        export_dict["vCBS"] = self.cbs_value

    def _export_tag_nfcom_10_gcbs_gred(self, xsd_fields, class_obj, export_dict):
        if self.cbs_reduction:
            export_dict["pRedAliq"] = self.cbs_reduction
            export_dict["pAliqEfet"] = self.cbs_percent * (1 - self.cbs_reduction / 100)
