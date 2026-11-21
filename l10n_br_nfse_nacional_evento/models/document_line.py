# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.exceptions import UserError


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    def _nfse_event_is_required(self):
        """Rule E0390 (Anexo VI, leiaute 1.04.01 of NT 009): the atvEvento
        group is mandatory for the item 12 and the subitem 17.10."""
        code = self.nfse10_cTribNac or ""
        return code[:2] == "12" or code[:4] == "1710"

    def _export_tag_nfse_10_atvevento(self, xsd_fields, class_obj, export_dict):
        """Build the serv/atvEvento group of the DPS from the fiscal document.

        Called by spec_driven_model while exporting the serv group of the
        line."""
        document = self.document_id
        values = document._nfse_event_values()
        if not values and not self._nfse_event_is_required():
            return
        complete = (
            values
            and values["dtIni"]
            and values["dtFim"]
            and ("idAtvEvt" in values or "end" in values)
        )
        if not complete:
            raise UserError(
                self.env._(
                    "Inform the event of %(document)s: its description, start "
                    "and end dates and its municipal code or venue (rule E0390 "
                    "of the NFS-e Nacional for the service %(code)s).",
                    document=document.display_name,
                    code=self.national_taxation_code_id.code,
                )
            )
        export_dict.update(values)
