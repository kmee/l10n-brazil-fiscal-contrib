# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_ISSUER_COMPANY
from odoo.addons.l10n_br_nfe.models.document import filter_processador_edoc_nfe

from .product_template import CRED_PRESUMIDO_CODE_PATTERN

# leiauteNFe_v4.00.xsd: <gCred minOccurs="0" maxOccurs="4">
GCRED_MAX_OCCURS = 4


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _document_check(self):
        result = super()._document_check()
        for record in self.filtered(filter_processador_edoc_nfe):
            if record.issuer == DOCUMENT_ISSUER_COMPANY:
                record._check_nfe40_gCred()
        return result

    def _check_nfe40_gCred(self):
        """Refuse to issue an NF-e whose presumed credit groups the schema
        would reject: more than 4 groups per item, a code that is not 8 or
        10 characters long or a percentage out of the 0 to 999 range."""
        self.ensure_one()
        errors = []
        for line in self.fiscal_line_ids:
            item = line.product_id.display_name or line.name
            if len(line.nfe40_gCred) > GCRED_MAX_OCCURS:
                errors.append(
                    _(
                        "%(item)s: the NF-e accepts at most %(max)s presumed "
                        "credits per item.",
                        item=item,
                        max=GCRED_MAX_OCCURS,
                    )
                )
            for credit in line.nfe40_gCred:
                code = credit.nfe40_cCredPresumido or ""
                if not CRED_PRESUMIDO_CODE_PATTERN.fullmatch(code):
                    errors.append(
                        _(
                            "%(item)s: the presumed credit code %(code)r must "
                            "have 8 or 10 characters, without spaces.",
                            item=item,
                            code=code,
                        )
                    )
                if not 0 <= credit.nfe40_pCredPresumido < 1000:
                    errors.append(
                        _(
                            "%(item)s: the presumed credit percentage must be "
                            "between 0 and 999.",
                            item=item,
                        )
                    )
        if errors:
            raise UserError(
                _(
                    "The NF-e presumed credit data (gCred) is invalid:\n%(errors)s",
                    errors="\n".join(errors),
                )
            )
