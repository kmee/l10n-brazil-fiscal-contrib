# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    nfe40_obsItem = fields.Many2one(
        compute="_compute_nfe40_obsItem",
        store=True,
        readonly=False,
    )

    @api.depends("product_id")
    def _compute_nfe40_obsItem(self):
        for line in self:
            line.nfe40_obsItem = line.product_id.nfe40_obsItem
