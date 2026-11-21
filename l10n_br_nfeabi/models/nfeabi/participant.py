# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields

from odoo.addons.l10n_br_fiscal.constants.fiscal import TAX_FRAMEWORK_SIMPLES_ALL
from odoo.addons.spec_driven_model.models import spec_models

from ...constants.nfeabi import MODE_AUCTION, NFEABI_CONTRIBUTOR


class NfeAbiParticipantMixin:
    """Identification (CNPJ or CPF and name) taken from the partner."""

    @api.depends("partner_id.cnpj_cpf_stripped", "partner_id.legal_name")
    def _compute_nfeabi_identification(self):
        for record in self:
            values = record.partner_id._nfeabi_identification()
            record.nfeabi10_CNPJ = values["CNPJ"]
            record.nfeabi10_CPF = values["CPF"]
            record.nfeabi10_xNome = values["xNome"]

    def _nfeabi_sequence(self, field_name, siblings):
        for record in self:
            records = list(siblings(record))
            position = records.index(record) + 1 if record in records else 1
            record[field_name] = str(position)


class NfeAbiTransmitter(NfeAbiParticipantMixin, spec_models.SpecModel):
    """Seller, transmitter or assignor of the property (MOC NF-e ABI 1.00a,
    group E). The company issuing the NF-e ABI is the declarant."""

    _name = "l10n_br_nfeabi.transmitter"
    _inherit = "nfeabi.10.ttransmit"
    _description = "NF-e ABI Transmitter"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        related="nfeabi10_transmit_TInfNFeABI_id",
    )

    partner_id = fields.Many2one(comodel_name="res.partner", required=True)

    is_declarant = fields.Boolean(compute="_compute_is_declarant")

    transfer_percent = fields.Float(
        string="Transferred Share (%)",
        digits=(7, 4),
        help="Share of the property transferred by this transmitter, in "
        "percent (pTransIndiv). Informed only in the complete NF-e ABI.",
    )

    nfeabi10_CNPJ = fields.Char(compute="_compute_nfeabi_identification")
    nfeabi10_CPF = fields.Char(compute="_compute_nfeabi_identification")
    nfeabi10_xNome = fields.Char(compute="_compute_nfeabi_identification")

    nfeabi10_nTransmit = fields.Char(compute="_compute_nfeabi10_nTransmit")

    nfeabi10_indDeclarante = fields.Char(compute="_compute_nfeabi_complete")

    nfeabi10_pTransIndiv = fields.Float(compute="_compute_nfeabi_complete")

    nfeabi10_enderTransmit = fields.Many2one(
        comodel_name="res.partner", compute="_compute_nfeabi_complete"
    )

    nfeabi10_indContrib = fields.Selection(
        selection=NFEABI_CONTRIBUTOR,
        string="IBS/CBS Contributor",
        compute="_compute_nfeabi10_indContrib",
        store=True,
        readonly=False,
    )

    @api.depends("partner_id", "document_id.company_id")
    def _compute_is_declarant(self):
        for record in self:
            record.is_declarant = bool(
                record.partner_id
                and record.partner_id == record.document_id.company_id.partner_id
            )

    def _compute_nfeabi10_nTransmit(self):
        # MOC NF-e ABI 1.00a, E02: the declarant is the transmitter number 1
        self._nfeabi_sequence(
            "nfeabi10_nTransmit",
            lambda record: record.document_id.nfeabi10_transmit.sorted(
                lambda transmitter: not transmitter.is_declarant
            ),
        )

    @api.depends(
        "is_declarant",
        "transfer_percent",
        "document_id.nfeabi10_tpNF",
        "document_id.nfeabi10_modOper",
    )
    def _compute_nfeabi_complete(self):
        for record in self:
            complete = record.document_id.nfeabi10_tpNF == "1"
            # NT 2026.001, rules E02-10 and E02-20; MOC NF-e ABI 1.00a, E18
            # and E06 (address of the declarant)
            record.nfeabi10_indDeclarante = (
                ("1" if record.is_declarant else "0")
                if complete and record.document_id.nfeabi10_modOper != MODE_AUCTION
                else False
            )
            record.nfeabi10_pTransIndiv = record.transfer_percent if complete else 0.0
            record.nfeabi10_enderTransmit = (
                record.partner_id if record.is_declarant else False
            )

    @api.depends("partner_id")
    def _compute_nfeabi10_indContrib(self):
        for record in self:
            partner = record.partner_id
            if not partner.is_company:
                record.nfeabi10_indContrib = "0"
            elif partner.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
                record.nfeabi10_indContrib = "2"
            else:
                record.nfeabi10_indContrib = "1"


class NfeAbiAcquirer(NfeAbiParticipantMixin, spec_models.SpecModel):
    """Buyer, acquirer or assignee of the property (MOC NF-e ABI 1.00a,
    group F)."""

    _name = "l10n_br_nfeabi.acquirer"
    _inherit = "nfeabi.10.tadquirente"
    _description = "NF-e ABI Acquirer"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        related="nfeabi10_adquirente_TInfNFeABI_id",
    )

    partner_id = fields.Many2one(comodel_name="res.partner", required=True)

    nfeabi10_CNPJ = fields.Char(compute="_compute_nfeabi_identification")
    nfeabi10_CPF = fields.Char(compute="_compute_nfeabi_identification")
    nfeabi10_xNome = fields.Char(compute="_compute_nfeabi_identification")

    nfeabi10_nAdquir = fields.Char(compute="_compute_nfeabi10_nAdquir")

    nfeabi10_enderAdquirente = fields.Many2one(
        comodel_name="res.partner", related="partner_id"
    )

    def _compute_nfeabi10_nAdquir(self):
        self._nfeabi_sequence(
            "nfeabi10_nAdquir", lambda record: record.document_id.nfeabi10_adquirente
        )


class NfeAbiBroker(NfeAbiParticipantMixin, spec_models.SpecModel):
    """Broker of the operation hired by the seller (MOC NF-e ABI 1.00a, H22)."""

    _name = "l10n_br_nfeabi.broker"
    _inherit = "nfeabi.10.tgintermedcorret"
    _description = "NF-e ABI Broker"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        related="nfeabi10_gIntermedCorret_TInfOper_id",
    )

    partner_id = fields.Many2one(comodel_name="res.partner", required=True)

    nfeabi10_CNPJ = fields.Char(compute="_compute_nfeabi_identification")
    nfeabi10_CPF = fields.Char(compute="_compute_nfeabi_identification")
    nfeabi10_xNome = fields.Char(compute="_compute_nfeabi_identification")

    nfeabi10_nCorretagem = fields.Char(compute="_compute_nfeabi10_nCorretagem")

    nfeabi10_vCorretagem = fields.Monetary(string="Brokerage Amount", required=True)

    def _compute_nfeabi10_nCorretagem(self):
        self._nfeabi_sequence(
            "nfeabi10_nCorretagem",
            lambda record: record.document_id.nfeabi10_gIntermedCorret,
        )
