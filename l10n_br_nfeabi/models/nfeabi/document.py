# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import random
import re
from pathlib import Path

from odoo import _, api, fields
from odoo.exceptions import UserError, ValidationError
from odoo.modules.module import get_module_path
from odoo.tools import float_compare, float_round

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    PROCESSADOR_OCA,
)
from odoo.addons.l10n_br_nfeabi_spec.bindings.v1_0 import (
    EvCancNfeAbi,
    EvCancNfeAbiDescEvento,
    EvDesfazimAlienac,
    EvDesfazimAlienacDescEvento,
    Evento,
    InfEventoTpAmb,
    InfEventoTpEvento,
    NfeAbi,
    Tevento,
    TinfNfeSupl,
)
from odoo.addons.spec_driven_model.models import spec_models

from ...constants.nfeabi import (
    EXCHANGE_BALANCE_NATURES,
    MODE_ASSIGNMENT,
    MODE_AUCTION,
    MODE_EXCHANGE,
    MODE_GENERAL,
    MODELO_FISCAL_NFEABI,
    NFEABI_CANCEL_EVENT,
    NFEABI_DETAILS_BY_NATURE,
    NFEABI_DOCUMENT_TYPES,
    NFEABI_ENVIRONMENTS,
    NFEABI_EVENT_VERSION,
    NFEABI_HOMOLOGATION_NAME,
    NFEABI_INSTRUMENTS,
    NFEABI_MODES,
    NFEABI_NATURES,
    NFEABI_NATURES_BY_MODE,
    NFEABI_OPERATION_DETAILS,
    NFEABI_UNDO_EVENT,
    NFEABI_UNDO_TYPES,
    NFEABI_VERSION,
    PROPERTY_NEW_RESIDENTIAL,
    PROPERTY_RESIDENTIAL_LOT,
)


def nfeabi_schema(name):
    """Path of a schema of the l10n_br_nfeabi_spec module."""
    return str(Path(get_module_path("l10n_br_nfeabi_spec"), "schemas", "v1_0", name))


def filter_nfeabi(record):
    return (
        record.processador_edoc == PROCESSADOR_OCA
        and record.document_type_id.code == MODELO_FISCAL_NFEABI
    )


def nfeabi_check_digit(key):
    """Modulo 11 (weights 2 to 9) check digit of the access key; the
    characters of an alphanumeric CNPJ count as their ASCII code minus 48
    (MOC NF-e ABI 1.00a, Visão Geral, item 2.2.3, and DFe NTCJ 2025.001)."""
    total = sum(
        (ord(char) - 48) * (2 + index % 8) for index, char in enumerate(reversed(key))
    )
    rest = total % 11
    return "0" if rest < 2 else str(11 - rest)


