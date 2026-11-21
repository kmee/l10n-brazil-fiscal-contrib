# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from nfelib.cte.bindings.v4_0.cte_tipos_basico_v4_00 import Tgtve

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models

GTVE_VERSION = "4.00"

STACKED_SPEC_CLASSES = {
    "cte40_ide": "cte.40.tgtve_ide",
    "cte40_detGTV": "cte.40.detgtv",
}


class GTVe(spec_models.StackedModel):
    """infCte of a GTV-e, built from its l10n_br_fiscal.document.

    The GTV-e uses the cte40_ names of the CT-e (57) with other contents,
    so it cannot be stacked in l10n_br_fiscal.document next to the CT-e.
    """

    _name = "l10n_br_gtve.gtve"
    _inherit = "cte.40.tgtve_infcte"
    _description = "GTV-e"
    _rec_name = "document_id"

    _cte40_stacking_mixin = "cte.40.tgtve_infcte"
    # mapped to the company and partners below
    _cte40_stacking_skip_paths = (
        "cte40_emit",
        "cte40_rem",
        "cte40_dest",
        "cte40_toma",
        "cte40_tomaTerceiro",
    )
    _cte40_odoo_module = (
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00"
    )
    _cte40_binding_module = "nfelib.cte.bindings.v4_0.cte_tipos_basico_v4_00"

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        required=True,
        ondelete="cascade",
        index=True,
    )

    cte40_versao = fields.Char(default=GTVE_VERSION)

    cte40_Id = fields.Char(compute="_compute_cte40_key_fields")

    # ide
    cte40_cUF = fields.Char(
        related="document_id.company_id.partner_id.state_id.ibge_code"
    )

    cte40_cCT = fields.Char(compute="_compute_cte40_key_fields")

    cte40_cDV = fields.Char(compute="_compute_cte40_key_fields")

    cte40_CFOP = fields.Char(related="document_id.gtve_cfop_id.code")

    cte40_natOp = fields.Char(compute="_compute_cte40_natOp")

    cte40_mod = fields.Char(related="document_id.document_type_id.code")

    cte40_serie = fields.Char(related="document_id.document_serie")

    cte40_nCT = fields.Char(related="document_id.document_number")

    cte40_dhEmi = fields.Datetime(related="document_id.document_date")

    cte40_tpImp = fields.Selection(default="1")

    cte40_tpEmis = fields.Selection(default="1")

    cte40_tpAmb = fields.Selection(related="document_id.cte_environment")

    cte40_tpCTe = fields.Selection(default="4")

    cte40_verProc = fields.Char(
        default=lambda self: self.env["ir.config_parameter"]
        .sudo()
        .get_param("l10n_br_cte.version.name", default="Odoo Brasil OCA")
    )

    cte40_cMunEnv = fields.Char(
        related="document_id.company_id.partner_id.city_id.ibge_code"
    )

    cte40_xMunEnv = fields.Char(
        related="document_id.company_id.partner_id.city_id.name"
    )

    cte40_UFEnv = fields.Char(related="document_id.company_id.partner_id.state_id.code")

    cte40_modal = fields.Selection(related="document_id.transport_modal")

    cte40_tpServ = fields.Selection(default="9")

    cte40_indIEToma = fields.Selection(related="document_id.cte40_indIEToma")

    cte40_dhSaidaOrig = fields.Datetime(related="document_id.gtve_departure_date")

    cte40_dhChegadaDest = fields.Datetime(related="document_id.gtve_arrival_date")

    # emit, rem, dest
    cte40_emit = fields.Many2one(
        comodel_name="res.company", related="document_id.company_id"
    )

    cte40_rem = fields.Many2one(
        comodel_name="res.partner", related="document_id.partner_sendering_id"
    )

    cte40_dest = fields.Many2one(
        comodel_name="res.partner", related="document_id.partner_shipping_id"
    )

    cte40_autXML = fields.One2many(
        comodel_name="l10n_br_cte.autxml", related="document_id.cte40_autXML"
    )

    # detGTV
    cte40_qCarga = fields.Float(related="document_id.gtve_load_quantity")

    cte40_infEspecie = fields.One2many(
        comodel_name="l10n_br_gtve.species",
        related="document_id.gtve_species_ids",
    )

    cte40_infVeiculo = fields.One2many(
        comodel_name="l10n_br_gtve.vehicle",
        related="document_id.gtve_vehicle_ids",
    )

    @classmethod
    def _build_model(cls, pool, cr):
        """Keep StackedModel ahead of the stacked spec mixins in the bases.

        StackedModel puts the stacked spec mixins (TgtveInfCte...) before
        itself in the bases. When the CT-e spec hook already made
        cte.40.tgtve_infcte concrete in this registry (on 16.0 _build_binding
        runs it, e.g. in the at_install tests of another CT-e module), that
        class has SpecModel before TgtveInfCte and the MRO of this model
        cannot be built. SpecModel and StackedModel first works both ways.
        """
        model = super()._build_model(pool, cr)
        if cls.__bases__[0] is not spec_models.StackedModel:
            cls.__bases__ = (spec_models.StackedModel,) + tuple(
                base for base in cls.__bases__ if base is not spec_models.StackedModel
            )
        return model

    @api.depends("document_id.document_key")
    def _compute_cte40_key_fields(self):
        for record in self:
            key = record.document_id.document_key
            record.cte40_Id = key and f"CTe{key}"
            record.cte40_cCT = key and key[35:43]
            record.cte40_cDV = key and key[43:]

    @api.depends("document_id.operation_name", "document_id.fiscal_operation_id")
    def _compute_cte40_natOp(self):
        for record in self:
            document = record.document_id
            record.cte40_natOp = (
                document.operation_name or document.fiscal_operation_id.name
            )

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        # l10n_br_cte makes these spec mixins concrete before this module is
        # installed, and the comodel of the stacking points then points here
        if field_name in STACKED_SPEC_CLASSES:
            return self._build_binding(class_name=STACKED_SPEC_CLASSES[field_name])
        return super()._export_many2one(field_name, xsd_required, class_obj)

    def _export_fields_cte_40_tgtve_ide(self, xsd_fields, class_obj, export_dict):
        for name in ("cte40_toma", "cte40_tomaTerceiro"):
            if name in xsd_fields:
                xsd_fields.remove(name)
        taker = self.document_id.gtve_service_taker
        if taker == "4":
            third_party = self.document_id.partner_id._build_binding(
                class_name="cte.40.tomaterceiro"
            )
            third_party.toma = taker
            export_dict["tomaTerceiro"] = third_party
        else:
            export_dict["toma"] = Tgtve.InfCte.Ide.Toma(toma=taker)
