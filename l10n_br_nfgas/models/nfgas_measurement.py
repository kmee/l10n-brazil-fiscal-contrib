# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class NFGasMeter(spec_models.SpecModel):
    _name = "l10n_br_nfgas.meter"
    _inherit = "nfgas.10.gmed"
    _description = "NFGas Metering Equipment (gMed)"
    _order = "id"

    nfgas10_nMed = fields.Char(compute="_compute_nfgas10_nMed")

    nfgas10_idEqp = fields.Char(required=True)

    nfgas10_tpEqp = fields.Selection(required=True, default="1")

    def _compute_nfgas10_nMed(self):
        for meter in self:
            meters = list(meter.nfgas10_gMed_infNFGas_id.nfgas10_gMed)
            position = meters.index(meter) + 1 if meter in meters else 1
            meter.nfgas10_nMed = str(position).zfill(2)


class NFGasConsumptionHistory(spec_models.SpecModel):
    _name = "l10n_br_nfgas.consumption.history"
    _inherit = "nfgas.10.ghistcons"
    _description = "NFGas Consumption History (gHistCons)"

    nfgas10_xHistorico = fields.Char(required=True)

    nfgas10_gCons = fields.One2many(
        comodel_name="l10n_br_nfgas.consumption.history.line",
    )


class NFGasConsumptionHistoryLine(spec_models.SpecModel):
    _name = "l10n_br_nfgas.consumption.history.line"
    _inherit = "nfgas.10.gcons"
    _description = "NFGas Consumption of a Month (gCons)"

    nfgas10_CompetFat = fields.Char(required=True)

    nfgas10_uMed = fields.Selection(default="1")