class NFeABI(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document"
    _inherit = ["l10n_br_fiscal.document", "nfeabi.10.tinfnfeabi"]

    _nfeabi10_odoo_module = "odoo.addons.l10n_br_nfeabi_spec.models.v1_0.nfe_abi_v1_00"
    _nfeabi10_stacking_mixin = "nfeabi.10.tinfnfeabi"
    _nfeabi10_stacking_force_paths = [
        "tinfnfeabi.infOper",
        "tinfnfeabi.gInfTrib",
        "tinfnfeabi.total",
        "tinfnfeabi.infAdic",
        "ide.gModNat",
        "infOper.gRedAjusteImovel",
    ]
    # NF-e ABI of transition, advance payment, contingency, exchange with a
    # balance (torna), development (incorporação) and public purchases are
    # not supported yet
    _nfeabi10_stacking_skip_paths = (
        "nfeabi10_gCont",
        "nfeabi10_gPagAntecipado",
        "nfeabi10_gInfTribTransic",
        "nfeabi10_gTorna",
        "nfeabi10_gIncorpLote",
        "nfeabi10_gCompraGov",
        "nfeabi10_pag",
    )

    nfeabi_environment = fields.Selection(
        selection=NFEABI_ENVIRONMENTS,
        string="NF-e ABI Environment",
        copy=False,
        default=lambda self: self.env.company.nfeabi_environment,
    )

    ##########################
    # NF-e ABI tag: infNFeABI
    ##########################

    nfeabi10_versao = fields.Char(compute="_compute_nfeabi10_versao")

    nfeabi10_Id = fields.Char(compute="_compute_nfeabi10_Id")

    def _compute_nfeabi10_versao(self):
        self.nfeabi10_versao = NFEABI_VERSION

    @api.depends("document_type_id", "document_key")
    def _compute_nfeabi10_Id(self):
        # MOC NF-e ABI 1.00a, Anexo I, A03: the key after the literal NFeABI
        for record in self:
            record.nfeabi10_Id = (
                f"{record.document_type_id.prefix}{record.document_key}"
                if record.document_key and record.document_type_id.prefix
                else False
            )

    ##########################
    # NF-e ABI tag: ide
    ##########################

    nfeabi10_cUF = fields.Selection(compute="_compute_nfeabi10_ide")
    nfeabi10_cNF = fields.Char(related="key_random_code")
    nfeabi10_mod = fields.Char(related="document_type_id.code")
    nfeabi10_serie = fields.Char(related="document_serie")
    nfeabi10_nNF = fields.Char(related="document_number")
    nfeabi10_dhEmi = fields.Datetime(related="document_date")
    nfeabi10_tpNF = fields.Selection(
        selection=NFEABI_DOCUMENT_TYPES,
        string="NF-e ABI Type",
        default="0",
        help="Simplified: the operation covers the whole property and has a "
        "single transmitter. Complete: part of the property or more than one "
        "transmitter (NT 2026.001, B08).",
    )
    nfeabi10_tpImp = fields.Char(default="1")
    nfeabi10_modOper = fields.Selection(
        selection=NFEABI_MODES, string="Operation Mode", default=MODE_GENERAL
    )
    nfeabi10_natOper = fields.Selection(
        selection=NFEABI_NATURES, string="Operation Nature", default="01"
    )
    nfeabi10_detOper = fields.Selection(
        selection=NFEABI_OPERATION_DETAILS, string="Operation Detail"
    )
    nfeabi10_tpEmis = fields.Char(default="1")
    nfeabi10_nSiteAutoriz = fields.Char(default="0")
    nfeabi10_cDV = fields.Char(related="key_check_digit")
    nfeabi10_tpAmb = fields.Selection(related="nfeabi_environment")
    nfeabi10_finNFe = fields.Char(default="1")
    nfeabi10_procEmi = fields.Char(default="0")
    nfeabi10_verProc = fields.Char(
        copy=False,
        default=lambda self: self.env["ir.config_parameter"]
        .sudo()
        .get_param("l10n_br_nfeabi.version.name", default="Odoo Brasil OCA v16"),
    )

    @api.depends("company_id")
    def _compute_nfeabi10_ide(self):
        for record in self:
            record.nfeabi10_cUF = record.company_id.state_id.ibge_code

    ##########################
    # NF-e ABI tags: emit, transmit, adquirente and imovel
    ##########################

    nfeabi10_emit = fields.Many2one(comodel_name="res.company", related="company_id")

    nfeabi10_transmit = fields.One2many(string="Transmitters", copy=True)

    nfeabi10_adquirente = fields.One2many(string="Acquirers", copy=True)

    nfeabi10_imovel = fields.Many2one(string="Property")

    ##########################
    # NF-e ABI tag: infOper
    ##########################

    nfeabi10_pTransImovel = fields.Float(
        string="Transferred Share of the Property (%)",
        default=100.0,
        help="Share of the property transferred by the whole operation "
        "(pTransImovel), informed only in the complete NF-e ABI.",
    )
    nfeabi10_vTotalOperacao = fields.Monetary(
        string="Total Operation Amount",
        compute="_compute_nfeabi_values",
        currency_field="currency_id",
    )
    nfeabi10_vInicial = fields.Monetary(
        string="Adjustment Reducer Initial Amount", currency_field="currency_id"
    )
    nfeabi10_vITBI = fields.Monetary(string="ITBI Amount", currency_field="currency_id")
    nfeabi10_vLaudemio = fields.Monetary(
        string="Laudemium Amount", currency_field="currency_id"
    )
    nfeabi10_vContrap = fields.Monetary(
        string="Counterparts Amount", currency_field="currency_id"
    )
    nfeabi10_vRedAjusteImovel = fields.Monetary(
        string="Property Adjustment Reducer",
        compute="_compute_nfeabi10_vRedAjusteImovel",
        store=True,
        readonly=False,
        currency_field="currency_id",
        help="Adjustment reducer of the property (arts. 257 and 258 of the LC "
        "214/2025). Computed as the initial amount plus ITBI, laudemium and "
        "counterparts when the initial amount is informed (rule H15-10).",
    )
    nfeabi10_indRedSocial = fields.Char(compute="_compute_nfeabi10_indRedSocial")
    nfeabi10_vRedSocial = fields.Monetary(
        string="Social Reducer",
        currency_field="currency_id",
        help="Social reducer (art. 259 of the LC 214/2025): R$ 100,000.00 for "
        "a new residential property or R$ 30,000.00 for a residential lot, "
        "updated by the IPCA since 01/16/2025. Informing it asks for the "
        "reducer; it is used only once per property.",
    )
    nfeabi10_tpInstrumento = fields.Selection(
        selection=NFEABI_INSTRUMENTS, string="Instrument Type", default="01"
    )
    nfeabi10_xOutrosInst = fields.Char(string="Other Instrument")
    nfeabi10_dtInstrumento = fields.Date(string="Instrument Date")
    nfeabi10_indIntermedCorret = fields.Char(
        compute="_compute_nfeabi10_indIntermedCorret"
    )
    nfeabi10_gIntermedCorret = fields.One2many(string="Brokers", copy=True)

    @api.depends(
        "nfeabi10_vInicial",
        "nfeabi10_vITBI",
        "nfeabi10_vLaudemio",
        "nfeabi10_vContrap",
    )
    def _compute_nfeabi10_vRedAjusteImovel(self):
        # MOC NF-e ABI 1.00a, rule H15-10
        for record in self:
            if record.nfeabi10_vInicial:
                record.nfeabi10_vRedAjusteImovel = (
                    record.nfeabi10_vInicial
                    + record.nfeabi10_vITBI
                    + record.nfeabi10_vLaudemio
                    + record.nfeabi10_vContrap
                )

    @api.depends(
        "nfeabi10_vRedSocial",
        "nfeabi10_modOper",
        "nfeabi10_natOper",
        "nfeabi10_imovel.nfeabi10_enquadramento",
    )
    def _compute_nfeabi10_indRedSocial(self):
        # MOC NF-e ABI 1.00a, H16, and NT 2026.001, rule H16-10
        for record in self:
            record.nfeabi10_indRedSocial = (
                ("1" if record.nfeabi10_vRedSocial else "0")
                if record._nfeabi_reducers_allowed()
                and record.nfeabi10_imovel.nfeabi10_enquadramento
                in (PROPERTY_NEW_RESIDENTIAL, PROPERTY_RESIDENTIAL_LOT)
                else False
            )

    @api.depends("nfeabi10_modOper", "nfeabi10_gIntermedCorret")
    def _compute_nfeabi10_indIntermedCorret(self):
        # MOC NF-e ABI 1.00a, H21: only for the general alienation mode
        for record in self:
            record.nfeabi10_indIntermedCorret = (
                ("1" if record.nfeabi10_gIntermedCorret else "0")
                if record.nfeabi10_modOper == MODE_GENERAL
                else False
            )

    ##########################
    # NF-e ABI tags: gInfTrib, total
    ##########################

    nfeabi10_vOperacIndiv = fields.Monetary(
        string="Declarant Operation Amount",
        compute="_compute_nfeabi_values",
        currency_field="currency_id",
    )
    nfeabi10_vRedAjusteIndiv = fields.Monetary(
        compute="_compute_nfeabi_values", currency_field="currency_id"
    )
    nfeabi10_vRedSocialIndiv = fields.Monetary(
        compute="_compute_nfeabi_values", currency_field="currency_id"
    )
    nfeabi10_vBC = fields.Monetary(
        string="IBS/CBS Base of the Declarant",
        compute="_compute_nfeabi_values",
        currency_field="currency_id",
    )
    nfeabi10_vIBSUF = fields.Monetary(
        compute="_compute_nfeabi_totals", currency_field="currency_id"
    )
    nfeabi10_vIBSMun = fields.Monetary(
        compute="_compute_nfeabi_totals", currency_field="currency_id"
    )
    nfeabi10_vCBS = fields.Monetary(
        compute="_compute_nfeabi_totals", currency_field="currency_id"
    )
    nfeabi10_vNF = fields.Monetary(
        string="NF-e ABI Total",
        compute="_compute_nfeabi_totals",
        currency_field="currency_id",
    )

    # IBSCBS is exported by the tag hooks below and gCompraGov is not
    # supported: both point to abstract types of nfeabiTiposBasico, so they are
    # not relational in the document, otherwise reading the stacked gInfTrib
    # group (l10n_br_nfe export) fails on the abstract comodel; IBSCBS is set
    # when there is IBS and CBS, so that the same export keeps the group
    nfeabi10_IBSCBS = fields.Boolean(compute="_compute_nfeabi10_IBSCBS")
    nfeabi10_gCompraGov = fields.Boolean()

    @api.depends("fiscal_line_ids.ibs_cst_id")
    def _compute_nfeabi10_IBSCBS(self):
        for record in self:
            record.nfeabi10_IBSCBS = bool(record._nfeabi_ibscbs_lines())

    def _export_field(self, xsd_field, class_obj, member_spec, export_value=None):
        if xsd_field == "nfeabi10_IBSCBS":
            return self._export_m2o_via_tag_hooks(xsd_field, class_obj)
        return super()._export_field(xsd_field, class_obj, member_spec, export_value)

    def _nfeabi_balance_exchange(self):
        """Exchange of real estate only (natOper 13 or 14), which taxes the
        balance (torna) alone."""
        self.ensure_one()
        return (
            self.nfeabi10_modOper == MODE_EXCHANGE
            and self.nfeabi10_natOper in EXCHANGE_BALANCE_NATURES
        )

    def _nfeabi_reducers_allowed(self):
        """Rules U12-50, U12-60, U13-80 and H16-10: no reducers in the
        assignment of rights nor in the exchange that taxes the balance."""
        self.ensure_one()
        return (
            self.nfeabi10_modOper != MODE_ASSIGNMENT
            and not self._nfeabi_balance_exchange()
        )

    def _nfeabi_declarant(self):
        self.ensure_one()
        return self.nfeabi10_transmit.filtered("is_declarant")[:1]

    def _nfeabi_declarant_share(self):
        """Share of the declarant in the operation: 1 in the simplified
        NF-e ABI, pTransIndiv / pTransImovel in the complete one."""
        self.ensure_one()
        if self.nfeabi10_tpNF != "1" or not self.nfeabi10_pTransImovel:
            return 1.0
        return self._nfeabi_declarant().transfer_percent / self.nfeabi10_pTransImovel

    @api.depends(
        "fiscal_line_ids.price_gross",
        "nfeabi10_tpNF",
        "nfeabi10_modOper",
        "nfeabi10_natOper",
        "nfeabi10_pTransImovel",
        "nfeabi10_transmit.transfer_percent",
        "nfeabi10_transmit.is_declarant",
        "nfeabi10_vRedAjusteImovel",
        "nfeabi10_vRedSocial",
        "nfeabi10_imovel.nfeabi10_enquadramento",
    )
    def _compute_nfeabi_values(self):
        """Tabela de Códigos NF-e ABI v1.01, sheets vOperacIndiv,
        vRedAjusteIndiv, vRedSocialIndiv and vBC; NT 2026.001, rules U10 to
        U14."""
        for record in self:
            currency = record.currency_id or record.company_id.currency_id
            total = sum(record.fiscal_line_ids.mapped("price_gross"))
            complete = record.nfeabi10_tpNF == "1"
            individual = total * record._nfeabi_declarant_share()
            adjustment = social = 0.0
            if record._nfeabi_reducers_allowed():
                # the complete NF-e ABI applies the transferred share, given
                # in percent, of the declarant (pTransIndiv)
                share = (
                    record._nfeabi_declarant().transfer_percent / 100
                    if complete
                    else 1.0
                )
                adjustment = record.nfeabi10_vRedAjusteImovel * share
                if record.nfeabi10_indRedSocial == "1":
                    social = record.nfeabi10_vRedSocial * share
            if record.nfeabi10_modOper == MODE_ASSIGNMENT:
                base = individual
            elif record._nfeabi_balance_exchange():
                # without balance (indTorna 0) the exchange is not taxed
                base = 0.0
            else:
                base = max(individual - adjustment - social, 0.0)
            record.nfeabi10_vTotalOperacao = total
            record.nfeabi10_vOperacIndiv = currency.round(individual)
            record.nfeabi10_vRedAjusteIndiv = currency.round(adjustment)
            record.nfeabi10_vRedSocialIndiv = currency.round(social)
            record.nfeabi10_vBC = currency.round(base)

    @api.depends(
        "nfeabi10_vOperacIndiv",
        "fiscal_line_ids.ibs_value",
        "fiscal_line_ids.cbs_value",
    )
    def _compute_nfeabi_totals(self):
        for record in self:
            lines = record._nfeabi_ibscbs_lines()
            record.nfeabi10_vIBSUF = sum(lines.mapped("ibs_value"))
            # the fiscal engine has no municipal IBS yet (0% in 2026)
            record.nfeabi10_vIBSMun = 0.0
            record.nfeabi10_vCBS = sum(lines.mapped("cbs_value"))
            # MOC NF-e ABI 1.00a and NT 2026.001, rule W11-10
            record.nfeabi10_vNF = (
                record.nfeabi10_vOperacIndiv
                + record.nfeabi10_vIBSUF
                + record.nfeabi10_vIBSMun
                + record.nfeabi10_vCBS
            )

    def _nfeabi_ibscbs_lines(self):
        return self.fiscal_line_ids.filtered("ibs_cst_id")

    def _nfeabi_ibscbs_base(self):
        """IBS and CBS base of the declarant (vBC), used by the fiscal
        engine on the line of the NF-e ABI."""
        self.ensure_one()
        return self.nfeabi10_vBC

    def _export_tag_nfeabi_10_ibscbs(self, xsd_fields, class_obj, export_dict):
        """IBSCBS group of the declarant (MOC NF-e ABI 1.00a, U06)."""
        line = self._nfeabi_ibscbs_lines()[:1]
        if not line:
            return
        export_dict["CST"] = line.ibs_cst_id.code
        export_dict["cClassTrib"] = line.tax_classification_id.code

    def _export_tag_nfeabi_10_gibscbs(self, xsd_fields, class_obj, export_dict):
        export_dict["vOperacIndiv"] = self.nfeabi10_vOperacIndiv
        if self._nfeabi_reducers_allowed():
            export_dict["vRedAjusteIndiv"] = self.nfeabi10_vRedAjusteIndiv
            if self.nfeabi10_indRedSocial:
                export_dict["vRedSocialIndiv"] = self.nfeabi10_vRedSocialIndiv
        export_dict["vBC"] = self.nfeabi10_vBC

    def _nfeabi_reduction(self, percent, reduction):
        """gRed values: the effective rate applied to vBC (rules U20, U26
        and U32: value = pAliqEfet * vBC)."""
        return {
            "pRedAliq": reduction,
            "pAliqEfet": float_round(percent * (1 - reduction / 100), 4),
        }

    def _export_tag_nfeabi_10_gibsuf(self, xsd_fields, class_obj, export_dict):
        line = self._nfeabi_ibscbs_lines()[:1]
        export_dict["pIBSUF"] = line.ibs_percent
        export_dict["vIBSUF"] = self.nfeabi10_vIBSUF

    def _export_tag_nfeabi_10_gibsuf_gred(self, xsd_fields, class_obj, export_dict):
        line = self._nfeabi_ibscbs_lines()[:1]
        export_dict.update(self._nfeabi_reduction(line.ibs_percent, line.ibs_reduction))

    def _export_tag_nfeabi_10_gibsmun(self, xsd_fields, class_obj, export_dict):
        export_dict["pIBSMun"] = 0.0
        export_dict["vIBSMun"] = self.nfeabi10_vIBSMun

    def _export_tag_nfeabi_10_gibsmun_gred(self, xsd_fields, class_obj, export_dict):
        export_dict.update(self._nfeabi_reduction(0.0, 0.0))

    def _export_tag_nfeabi_10_gcbs(self, xsd_fields, class_obj, export_dict):
        line = self._nfeabi_ibscbs_lines()[:1]
        export_dict["pCBS"] = line.cbs_percent
        export_dict["vCBS"] = self.nfeabi10_vCBS

    def _export_tag_nfeabi_10_gcbs_gred(self, xsd_fields, class_obj, export_dict):
        line = self._nfeabi_ibscbs_lines()[:1]
        export_dict.update(self._nfeabi_reduction(line.cbs_percent, line.cbs_reduction))

    ##########################
    # NF-e ABI tag: infAdic and infRespTec
    ##########################

    nfeabi10_infAdFisco = fields.Char(compute="_compute_nfeabi10_infAdic")
    nfeabi10_infCpl = fields.Char(compute="_compute_nfeabi10_infAdic")
    nfeabi10_CNPJ = fields.Char(compute="_compute_nfeabi10_infRespTec")
    nfeabi10_xContato = fields.Char(compute="_compute_nfeabi10_infRespTec")
    nfeabi10_email = fields.Char(compute="_compute_nfeabi10_infRespTec")
    nfeabi10_fone = fields.Char(compute="_compute_nfeabi10_infRespTec")

    @api.depends("fiscal_additional_data", "customer_additional_data")
    def _compute_nfeabi10_infAdic(self):
        for record in self:
            record.nfeabi10_infAdFisco = " ".join(
                (record.fiscal_additional_data or "").split()
            )
            record.nfeabi10_infCpl = " ".join(
                (record.customer_additional_data or "").split()
            )

    @api.depends("company_id.nfeabi_technical_partner_id")
    def _compute_nfeabi10_infRespTec(self):
        for record in self:
            values = record.company_id._nfeabi_technical_responsible()
            record.nfeabi10_CNPJ = values["CNPJ"]
            record.nfeabi10_xContato = values["xContato"]
            record.nfeabi10_email = values["email"]
            record.nfeabi10_fone = values["fone"]

    ################################
    # Framework Spec model's methods
    ################################

    def _export_fields_nfeabi_10_tinfnfeabi(self, xsd_fields, class_obj, export_dict):
        if not (self.nfeabi10_infAdFisco or self.nfeabi10_infCpl):
            xsd_fields.remove("nfeabi10_infAdic")

    def _export_fields_nfeabi_10_tinfoper(self, xsd_fields, class_obj, export_dict):
        if self.nfeabi10_tpNF != "1":
            # MOC NF-e ABI 1.00a, rule H02-10
            xsd_fields.remove("nfeabi10_pTransImovel")
        if not self._nfeabi_reducers_allowed():
            # MOC NF-e ABI 1.00a, H11
            xsd_fields.remove("nfeabi10_gRedAjusteImovel")

    def _export_one2many(self, field_name, class_obj=None):
        if field_name != "nfeabi10_transmit":
            return super()._export_one2many(field_name, class_obj)
        # MOC NF-e ABI 1.00a, E02: the declarant is the transmitter number 1
        transmitters = self.nfeabi10_transmit.sorted(lambda t: not t.is_declarant)
        return [
            transmitter._build_binding(
                class_name=class_obj._fields[field_name].comodel_name
            )
            for transmitter in transmitters
        ]

    ################################
    # Business Model Methods
    ################################

    def _nfeabi_qrcode(self):
        """NT 2026.001, item 5.2 (normal emission)."""
        self.ensure_one()
        return (
            f"{self.company_id.nfeabi_qrcode_url}?chNFeABI={self.document_key}"
            f"&tpAmb={self.nfeabi_environment}"
        )

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filter_nfeabi):
            inf = record._build_binding("nfeabi", "10")
            # MOC NF-e ABI 1.00a, C18: the issuer is the seller in the
            # supported modes
            inf.emit.tpEmit = "01"
            if record.nfeabi_environment == "2":
                # NT 2026.001, rule C04-10
                inf.emit.xNome = NFEABI_HOMOLOGATION_NAME
            edocs.append(
                NfeAbi(
                    infNFeABI=inf,
                    infNFeSupl=TinfNfeSupl(
                        qrCode=record._nfeabi_qrcode(),
                        urlChave=record.company_id.nfeabi_key_query_url,
                    ),
                )
            )
        return edocs

    def _nfeabi_sign(self, binding, doc_id):
        certificate = self.company_id.sudo().certificate
        return binding.to_xml(
            pkcs12_data=certificate.with_context(bin_size=False).file,
            pkcs12_password=certificate.password,
            doc_id=doc_id,
        )

    def _nfeabi_event_environment(self):
        return EVENT_ENV_PROD if self.nfeabi_environment == "1" else EVENT_ENV_HML

    def _document_export(self, **kwargs):
        result = super()._document_export(**kwargs)
        for record in self.filtered(filter_nfeabi):
            edoc = record.serialize()[0]
            signed_xml = record._nfeabi_sign(edoc, edoc.infNFeABI.Id)
            if (
                record.authorization_event_id
                and record.authorization_event_id.state == "draft"
            ):
                record.sudo().authorization_event_id.unlink()
            record.authorization_event_id = record.event_ids.create_event_save_xml(
                company_id=record.company_id,
                environment=record._nfeabi_event_environment(),
                event_type="0",
                xml_file=signed_xml,
                document_id=record,
            )
            record._validate_xml(signed_xml)
        return result

    def _validate_xml(self, xml_file):
        self.ensure_one()
        if not filter_nfeabi(self):
            return super()._validate_xml(xml_file)
        errors = NfeAbi.schema_validation(xml_file, nfeabi_schema("NFeABI_v1.00.xsd"))
        self.write({"xml_error_message": "\n".join(errors) or False})

    def _generate_key(self):
        nfeabi = self.filtered(filter_nfeabi)
        result = super(NFeABI, self - nfeabi)._generate_key()
        for record in nfeabi:
            # MOC NF-e ABI 1.00a, Visão Geral, item 2.2.3 (chave de acesso)
            date = fields.Datetime.context_timestamp(record, record.document_date)
            if not record.key_random_code:
                record.key_random_code = str(random.randint(1, 9999998)).zfill(7)
            issuer = re.sub(r"[^A-Z0-9]", "", (record.company_id.vat or "").upper())
            key = "".join(
                (
                    record.company_id.state_id.ibge_code or "",
                    date.strftime("%y%m"),
                    issuer.zfill(14),
                    record.document_type_id.code,
                    (record.document_serie or "").zfill(3),
                    (record.document_number or "").zfill(9),
                    record.nfeabi10_tpEmis or "1",
                    record.nfeabi10_nSiteAutoriz or "0",
                    record.key_random_code,
                )
            )
            if len(key) != 43:
                raise ValidationError(
                    _(
                        "Cannot build the NF-e ABI access key of %(document)s: "
                        "check the company CNPJ or CPF and state, the serie and "
                        "the number.",
                        document=record.display_name,
                    )
                )
            record.key_check_digit = nfeabi_check_digit(key)
            record.document_key = key + record.key_check_digit
        return result

    @api.constrains("document_key")
    def _check_key(self):
        # erpbrasil.base does not know the model 77 yet
        nfeabi = self.filtered(
            lambda d: d.document_type_id.code == MODELO_FISCAL_NFEABI
        )
        result = super(NFeABI, self - nfeabi)._check_key()
        for record in nfeabi.filtered("document_key"):
            key = record.document_key
            if len(key) != 44 or key[-1] != nfeabi_check_digit(key[:-1]):
                raise ValidationError(_("Invalid NF-e ABI access key: %s") % key)
            if self.search_count(
                [
                    ("id", "!=", record.id),
                    ("company_id", "=", record.company_id.id),
                    ("issuer", "=", record.issuer),
                    ("document_key", "=", key),
                    ("document_type_id", "=", record.document_type_id.id),
                ]
            ):
                raise ValidationError(
                    _("There is already a fiscal document with this key: %s") % key
                )
        return result

    def _document_number(self):
        if (
            filter_nfeabi(self)
            and self.issuer == DOCUMENT_ISSUER_COMPANY
            and not self.document_serie_id
        ):
            self.document_serie_id = self.document_type_id.get_document_serie(
                self.company_id, self.fiscal_operation_id
            )
        return super()._document_number()

    def _document_check(self):
        result = super()._document_check()
        for record in self.filtered(filter_nfeabi):
            record._check_nfeabi_required_fields()
            # the IBS and CBS base of the line depends on the reducers and on
            # the shares informed in the document
            record.fiscal_line_ids._compute_tax_fields()
        return result

    def _check_nfeabi_required_fields(self):  # noqa: C901
        self.ensure_one()
        missing = []

        def check(value, label):
            if not value:
                missing.append(label)

        company = self.company_id
        check(company.vat, _("Company CNPJ or CPF"))
        check(company.state_id, _("Company State"))
        check(company.city_id, _("Company City"))
        check(company.sudo().certificate, _("Digital Certificate"))
        check(company.nfeabi_qrcode_url, _("NF-e ABI QR Code URL of the company"))
        check(company.nfeabi_key_query_url, _("NF-e ABI Key Query URL of the company"))
        responsible = company._nfeabi_technical_responsible()
        check(
            responsible["CNPJ"] and responsible["email"] and responsible["fone"],
            _("CNPJ, e-mail and phone of the technical responsible"),
        )
        check(self.document_serie_id, _("Document Serie"))
        check(self.nfeabi10_imovel, _("Property"))
        check(self.nfeabi10_adquirente, _("Acquirers"))
        check(self.nfeabi10_dtInstrumento, _("Instrument Date"))
        if self.nfeabi10_tpInstrumento == "99":
            # MOC NF-e ABI 1.00a, H19
            check(self.nfeabi10_xOutrosInst, _("Other Instrument"))
        if self.nfeabi10_imovel:
            missing += self.nfeabi10_imovel._nfeabi_missing_fields()
        declarant = self._nfeabi_declarant()
        check(declarant, _("The company as one of the transmitters (declarant)"))
        lines = self._nfeabi_ibscbs_lines()
        if len(self.fiscal_line_ids) != 1 or len(lines) != 1:
            missing.append(_("A single document line with the IBS and CBS taxes"))
        else:
            check(lines.tax_classification_id, _("Tax Classification (cClassTrib)"))
        if missing:
            raise UserError(
                _("Fill in the required NF-e ABI fields:\n- %s") % "\n- ".join(missing)
            )
        self._check_nfeabi_operation()

    def _check_nfeabi_operation(self):
        self.ensure_one()
        errors = []
        mode = self.nfeabi10_modOper
        if mode == MODE_AUCTION:
            errors.append(
                _(
                    "The judicial auction, adjudication and redemption mode is "
                    "not supported yet."
                )
            )
        elif self.nfeabi10_natOper not in NFEABI_NATURES_BY_MODE[mode]:
            # Tabela de Códigos NF-e ABI v1.01, sheet gModNat
            errors.append(_("The operation nature does not belong to the mode."))
        if self.nfeabi10_detOper and (
            mode == MODE_EXCHANGE
            or self.nfeabi10_detOper
            not in NFEABI_DETAILS_BY_NATURE.get(self.nfeabi10_natOper, ())
        ):
            # NT 2026.001, rule B13-10, and sheet gModNat
            errors.append(_("The operation detail does not belong to the nature."))
        transmitters = self.nfeabi10_transmit
        if self.nfeabi10_tpNF == "0" and len(transmitters) > 1:
            # NT 2026.001, rule E01a-20
            errors.append(_("The simplified NF-e ABI accepts a single transmitter."))
        if self.nfeabi10_tpNF == "1":
            # MOC NF-e ABI 1.00a, rules E18-20, H02-20 and H02-30
            if not self.nfeabi10_pTransImovel or any(
                not transmitter.transfer_percent for transmitter in transmitters
            ):
                errors.append(
                    _(
                        "The complete NF-e ABI needs the transferred share of the "
                        "property and of each transmitter."
                    )
                )
            elif float_compare(
                sum(transmitters.mapped("transfer_percent")),
                self.nfeabi10_pTransImovel,
                precision_digits=4,
            ):
                errors.append(
                    _(
                        "The shares of the transmitters must add up to the "
                        "transferred share of the property."
                    )
                )
        if self.nfeabi10_vRedSocial and not self.nfeabi10_indRedSocial:
            # MOC NF-e ABI 1.00a, H16 and H16a; NT 2026.001, rule H16-10
            errors.append(
                _(
                    "The social reducer is only allowed for a new residential "
                    "property or a residential lot, out of the assignment of "
                    "rights and of the exchange of real estate."
                )
            )
        if errors:
            raise UserError("\n".join(errors))

    def _eletronic_document_send(self):
        if self.filtered(filter_nfeabi):
            raise UserError(
                _(
                    "The NF-e ABI transmission to the tax authority is not "
                    "available yet. Use the signed XML of the document "
                    "authorization event."
                )
            )
        return super()._eletronic_document_send()

    def _document_cancel(self, justificative):
        if self.filtered(filter_nfeabi):
            raise UserError(
                _(
                    "The NF-e ABI transmission to the tax authority is not "
                    "available yet, so the NF-e ABI cannot be cancelled from "
                    "Odoo."
                )
            )
        return super()._document_cancel(justificative)

    def _nfeabi_event_xml(self, event_type, detail, sequence=1):
        """Signed XML of an event of the NF-e ABI (MOC NF-e ABI 1.00a,
        Visão Geral, item 5.4, and NT 2026.001, chapter 3)."""
        self.ensure_one()
        event_date = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        identification = self.company_id.partner_id._nfeabi_identification()
        event_id = f"ID{event_type}{self.document_key}{sequence:03d}"
        event = Evento(
            versao=NFEABI_EVENT_VERSION,
            infEvento=Tevento.InfEvento(
                cOrgao=self.company_id.state_id.ibge_code,
                tpAmb=InfEventoTpAmb(self.nfeabi_environment),
                CNPJ=identification["CNPJ"] or None,
                CPF=identification["CPF"] or None,
                chNFeABI=self.document_key,
                dhEvento=event_date.replace(microsecond=0).isoformat(),
                tpEvento=InfEventoTpEvento(event_type),
                nSeqEvento=str(sequence),
                verEvento=NFEABI_EVENT_VERSION,
                detEvento=Tevento.InfEvento.DetEvento(
                    versaoEvento=NFEABI_EVENT_VERSION, any_element=detail
                ),
                Id=event_id,
            ),
        )
        return self._nfeabi_sign(event, event_id)

    def _nfeabi_cancel_event_xml(self, justification):
        """Cancellation event (110111)."""
        return self._nfeabi_event_xml(
            NFEABI_CANCEL_EVENT,
            EvCancNfeAbi(
                versao=NFEABI_EVENT_VERSION,
                descEvento=EvCancNfeAbiDescEvento.CANCELAMENTO,
                nProt=self.authorization_protocol,
                xJust=justification,
            ),
        )

    def _nfeabi_undo_event_xml(self, undo_type, undo_date, description=None):
        """Undo of the alienation event (112320, NT 2026.001, ZZC01)."""
        if undo_type not in dict(NFEABI_UNDO_TYPES):
            raise UserError(_("Invalid undo type: %s") % undo_type)
        if undo_type == "99" and not description:
            # NT 2026.001, ZZC04
            raise UserError(_("Describe the undo of the alienation."))
        return self._nfeabi_event_xml(
            NFEABI_UNDO_EVENT,
            EvDesfazimAlienac(
                versao=NFEABI_EVENT_VERSION,
                descEvento=EvDesfazimAlienacDescEvento.EVENTO_DE_DESFAZIMENTO_DA_ALIENA_O,
                tpDesfaz=undo_type,
                dtDesfaz=fields.Date.to_string(undo_date),
                xDesfaz=description,
            ),
        )
