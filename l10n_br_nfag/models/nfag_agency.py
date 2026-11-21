# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class NFAgMeter(spec_models.SpecModel):
    _name = "l10n_br_nfag.meter"
    _inherit = "nfag.10.gmed"
    _description = "NFAg Water Meter (gMed)"

    nfag10_nMed = fields.Char(required=True)

    nfag10_idMedidor = fields.Char(required=True)


class NFAgConsumptionHistory(spec_models.SpecModel):
    _name = "l10n_br_nfag.consumption.history"
    _inherit = "nfag.10.ghistcons"
    _description = "NFAg Consumption History (gHistCons)"

    nfag10_xHistorico = fields.Char(required=True)

    nfag10_gCons = fields.One2many(
        comodel_name="l10n_br_nfag.consumption.history.line",
    )


class NFAgConsumptionHistoryLine(spec_models.SpecModel):
    _name = "l10n_br_nfag.consumption.history.line"
    _inherit = "nfag.10.gcons"
    _description = "NFAg Consumption of a Month (gCons)"

    nfag10_CompetFat = fields.Char(required=True)
