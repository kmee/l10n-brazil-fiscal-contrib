# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    MODELO_FISCAL_NFE,
)
from odoo.addons.l10n_br_nfe.models.document import filter_processador_edoc_nfe

ADDRESS_FIELDS = ("street_name", "street_number", "street2", "district", "city_id")


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    nfe40_retirada = fields.Many2one(
        string="Pickup Address",
        compute="_compute_nfe40_retirada",
        store=True,
        readonly=False,
        help="Address the goods leave from, reported in the pickup group "
        "(retirada) of the NF-e only when it differs from the issuer address. "
        "By default, the address of the warehouse of the deliveries invoiced.",
    )

    @api.depends(
        "move_ids.picking_ids.location_id.warehouse_id.partner_id",
        "company_id.partner_id",
    )
    def _compute_nfe40_retirada(self):
        for record in self:
            pickings = self.env["stock.picking"]
            if (
                record.document_type == MODELO_FISCAL_NFE
                and record.fiscal_operation_type == "out"
            ):
                pickings = record.move_ids.picking_ids.filtered(
                    lambda picking: picking.picking_type_code == "outgoing"
                )
            record.nfe40_retirada = record._nfe40_retirada_from_pickings(pickings)

    def _nfe40_retirada_from_pickings(self, pickings):
        """The single warehouse address of the pickings, when it is not the
        issuer address (leiauteNFe_v4.00.xsd, retirada)."""
        self.ensure_one()
        partner = pickings.location_id.warehouse_id.partner_id
        if len(partner) != 1 or self._nfe40_is_issuer_address(partner):
            return self.env["res.partner"]
        return partner

    def _nfe40_is_issuer_address(self, partner):
        issuer = self.company_id.partner_id
        return partner == issuer or all(
            partner[name] == issuer[name] for name in ADDRESS_FIELDS
        )

    def _document_check(self):
        result = super()._document_check()
        for record in self.filtered(filter_processador_edoc_nfe):
            if record.issuer == DOCUMENT_ISSUER_COMPANY and record.nfe40_retirada:
                record._check_nfe40_retirada()
        return result

    def _check_nfe40_retirada(self):
        """Refuse the pickup group in the NFC-e and in the NF-e with the
        simplified DANFE (rule F01-10, rejection 669) and a pickup address
        without the data required by the layout."""
        self.ensure_one()
        partner = self.nfe40_retirada
        if self.document_type != MODELO_FISCAL_NFE or self.nfe40_tpImp == "6":
            raise UserError(
                _(
                    "The pickup address is not accepted in the NFC-e nor in the "
                    "NF-e with the simplified DANFE."
                )
            )
        missing = [
            label
            for label, value in (
                (_("CNPJ or CPF"), partner.vat),
                (_("street"), partner.street_name),
                (_("number"), partner.street_number),
                (_("district"), partner.district),
                (_("city"), partner.city_id),
            )
            if not value
        ]
        if missing:
            raise UserError(
                _(
                    "The pickup address %(partner)s is incomplete, fill: "
                    "%(missing)s.",
                    partner=partner.display_name,
                    missing=", ".join(missing),
                )
            )
