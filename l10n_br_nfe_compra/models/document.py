# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    MODELO_FISCAL_NFE,
)
from odoo.addons.l10n_br_nfe.models.document import filter_processador_edoc_nfe

# ICMS relief reason 8: sale to a public administration body (motDesICMS)
ICMS_RELIEF_PUBLIC_BODY = "8"


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    purchase_commitment_note = fields.Char(
        string="Commitment Note (Empenho)",
        size=22,
        copy=False,
        help="Commitment note (nota de empenho) of a public procurement, "
        "reported in the purchase group (compra/xNEmp) of the NF-e.",
    )

    purchase_order_ref = fields.Char(
        string="Customer Purchase Order",
        size=60,
        compute="_compute_purchase_order_ref",
        store=True,
        readonly=False,
        copy=False,
        help="Purchase order of the customer, reported in the purchase group "
        "(compra/xPed) of the NF-e. By default, the purchase order of the "
        "lines (when all of them have the same one) or the customer reference "
        "of the invoice.",
    )

    purchase_contract_ref = fields.Char(
        string="Purchase Contract",
        size=60,
        copy=False,
        help="Contract of the purchase, reported in the purchase group "
        "(compra/xCont) of the NF-e.",
    )

    @api.depends("fiscal_line_ids.partner_order", "move_ids.ref")
    def _compute_purchase_order_ref(self):
        for record in self:
            if record.document_type != MODELO_FISCAL_NFE:
                record.purchase_order_ref = False
                continue
            line_orders = set(record.fiscal_line_ids.mapped("partner_order"))
            if len(line_orders) == 1 and False not in line_orders:
                record.purchase_order_ref = line_orders.pop()
                continue
            invoices = record.move_ids.filtered(
                lambda move: move.move_type == "out_invoice" and move.ref
            )
            record.purchase_order_ref = invoices[:1].ref or False

    def _nfe40_compra_allowed(self):
        """The purchase group is refused in the NFC-e and in the NF-e with
        the simplified DANFE (rule ZB01-10, rejection 762)."""
        self.ensure_one()
        return self.document_type == MODELO_FISCAL_NFE and self.nfe40_tpImp != "6"

    def _export_tag_nfe_40_compra(self, xsd_fields, class_obj, export_dict):
        """Build the compra group from the document fields (no nfe.40.compra
        record behind the many2one, see spec_driven_model per tag hooks)."""
        if not self._nfe40_compra_allowed():
            return
        for tag, value in (
            ("xNEmp", self.purchase_commitment_note),
            ("xPed", self.purchase_order_ref),
            ("xCont", self.purchase_contract_ref),
        ):
            if value and value.strip():
                export_dict[tag] = value.strip()

    def _document_check(self):
        result = super()._document_check()
        for record in self.filtered(filter_processador_edoc_nfe):
            if record.issuer == DOCUMENT_ISSUER_COMPANY:
                record._check_nfe40_compra()
        return result

    def _check_nfe40_compra(self):
        """Rule ZB02-10 (rejection 359, applied at the discretion of each
        state): an NF-e with ICMS relief for a sale to a public body must
        carry the commitment note."""
        self.ensure_one()
        if not self._nfe40_compra_allowed() or self.purchase_commitment_note:
            return
        if any(
            line.icms_relief_id.code == ICMS_RELIEF_PUBLIC_BODY
            for line in self.fiscal_line_ids
        ):
            raise UserError(
                _(
                    "This NF-e has an ICMS relief for a sale to a public body: "
                    "inform the commitment note (nota de empenho)."
                )
            )
