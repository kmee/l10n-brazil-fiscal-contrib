# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from nfelib.nfse.bindings.v1_0.tipos_complexos_v1_01 import TclistaDocAjusteBc

from odoo import models
from odoo.exceptions import UserError

from .bc_adjustment import ISSQN_ADJUSTMENT_TYPES


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    def _export_tag_nfse_10_vajustebc(self, xsd_fields, class_obj, export_dict):
        """Build the valores/vAjusteBC group of the DPS: the ISSQN deduction
        of the line and the documents that support the adjustments.

        Called by spec_driven_model while exporting the valores group of
        the line."""
        adjustments = self.document_id.nfse_bc_adjustment_ids
        if not adjustments and not self.issqn_deduction_amount:
            return
        errors = self._nfse_bc_adjustment_errors(adjustments)
        if errors:
            raise UserError("\n".join(errors))
        if self.issqn_deduction_amount:
            export_dict["vAjusteBCISSQN"] = f"{self.issqn_deduction_amount:.2f}"
        if adjustments:
            export_dict["documentos"] = TclistaDocAjusteBc(
                docAjusteBC=[adjustment._nfse_binding() for adjustment in adjustments]
            )

    def _nfse_bc_adjustment_errors(self, adjustments):
        """Rules of the vAjusteBC group (Anexo VI, leiaute 1.04.01 of NT 009)
        that depend on the service of the line."""
        errors = []
        types = set(adjustments.mapped("adjustment_type"))
        issqn_types = types & set(ISSQN_ADJUSTMENT_TYPES)
        if self.nfse10_tribISSQN != "1" and (
            issqn_types or self.issqn_deduction_amount
        ):
            errors.append(
                self.env._(
                    "E0435: a service that is not taxed by the ISSQN only takes "
                    "the refund adjustments (types 101 to 199)."
                )
            )
        if self.issqn_deduction_amount and issqn_types:
            errors.append(
                self.env._(
                    "E0462: the ISSQN deduction of the line excludes the "
                    "adjustment documents of types 2 to 99."
                )
            )
        if (self.nfse10_cTribNac or "")[:4] in ("0601", "0602") and types - {
            "9",
            "199",
        }:
            errors.append(
                self.env._(
                    "E0463: the services 06.01 and 06.02 only take the "
                    "adjustment types 9 and 199."
                )
            )
        if any(a.applied_amount > self.price_gross for a in adjustments):
            errors.append(
                self.env._("E0467: an applied adjustment exceeds the service amount.")
            )
        return errors
