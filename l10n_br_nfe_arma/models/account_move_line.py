# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _fill_nfe40_arma(self):
        """(Re)build the NF-e firearm groups from the serial numbers of the
        stock moves the invoice lines were created from."""
        for line in self.filtered("fiscal_document_line_id"):
            lots = line.move_line_ids.move_line_ids.lot_id
            line.fiscal_document_line_id._nfe40_fill_arma(lots)
