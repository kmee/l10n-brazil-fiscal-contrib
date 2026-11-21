# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class NfeAbiSpecMixin(models.AbstractModel):
    _description = "Abstract Model"
    _name = "spec.mixin.nfeabi"
    _nfeabi10_odoo_module = "odoo.addons.l10n_br_nfeabi_spec.models.v1_0.nfe_abi_v1_00"
    # the package exports the classes of every schema file of the layout
    _nfeabi10_binding_module = "odoo.addons.l10n_br_nfeabi_spec.bindings.v1_0"

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
