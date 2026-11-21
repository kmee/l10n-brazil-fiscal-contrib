# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models

GTVE_TPESPECIE = [
    ("1", "Banknote"),
    ("2", "Check"),
    ("3", "Coin"),
    ("4", "Other"),
]


class GTVeSpecies(spec_models.SpecModel):
    _name = "l10n_br_gtve.species"
    _inherit = "cte.40.tgtve_infespecie"
    _description = "Species Transported in the GTV-e"
    _rec_name = "cte40_tpEspecie"

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        required=True,
        ondelete="cascade",
        index=True,
    )

    # missing in l10n_br_cte_spec: the enum lives in another nfelib module
    cte40_tpEspecie = fields.Selection(
        selection=GTVE_TPESPECIE,
        string="Species",
        required=True,
        default="1",
    )

    cte40_vEspecie = fields.Monetary(string="Value", required=True)

    cte40_tpNumerario = fields.Selection(
        string="Nationality", required=True, default="1"
    )

    cte40_xMoedaEstr = fields.Char(string="Foreign Currency")

    def _export_fields_cte_40_tgtve_infespecie(
        self, xsd_fields, class_obj, export_dict
    ):
        export_dict["tpEspecie"] = self.cte40_tpEspecie
        if self.cte40_tpNumerario != "2" and "cte40_xMoedaEstr" in xsd_fields:
            xsd_fields.remove("cte40_xMoedaEstr")

    # dispatch name when the detGTV one2many was mutated to this model
    _export_fields_l10n_br_gtve_species = _export_fields_cte_40_tgtve_infespecie
