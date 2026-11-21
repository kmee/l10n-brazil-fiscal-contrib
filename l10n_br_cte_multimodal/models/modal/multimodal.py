# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class Multimodal(spec_models.StackedModel):
    _name = "l10n_br_cte.modal.multimodal"
    _inherit = "cte.40.multimodal"
    _description = "Modal Multimodal CTe"

    _cte40_stacking_mixin = "cte.40.multimodal"
    # seg is optional (0-1): stack it so the insurance stays on this record
    _cte40_stacking_force_paths = ("multimodal.seg",)
    _cte40_odoo_module = (
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_multi_modal_v4_00"
    )
    _cte40_binding_module = "nfelib.cte.bindings.v4_0.cte_multi_modal_v4_00"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    cte40_COTM = fields.Char(related="document_id.cte40_COTM")

    cte40_indNegociavel = fields.Selection(related="document_id.cte40_indNegociavel")

    cte40_xSeg = fields.Char(related="document_id.cte40_multimodal_xSeg")

    cte40_CNPJ = fields.Char(compute="_compute_cte40_CNPJ")

    cte40_nApol = fields.Char(related="document_id.cte40_multimodal_nApol")

    cte40_nAver = fields.Char(related="document_id.cte40_multimodal_nAver")

    @api.depends("document_id.cte40_multimodal_CNPJ")
    def _compute_cte40_CNPJ(self):
        for record in self:
            record.cte40_CNPJ = re.sub(
                r"[^A-Z0-9]",
                "",
                (record.document_id.cte40_multimodal_CNPJ or "").upper(),
            )

    def _export_fields_cte_40_multimodal(self, xsd_fields, class_obj, export_dict):
        if "cte40_seg" in xsd_fields and not (
            self.document_id._cte40_multimodal_has_insurance()
        ):
            xsd_fields.remove("cte40_seg")

    def _export_fields_cte_40_infseg(self, xsd_fields, class_obj, export_dict):
        # CNPJ is mandatory in the XSD but may be empty (TCnpjOpc)
        export_dict["CNPJ"] = ""
