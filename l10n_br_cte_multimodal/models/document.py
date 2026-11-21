# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_cte_spec.models.v4_0.cte_multi_modal_v4_00 import (
    MULTIMODAL_INDNEGOCIAVEL,
)

INSURANCE_FIELDS = (
    "cte40_multimodal_xSeg",
    "cte40_multimodal_CNPJ",
    "cte40_multimodal_nApol",
    "cte40_multimodal_nAver",
)


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    cte_modal_multimodal_id = fields.Many2one(
        comodel_name="l10n_br_cte.modal.multimodal", copy=False
    )

    cte40_COTM = fields.Char(
        string="COTM",
        size=20,
        help="Number of the certificate of the multimodal transport operator.",
    )

    cte40_indNegociavel = fields.Selection(
        selection=MULTIMODAL_INDNEGOCIAVEL,
        string="Negotiable",
    )

    cte40_multimodal_xSeg = fields.Char(string="Insurance Company", size=30)

    cte40_multimodal_CNPJ = fields.Char(
        string="Insurance Company CNPJ",
        help="Required only when the party that hired the transport is "
        "responsible for the insurance and is a company.",
    )

    cte40_multimodal_nApol = fields.Char(string="Insurance Policy", size=20)

    cte40_multimodal_nAver = fields.Char(string="Insurance Endorsement", size=20)

    def _cte40_multimodal_has_insurance(self):
        self.ensure_one()
        return any(self[name] for name in INSURANCE_FIELDS)

    def _export_fields_cte_40_tcte_infmodal(self, xsd_fields, class_obj, export_dict):
        res = super()._export_fields_cte_40_tcte_infmodal(
            xsd_fields, class_obj, export_dict
        )
        if self.cte40_modal == "06":
            export_dict["any_element"] = self._export_cte_modal_multimodal()
        return res

    def _export_cte_modal_multimodal(self):
        self._check_cte40_multimodal()
        if not self.cte_modal_multimodal_id:
            self.cte_modal_multimodal_id = self.cte_modal_multimodal_id.create(
                {"document_id": self.id}
            )
        return self.cte_modal_multimodal_id._build_binding("cte", "40")

    def _check_cte40_multimodal(self):
        """MOC CT-e 4.00 Annex I, layout 3.6 (rule G026, rejection 580)."""
        required = ["cte40_COTM", "cte40_indNegociavel"]
        if self._cte40_multimodal_has_insurance():
            required += [
                "cte40_multimodal_xSeg",
                "cte40_multimodal_nApol",
                "cte40_multimodal_nAver",
            ]
        missing = [self._fields[name].string for name in required if not self[name]]
        if missing:
            raise UserError(
                _(
                    "Multimodal CT-e %(document)s: fill in %(fields)s.",
                    document=self.display_name,
                    fields=", ".join(missing),
                )
            )
