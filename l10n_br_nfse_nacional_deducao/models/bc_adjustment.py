# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from nfelib.nfse.bindings.v1_0.tipos_complexos_v1_01 import (
    TcdocAjusteBc,
    TcinfoPessoa,
    TcrtclistaDocDfe,
    TcrtclistaDocFiscalOutro,
    TcrtclistaDocOutro,
)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# TSRTCTpAjusteBC, leiaute 1.04.01 (NT 009)
ADJUSTMENT_TYPES = [
    ("2", "Materials"),
    ("5", "Consortium transfer"),
    ("6", "Health plan transfer"),
    ("7", "Services"),
    ("8", "Labor subcontracting"),
    ("9", "Partner professional"),
    ("99", "Other ISSQN only deductions"),
    ("101", "Real estate brokerage fee passed on to other brokers"),
    ("102", "Amount passed on to a supplier intermediated by a travel agency"),
    ("103", "Advertising agency refund of external production for third parties"),
    ("104", "Advertising agency refund of media for third parties"),
    ("105", "Health services disallowance"),
    ("199", "Other refunds of amounts paid on behalf of third parties"),
]
# adjustments of the ISSQN base only, the others being refunds that also
# leave the IBS/CBS base (rules E0435 and E0462)
ISSQN_ADJUSTMENT_TYPES = ("2", "5", "6", "7", "8", "9", "99")
DESCRIBED_ADJUSTMENT_TYPES = ("99", "199")
# rule E0479: these types need a fiscal document
FISCAL_ADJUSTMENT_TYPES = ("101", "103", "104", "199")

DFE_TYPE_BY_DOCUMENT_TYPE = {"SE": "1", "55": "2", "57": "3"}
DFE_KEY_LENGTH = {"1": 50, "2": 44, "3": 44}


