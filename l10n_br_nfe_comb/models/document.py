# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_ISSUER_COMPANY
from odoo.addons.l10n_br_nfe.models.document import filter_processador_edoc_nfe


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _document_check(self):
        result = super()._document_check()
        for record in self.filtered(filter_processador_edoc_nfe):
            if record.issuer == DOCUMENT_ISSUER_COMPANY:
                record._check_nfe40_comb()
        return result

    def _check_nfe40_comb(self):
        """Refuse to issue an NF-e the SEFAZ would reject because of the
        fuel group of its items."""
        self.ensure_one()
        errors = []
        for line in self.fiscal_line_ids.filtered("nfe40_comb"):
            errors += line._nfe40_comb_errors()
        if errors:
            raise UserError(
                _(
                    "The NF-e fuel data (comb) is incomplete or inconsistent:"
                    "\n%(errors)s",
                    errors="\n".join(errors),
                )
            )
