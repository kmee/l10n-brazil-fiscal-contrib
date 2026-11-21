# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    nfse_bc_adjustment_ids = fields.One2many(
        comodel_name="l10n_br_nfse_nacional.bc.adjustment",
        inverse_name="document_id",
        string="Tax Base Adjustment Documents",
        copy=True,
    )