class BcAdjustment(models.Model):
    _name = "l10n_br_nfse_nacional.bc.adjustment"
    _description = "NFS-e Nacional Tax Base Adjustment Document"
    _order = "document_id, id"

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="NFS-e",
        required=True,
        ondelete="cascade",
        index=True,
    )
    currency_id = fields.Many2one(related="document_id.currency_id")
    adjustment_type = fields.Selection(
        selection=ADJUSTMENT_TYPES,
        required=True,
        help="tpAjusteBC: what the document deducts from the tax base.",
    )
    adjustment_description = fields.Char(
        size=150,
        help="Required for the types 99 and 199, refused for the others.",
    )
    source_document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
        help="Fiscal document registered in Odoo that supports the "
        "adjustment: its key, amount, dates and supplier are copied.",
    )
    reference_type = fields.Selection(
        selection=[
            ("dfe", "Electronic document of the national repository"),
            ("fiscal", "Other fiscal document"),
            ("other", "Non fiscal document"),
        ],
        required=True,
        default="dfe",
    )
    dfe_type = fields.Selection(
        selection=[("1", "NFS-e"), ("2", "NF-e"), ("3", "CT-e"), ("9", "Other")],
        string="Electronic Document Type",
        compute="_compute_dfe_type",
        store=True,
        readonly=False,
    )
    dfe_type_description = fields.Char(
        string="Electronic Document Description",
        size=255,
    )
    dfe_key = fields.Char(
        string="Access Key",
        size=50,
        compute="_compute_dfe_key",
        store=True,
        readonly=False,
    )
    fiscal_city_id = fields.Many2one(
        comodel_name="res.city",
        string="Issuer City",
    )
    reference_number = fields.Char(size=255)
    reference_description = fields.Char(size=255)
    document_amount = fields.Monetary(
        compute="_compute_document_amount",
        store=True,
        readonly=False,
        help="vTotDoc: total amount of the supporting document.",
    )
    applied_amount = fields.Monetary(
        required=True,
        help="vAjusteAplic: part of the document amount deducted from the base "
        "of this NFS-e.",
    )
    issue_date = fields.Date(
        compute="_compute_issue_date",
        store=True,
        readonly=False,
    )
    competence_date = fields.Date(
        compute="_compute_competence_date",
        store=True,
        readonly=False,
    )
    supplier_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier",
        compute="_compute_supplier_id",
        store=True,
        readonly=False,
    )

    def _compute_from_source(self, field_name, value_of):
        # one compute per field: a value given on create protects its field only
        for adjustment in self:
            source = adjustment.source_document_id
            adjustment[field_name] = (
                value_of(source) if source else adjustment[field_name]
            )

    @api.depends("source_document_id")
    def _compute_dfe_type(self):
        self._compute_from_source(
            "dfe_type",
            lambda source: DFE_TYPE_BY_DOCUMENT_TYPE.get(
                source.document_type_id.code, "9"
            ),
        )

    @api.depends("source_document_id")
    def _compute_dfe_key(self):
        self._compute_from_source(
            "dfe_key", lambda source: source.nfse_key or source.document_key
        )

    @api.depends("source_document_id")
    def _compute_document_amount(self):
        self._compute_from_source(
            "document_amount", lambda source: source.fiscal_amount_total
        )

    @api.depends("source_document_id")
    def _compute_issue_date(self):
        self._compute_from_source("issue_date", self._source_date)

    @api.depends("source_document_id")
    def _compute_competence_date(self):
        self._compute_from_source("competence_date", self._source_date)

    @api.depends("source_document_id")
    def _compute_supplier_id(self):
        self._compute_from_source("supplier_id", lambda source: source.partner_id)

    @api.model
    def _source_date(self, source):
        return source.document_date and source.document_date.date()

    @api.constrains(
        "adjustment_type",
        "adjustment_description",
        "reference_type",
        "dfe_type",
        "dfe_type_description",
        "dfe_key",
        "document_amount",
        "applied_amount",
        "issue_date",
        "competence_date",
    )
    def _check_nfse_rules(self):
        for adjustment in self:
            errors = adjustment._nfse_rule_errors()
            if errors:
                raise ValidationError("\n".join(errors))

    def _nfse_rule_errors(self):
        """Level 1 rules of the docAjusteBC group (Anexo VI, leiaute
        1.04.01 of NT 009) that need nothing but the adjustment itself."""
        self.ensure_one()
        errors = []
        described = self.adjustment_type in DESCRIBED_ADJUSTMENT_TYPES
        if described and not self.adjustment_description:
            errors.append(_("E0465: the types 99 and 199 need a description."))
        if not described and self.adjustment_description:
            errors.append(_("E0464: only the types 99 and 199 take a description."))
        if self.applied_amount > self.document_amount:
            errors.append(_("E0469: the applied amount exceeds the document amount."))
        if (
            self.issue_date
            and self.competence_date
            and self.competence_date > self.issue_date
        ):
            errors.append(
                _("E0472: the competence date is after the document issue date.")
            )
        if self.reference_type == "dfe":
            if self.dfe_type == "9" and not self.dfe_type_description:
                errors.append(
                    _("E0470: describe the electronic document of type Other.")
                )
            length = DFE_KEY_LENGTH.get(self.dfe_type)
            key = self.dfe_key or ""
            if length and (len(key) != length or not key.isdigit()):
                errors.append(
                    _(
                        "E0460: the access key must have %(length)s digits.",
                        length=length,
                    )
                )
        if self.reference_type == "fiscal" and not (
            self.competence_date and self.competence_date < date(2026, 1, 1)
        ):
            errors.append(
                _(
                    "E0476: a fiscal document outside the national repository "
                    "is accepted only with a competence before 2026."
                )
            )
        if (
            self.reference_type == "other"
            and self.adjustment_type in FISCAL_ADJUSTMENT_TYPES
        ):
            errors.append(
                _("E0479: the types 101, 103, 104 and 199 need a fiscal document.")
            )
        return errors

    def _nfse_binding(self):
        """docAjusteBC element (TCDocAjusteBC) of the adjustment."""
        self.ensure_one()
        values = {
            "tpAjusteBC": self.adjustment_type,
            "xTpAjusteBC": self.adjustment_description or None,
            "vTotDoc": f"{self.document_amount:.2f}",
            "vAjusteAplic": f"{self.applied_amount:.2f}",
            "dtEmiDoc": self.issue_date and fields.Date.to_string(self.issue_date),
            "dtCompDoc": self.competence_date
            and fields.Date.to_string(self.competence_date),
        }
        if self.reference_type == "dfe":
            values["dFeNacional"] = TcrtclistaDocDfe(
                tipoChaveDFe=self.dfe_type,
                xTipoChaveDFe=self.dfe_type_description or None,
                chaveDFe=self.dfe_key,
            )
        elif self.reference_type == "fiscal":
            values["docFiscalOutro"] = TcrtclistaDocFiscalOutro(
                cMunDocFiscal=self.fiscal_city_id.ibge_code,
                nDocFiscal=self.reference_number,
                xDocFiscal=self.reference_description,
            )
        else:
            values["docOutro"] = TcrtclistaDocOutro(
                nDoc=self.reference_number,
                xDoc=self.reference_description,
            )
        if self.supplier_id:
            supplier = self.supplier_id
            values["fornec"] = TcinfoPessoa(
                CNPJ=supplier.nfse10_CNPJ or None,
                CPF=supplier.nfse10_CPF or None,
                NIF=supplier.nfse10_NIF or None,
                cNaoNIF=supplier.nfse10_cNaoNIF or None,
                xNome=supplier.nfse10_xNome,
            )
        return TcdocAjusteBc(**{k: v for k, v in values.items() if v})
