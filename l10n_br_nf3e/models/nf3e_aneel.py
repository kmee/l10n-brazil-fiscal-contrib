# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class NF3eBillingHistory(spec_models.SpecModel):
    _name = "l10n_br_nf3e.billing.history"
    _inherit = "nf3e.10.ghistfat"
    _description = "NF3e Billing History (gHistFat)"

    nf3e10_xGrandFat = fields.Char(required=True)

    nf3e10_gGrandFat = fields.One2many(
        comodel_name="l10n_br_nf3e.billing.history.line",
    )


class NF3eBillingHistoryLine(spec_models.SpecModel):
    _name = "l10n_br_nf3e.billing.history.line"
    _inherit = "nf3e.10.ggrandfat"
    _description = "NF3e Billed Quantity of a Month (gGrandFat)"

    nf3e10_CompetFat = fields.Char(required=True)


class NF3eMeter(spec_models.SpecModel):
    _name = "l10n_br_nf3e.meter"
    _inherit = "nf3e.10.gmed"
    _description = "NF3e Meter (gMed)"

    nf3e10_nMed = fields.Char(required=True)

    nf3e10_idMedidor = fields.Char(required=True)
