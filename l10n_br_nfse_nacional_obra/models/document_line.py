# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.exceptions import UserError

# Rule E0370 (Anexo VI, leiaute 1.04.01 of NT 009): the infoObra group is
# mandatory for these national taxation codes
OBRA_TAXATION_CODES = (
    "070201",
    "070202",
    "070401",
    "070501",
    "070502",
    "070601",
    "070602",
    "070701",
    "070801",
    "071701",
    "071901",
    "141403",
    "141404",
)


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    def _export_tag_nfse_10_obra(self, xsd_fields, class_obj, export_dict):
        """Build the serv/obra group of the DPS from the fiscal document.

        Called by spec_driven_model while exporting the serv group of the
        line. An address alone is only reported for the services that require
        the group, so a shipping address does not turn every NFS-e into a
        construction work."""
        document = self.document_id
        required = self.nfse10_cTribNac in OBRA_TAXATION_CODES
        values = document._nfse_obra_values()
        if not required and "end" in values:
            return
        if required and not values:
            raise UserError(
                self.env._(
                    "The service %(code)s of %(document)s is a construction "
                    "work: inform its CNO, CIB or address (rule E0370 of the "
                    "NFS-e Nacional).",
                    code=self.national_taxation_code_id.code,
                    document=document.display_name,
                )
            )
        export_dict.update(values)
