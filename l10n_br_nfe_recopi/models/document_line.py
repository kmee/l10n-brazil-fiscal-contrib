# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    nfe40_nRECOPI = fields.Char(
        compute="_compute_nfe40_nRECOPI",
        store=True,
        readonly=False,
    )

    @api.depends("product_id", "document_id.recopi_number")
    def _compute_nfe40_nRECOPI(self):
        for line in self:
            if line.product_id.recopi_paper:
                line.nfe40_nRECOPI = line.document_id.recopi_number
            else:
                line.nfe40_nRECOPI = False
