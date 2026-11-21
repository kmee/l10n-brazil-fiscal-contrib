# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BpeNoBoardingWizard(models.TransientModel):
    _name = "l10n_br_bpe.no.boarding.wizard"
    _description = "BP-e No Boarding Wizard"
    _inherit = "l10n_br_fiscal.base.wizard.mixin"

    justification = fields.Text(required=True)

    def doit(self):
        for wizard in self:
            wizard.document_id._bpe_no_boarding(wizard.justification)
        return self._close()
