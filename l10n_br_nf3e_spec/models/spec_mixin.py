# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Nf3eSpecMixin(models.AbstractModel):
    _description = "Abstract Model"
    _name = "spec.mixin.nf3e"
    _nf3e10_odoo_module = (
        "odoo.addons.l10n_br_nf3e_spec.models.v1_0.nf3e_tipos_basico_v1_00"
    )
    _nf3e10_binding_module = "nfelib.nf3e.bindings.v1_0.nf3e_tipos_basico_v1_00"

    brl_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Moeda",
        compute="_compute_brl_currency_id",
        default=lambda self: self.env.ref("base.BRL"),
    )

    def _compute_brl_currency_id(self):
        self.brl_currency_id = self.env.ref("base.BRL")

    def _valid_field_parameter(self, field, name):
        if name in (
            "xsd_type",
            "xsd_required",
            "choice",
            "xsd_implicit",
            "xsd_choice_required",
        ):
            return True
        return super()._valid_field_parameter(field, name)
