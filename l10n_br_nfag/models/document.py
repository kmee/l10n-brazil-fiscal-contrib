# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import random
import re
from unicodedata import normalize

from erpbrasil.base.misc import punctuation_rm

from odoo import _, api, fields
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_FISCAL_CANCELADO,
)
from odoo.addons.l10n_br_fiscal_edi.tools import tax_authority_date_to_utc
from odoo.addons.l10n_br_nfag_spec.bindings.v1_0 import (
    EvCancNfag,
    EvCancNfagDescEvento,
    EventoNfag,
    Nfag,
    Tamb,
    TcorgaoIbge,
    Tnfag,
)
from odoo.addons.spec_driven_model.models import spec_models

from ..constants.nfag import (
    MODELO_FISCAL_NFAG,
    NFAG_AUTHORIZED,
    NFAG_CANCEL_EVENT,
    NFAG_COFINS_CST,
    NFAG_ENVIRONMENTS,
    NFAG_EVENT_REGISTERED,
    NFAG_EVENT_SEQUENCE,
    NFAG_ID_PREFIX,
    NFAG_PIS_CST,
    NFAG_VERSION,
    nfag_schema,
)
from ..nfag_client.client import NfagClient

XML_DECLARATION = re.compile(r"^\s*<\?xml[^>]*\?>")


def filter_nfag(record):
    return (
        record.processador_edoc == PROCESSADOR_OCA
        and record.document_type_id.code == MODELO_FISCAL_NFAG
    )


def nfag_check_digit(key):
    """Modulo 11 (weights 2 to 9) check digit of the access key; the
    characters of an alphanumeric CNPJ count as their ASCII code minus 48
    (MOC NFAg 1.00l, Visão Geral, cálculo do dígito verificador)."""
    total = sum(
        (ord(char) - 48) * (2 + index % 8) for index, char in enumerate(reversed(key))
    )
    rest = total % 11
    return "0" if rest < 2 else str(11 - rest)


def _clean_text(text):
    return (
        normalize("NFKD", text)
        .encode("ASCII", "ignore")
        .decode("ASCII")
        .replace("\n", " ")
        .replace("\r", "")
        .strip()
    )


class NFAg(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document"
    _inherit = ["l10n_br_fiscal.document", "nfag.10.infnfag"]

    _nfag10_odoo_module = (
        "odoo.addons.l10n_br_nfag_spec.models.v1_0.nfag_tipos_basico_v1_00"
    )
    _nfag10_stacking_mixin = "nfag.10.infnfag"
    # ligacao, gFat and gAgencia are optional in the XSD only for the
    # aggregating NFAg (tpFat 5, NT 2026.004 v1.01), which is not supported
    _nfag10_stacking_force_paths = (
        "infnfag.ligacao",
        "infnfag.gFat",
        "infnfag.gAgencia",
        "infnfag.infAdic",
    )
    # IBSCBSTot is exported by the tag hooks below; gFatConjunto and gPIX
    # (not supported yet) would be stacked by the infnfag.gFat force path
    _nfag10_stacking_skip_paths = (
        "nfag10_IBSCBSTot",
        "nfag10_gFatConjunto",
        "nfag10_gPIX",
    )

    nfag_environment = fields.Selection(
        selection=NFAG_ENVIRONMENTS,
        string="NFAg Environment",
        copy=False,
        default=lambda self: self.env.company.nfag_environment,
    )

    ##########################
    # NFAg tag: infNFAg
    ##########################

    nfag10_versao = fields.Char(compute="_compute_nfag10_versao")

    nfag10_Id = fields.Char(compute="_compute_nfag10_Id")

    def _compute_nfag10_versao(self):
        self.nfag10_versao = NFAG_VERSION

    @api.depends("document_key")
    def _compute_nfag10_Id(self):
        # the XSD pattern and the MOC rule G09 take the literal NFAG, not the
        # NFAg prefix of the document type
        for record in self:
            record.nfag10_Id = (
                f"{NFAG_ID_PREFIX}{record.document_key}"
                if record.document_key
                else False
            )

    ##########################
    # NFAg tag: ide
    ##########################

    nfag10_cUF = fields.Selection(compute="_compute_nfag10_ide")
    nfag10_tpAmb = fields.Selection(related="nfag_environment")
    nfag10_mod = fields.Char(related="document_type_id.code")
    nfag10_serie = fields.Char(related="document_serie")
    nfag10_nNF = fields.Char(related="document_number")
    nfag10_cNF = fields.Char(related="key_random_code")
    nfag10_cDV = fields.Char(related="key_check_digit")
    nfag10_dhEmi = fields.Datetime(related="document_date")
    nfag10_tpEmis = fields.Selection(default="1")
    nfag10_nSiteAutoriz = fields.Char(default="0")
    nfag10_cMunFG = fields.Char(compute="_compute_nfag10_ide")
    nfag10_finNFAg = fields.Selection(default="0")
    nfag10_tpFat = fields.Selection(default="1")
    nfag10_verProc = fields.Char(
        copy=False,
        default=lambda self: self.env["ir.config_parameter"]
        .sudo()
        .get_param("l10n_br_nfag.version.name", default="Odoo Brasil OCA v18"),
    )

    @api.depends("company_id")
    def _compute_nfag10_ide(self):
        for record in self:
            record.nfag10_cUF = record.company_id.state_id.ibge_code
            record.nfag10_cMunFG = record.company_id.city_id.ibge_code

    ##########################
    # NFAg tags: emit, dest, gMed and det
    ##########################

    nfag10_emit = fields.Many2one(comodel_name="res.company", related="company_id")

    nfag10_dest = fields.Many2one(comodel_name="res.partner", related="partner_id")

    nfag10_gMed = fields.One2many(comodel_name="l10n_br_nfag.meter")

    nfag10_det = fields.One2many(
        comodel_name="l10n_br_fiscal.document.line",
        inverse_name="document_id",
        related="fiscal_line_ids",
    )

    ##########################
    # NFAg tag: gAgencia
    ##########################

    nfag10_gHistCons = fields.One2many(comodel_name="l10n_br_nfag.consumption.history")

    ##########################
    # NFAg tag: total
    ##########################

    nfag10_vProd = fields.Monetary(compute="_compute_nfag10_total")
    nfag10_vRetPIS = fields.Monetary(compute="_compute_nfag10_total")
    nfag10_vRetCofins = fields.Monetary(compute="_compute_nfag10_total")
    nfag10_vRetCSLL = fields.Monetary(compute="_compute_nfag10_total")
    nfag10_vIRRF = fields.Monetary(compute="_compute_nfag10_total")
    nfag10_vCOFINS = fields.Monetary(compute="_compute_nfag10_total")
    nfag10_vPIS = fields.Monetary(compute="_compute_nfag10_total")
    nfag10_vTFS = fields.Monetary(compute="_compute_nfag10_total")
    nfag10_vTFU = fields.Monetary(compute="_compute_nfag10_total")
    nfag10_vNF = fields.Monetary(compute="_compute_nfag10_total")
    nfag10_vTotDFe = fields.Monetary(compute="_compute_nfag10_total")

    def _nfag_sum(self, field_name):
        """Total of a line value with the sign of each item: the items with a
        deduction cClass subtract (MOC NFAg 1.00l, Anexo I, observação geral
        do grupo total, and Visão Geral, classificação de produtos)."""
        return sum(
            line._nfag_sign() * (line[field_name] or 0.0)
            for line in self.fiscal_line_ids
        )

    @api.depends(
        "document_date",
        "fiscal_line_ids.nfag10_vProd",
        "fiscal_line_ids.nfag10_cClass",
        "fiscal_line_ids.pis_value",
        "fiscal_line_ids.cofins_value",
        "fiscal_line_ids.pis_wh_value",
        "fiscal_line_ids.cofins_wh_value",
        "fiscal_line_ids.csll_wh_value",
        "fiscal_line_ids.irpj_wh_value",
        "fiscal_line_ids.ibs_value",
        "fiscal_line_ids.cbs_value",
    )
    def _compute_nfag10_total(self):
        for record in self:
            record.nfag10_vProd = record._nfag_sum("nfag10_vProd")
            record.nfag10_vRetPIS = record._nfag_sum("pis_wh_value")
            record.nfag10_vRetCofins = record._nfag_sum("cofins_wh_value")
            record.nfag10_vRetCSLL = record._nfag_sum("csll_wh_value")
            record.nfag10_vIRRF = record._nfag_sum("irpj_wh_value")
            record.nfag10_vPIS = record._nfag_sum("pis_value")
            record.nfag10_vCOFINS = record._nfag_sum("cofins_value")
            # the fiscal engine does not compute the TFS and TFU fees yet
            record.nfag10_vTFS = 0.0
            record.nfag10_vTFU = 0.0
            # MOC NFAg 1.00l, Anexo I, rule G177
            record.nfag10_vNF = (
                record.nfag10_vProd
                - record.nfag10_vRetPIS
                - record.nfag10_vRetCofins
                - record.nfag10_vRetCSLL
                - record.nfag10_vIRRF
            )
            # NT 2026.004 v1.01, item 4, rule 365: vNF in 2026, plus IBS and
            # CBS from 2027 on
            record.nfag10_vTotDFe = record.nfag10_vNF
            if record._nfag_issue_year() > 2026:
                record.nfag10_vTotDFe += record._nfag_sum(
                    "ibs_value"
                ) + record._nfag_sum("cbs_value")

    def _nfag_issue_year(self):
        self.ensure_one()
        issue_date = self.document_date or fields.Datetime.now()
        return fields.Datetime.context_timestamp(self, issue_date).year

    def _export_fields_nfag_10_total(self, xsd_fields, class_obj, export_dict):
        # the net values of NT 2026.004 (vItemLiq, vProdLiq) are not filled
        if "nfag10_vProdLiq" in xsd_fields:
            xsd_fields.remove("nfag10_vProdLiq")

    def _export_tag_nfag_10_ibscbstot(self, xsd_fields, class_obj, export_dict):
        export_dict["vBCIBSCBS"] = self._nfag_sum("ibs_base")

    def _export_tag_nfag_10_gibs(self, xsd_fields, class_obj, export_dict):
        # the municipal IBS is zero (rule G91 for 2026)
        export_dict["vIBS"] = self._nfag_sum("ibs_value")

    def _export_tag_nfag_10_gibsuf(self, xsd_fields, class_obj, export_dict):
        export_dict["vDif"] = 0.0
        export_dict["vDevTrib"] = 0.0
        export_dict["vIBSUF"] = self._nfag_sum("ibs_value")

    def _export_tag_nfag_10_gibsmun(self, xsd_fields, class_obj, export_dict):
        export_dict["vDif"] = 0.0
        export_dict["vDevTrib"] = 0.0
        export_dict["vIBSMun"] = 0.0

    def _export_tag_nfag_10_gcbs(self, xsd_fields, class_obj, export_dict):
        export_dict["vDif"] = 0.0
        export_dict["vDevTrib"] = 0.0
        export_dict["vCBS"] = self._nfag_sum("cbs_value")

    ##########################
    # NFAg tag: infAdic
    ##########################

    nfag10_infAdFisco = fields.Char(compute="_compute_nfag10_infAdic")

    nfag10_infCpl = fields.Char(compute="_compute_nfag10_infAdic")

    @api.depends("fiscal_additional_data", "customer_additional_data")
    def _compute_nfag10_infAdic(self):
        for record in self:
            record.nfag10_infAdFisco = " ".join(
                (record.fiscal_additional_data or "").split()
            )
            record.nfag10_infCpl = " ".join(
                (record.customer_additional_data or "").split()
            )

    def _export_fields_nfag_10_infadic(self, xsd_fields, class_obj, export_dict):
        # infCpl is a list of up to 5 texts in the XSD
        xsd_fields.remove("nfag10_infCpl")
        if self.nfag10_infCpl:
            export_dict["infCpl"] = [self.nfag10_infCpl]

    ################################
    # Framework Spec model's methods
    ################################

    def _export_fields_nfag_10_infnfag(self, xsd_fields, class_obj, export_dict):
        if not (self.nfag10_infAdFisco or self.nfag10_infCpl):
            xsd_fields.remove("nfag10_infAdic")

    def _export_fields_nfag_10_gfat(self, xsd_fields, class_obj, export_dict):
        if self.nfag10_codDebAuto:
            xsd_fields.remove("nfag10_codBanco")
            xsd_fields.remove("nfag10_codAgencia")

    def _export_one2many(self, field_name, class_obj=None):
        if field_name != "nfag10_det":
            return super()._export_one2many(field_name, class_obj)
        return [
            line._build_binding(class_name="nfag.10.det")
            for line in self.fiscal_line_ids
        ]

    ################################
    # Business Model Methods
    ################################

    def _nfag_qrcode(self):
        """MOC NFAg 1.00l, Visão Geral, item 9 (normal emission)."""
        self.ensure_one()
        return (
            f"{self.company_id.nfag_qrcode_url}?chNFAg={self.document_key}"
            f"&tpAmb={self.nfag_environment}"
        )

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filter_nfag):
            edocs.append(
                Nfag(
                    infNFAg=record._build_binding("nfag", "10"),
                    infNFAgSupl=Tnfag.InfNfagSupl(qrCodNFAg=record._nfag_qrcode()),
                )
            )
        return edocs

    def _nfag_sign(self, binding, doc_id):
        certificate = self.company_id._get_br_certificate()
        return binding.to_xml(
            pkcs12_data=certificate.with_context(bin_size=False).content,
            pkcs12_password=certificate.pkcs12_password,
            doc_id=doc_id,
        )

    def _nfag_event_environment(self):
        return EVENT_ENV_PROD if self.nfag_environment == "1" else EVENT_ENV_HML

    def _document_export(self, **kwargs):
        result = super()._document_export(**kwargs)
        for record in self.filtered(filter_nfag):
            edoc = record.serialize()[0]
            signed_xml = record._nfag_sign(edoc, edoc.infNFAg.Id)
            if (
                record.authorization_event_id
                and record.authorization_event_id.state == "draft"
            ):
                record.sudo().authorization_event_id.unlink()
            record.authorization_event_id = record.event_ids.create_event_save_xml(
                company_id=record.company_id,
                environment=record._nfag_event_environment(),
                event_type="0",
                xml_file=signed_xml,
                document_id=record,
            )
            record._validate_xml(signed_xml)
        return result

    def _validate_xml(self, xml_file):
        self.ensure_one()
        if not filter_nfag(self):
            return super()._validate_xml(xml_file)
        errors = Nfag.schema_validation(xml_file, nfag_schema("nfag"))
        self.write({"xml_error_message": "\n".join(errors) or False})

    def _generate_key(self):
        nfag = self.filtered(filter_nfag)
        result = super(NFAg, self - nfag)._generate_key()
        for record in nfag:
            # MOC NFAg 1.00l, Visão Geral, chave de acesso da NFAg
            date = fields.Datetime.context_timestamp(record, record.document_date)
            if not record.key_random_code:
                record.key_random_code = str(random.randint(0, 9999999)).zfill(7)
            key = "".join(
                (
                    record.company_id.state_id.ibge_code or "",
                    date.strftime("%y%m"),
                    re.sub(r"[^A-Z0-9]", "", (record.company_id.vat or "").upper()),
                    record.document_type_id.code,
                    (record.document_serie or "").zfill(3),
                    (record.document_number or "").zfill(9),
                    record.nfag10_tpEmis or "1",
                    record.nfag10_nSiteAutoriz or "0",
                    record.key_random_code,
                )
            )
            if len(key) != 43:
                raise ValidationError(
                    _(
                        "Cannot build the NFAg access key of %(document)s: check "
                        "the company CNPJ and state, the serie and the number.",
                        document=record.display_name,
                    )
                )
            record.key_check_digit = nfag_check_digit(key)
            record.document_key = key + record.key_check_digit
        return result

    def _document_number(self):
        if (
            filter_nfag(self)
            and self.issuer == DOCUMENT_ISSUER_COMPANY
            and not self.document_serie_id
        ):
            self.document_serie_id = self.document_type_id.get_document_serie(
                self.company_id, self.fiscal_operation_id
            )
        return super()._document_number()

    def _document_check(self):
        result = super()._document_check()
        for record in self.filtered(filter_nfag):
            record._check_nfag_required_fields()
        return result

    def _check_nfag_required_fields(self):
        self.ensure_one()
        missing = []

        def check(value, label):
            if not value:
                missing.append(label)

        company = self.company_id
        check(company.vat, _("Company CNPJ"))
        check(company.state_id, _("Company State"))
        check(company.city_id, _("Company City"))
        check(company.sudo().certificate, _("Digital Certificate"))
        check(self.partner_id, _("Customer"))
        check(self.partner_id.city_id, _("Customer City"))
        check(self.document_serie_id, _("Document Serie"))
        if self.nfag10_tpFat != "1" or self.nfag10_finNFAg != "0":
            missing.append(
                _("Only the normal NFAg (tpFat 1 and finNFAg 0) is supported yet")
            )
        if self.nfag10_tpEmis != "1":
            missing.append(_("The offline contingency is not supported yet"))
        for field_name in (
            # ligacao
            "nfag10_idLigacao",
            "nfag10_tpLigacao",
            "nfag10_latGPS",
            "nfag10_longGPS",
            # gFat: required for tpFat 1 (MOC NFAg 1.00l, Anexo I, rule G67)
            "nfag10_CompetFat",
            "nfag10_dVencFat",
            "nfag10_dProxLeitura",
            "nfag10_codBarras",
            # gAgencia: required for tpFat 1 (NT 2026.004 v1.01, rule 1068)
            "nfag10_nAgenciaAtend",
            "nfag10_enderAgenciaAtend",
        ):
            check(self[field_name], self._fields[field_name].string)
        # NFAg XSD: gFat takes codDebAuto or codBanco and codAgencia
        check(
            self.nfag10_codDebAuto or (self.nfag10_codBanco and self.nfag10_codAgencia),
            _("Automatic debit code or bank and branch of the invoice"),
        )
        # NFAg XSD: gAgencia needs 1 to 5 gHistCons with 1 to 13 gCons each
        if not 1 <= len(self.nfag10_gHistCons) <= 5 or any(
            not 1 <= len(history.nfag10_gCons) <= 13
            for history in self.nfag10_gHistCons
        ):
            missing.append(_("Consumption history (gHistCons) with 1 to 13 months"))
        check(self.fiscal_line_ids, _("Document Lines"))
        for line in self.fiscal_line_ids:
            label = line.name or line.product_id.display_name
            check(line.product_id.default_code, _("Product code of %s") % label)
            check(
                line.nfag10_cClass and re.fullmatch(r"[0-9]{7}", line.nfag10_cClass),
                _("Item classification code (7 digits) of %s") % label,
            )
            check(line.nfag10_uMed, _("Unit of measure of %s") % label)
            check(line.nfag10_indOrigemQtd, _("Origin of the quantity of %s") % label)
            # MOC NFAg 1.00l, Anexo I: the IBSCBS group of the item is 1-1
            check(
                line.ibs_cst_id and line.tax_classification_id,
                _("IBS/CBS tax situation and classification of %s") % label,
            )
            if line.pis_cst_id and line.pis_cst_id.code not in NFAG_PIS_CST:
                missing.append(_("PIS CST not accepted by the NFAg in %s") % label)
            if line.cofins_cst_id and line.cofins_cst_id.code not in NFAG_COFINS_CST:
                missing.append(_("COFINS CST not accepted by the NFAg in %s") % label)
        if missing:
            raise UserError(
                _("Fill in the required NFAg fields:\n- %s") % "\n- ".join(missing)
            )

    ################################
    # Transmission
    ################################

    def _get_nfag_client(self):
        self.ensure_one()
        certificate = self.company_id._get_br_certificate()
        return NfagClient(
            ambiente=self.nfag_environment,
            uf=self.company_id.state_id.ibge_code,
            pkcs12_data=certificate.with_context(bin_size=False).content,
            pkcs12_password=certificate.pkcs12_password,
        )

    def _eletronic_document_send(self):
        nfag_documents = self.filtered(filter_nfag)
        result = super(NFAg, self - nfag_documents)._eletronic_document_send()
        for record in nfag_documents:
            if record.xml_error_message:
                continue
            signed_xml = base64.b64decode(
                record.authorization_event_id.file_request_id.datas
            ).decode("utf-8")
            response = record._get_nfag_client().envia_nfag(signed_xml)
            record._nfag_process_response(response, signed_xml)
        return result

    def _nfag_process_response(self, response, signed_xml):
        """Answer of the synchronous NFAgRecepcao (retNFAg with protNFAg)."""
        self.ensure_one()
        status = response.cStat
        reason = response.xMotivo
        inf_prot = response.protNFAg and response.protNFAg.infProt
        if inf_prot:
            status = inf_prot.cStat
            reason = inf_prot.xMotivo
        self.write({"status_code": status, "status_name": reason})
        if status in NFAG_AUTHORIZED and inf_prot:
            self.authorization_event_id.set_done(
                status_code=status,
                response=reason,
                protocol_date=tax_authority_date_to_utc(inf_prot.dhRecbto),
                protocol_number=inf_prot.nProt,
                file_response_xml=self._nfag_proc_xml(signed_xml, response),
            )
            self._change_state(SITUACAO_EDOC_AUTORIZADA)
        else:
            self._change_state(SITUACAO_EDOC_REJEITADA)

    def _nfag_proc_xml(self, signed_xml, response):
        """nfagProc: the signed NFAg with the authorization protocol."""
        prot_xml = response.protNFAg.to_xml(ns_map={None: Nfag.Meta.namespace})
        prot_xml = XML_DECLARATION.sub("", prot_xml).strip()
        nfag_xml = XML_DECLARATION.sub("", signed_xml).strip()
        return (
            f'<nfagProc xmlns="{Nfag.Meta.namespace}" versao="{NFAG_VERSION}">'
            f"{nfag_xml}{prot_xml}</nfagProc>"
        )

    ################################
    # Cancellation event (110111)
    ################################

    def _nfag_cancel_event_xml(self, justification):
        """Signed XML of the cancellation event of the NFAg (MOC NFAg 1.00l,
        Visão Geral, evento de cancelamento)."""
        self.ensure_one()
        if not self.authorization_protocol:
            raise UserError(_("Authorization Protocol Not Found!"))
        event_date = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        event = EventoNfag(
            versao=NFAG_VERSION,
            infEvento=EventoNfag.InfEvento(
                cOrgao=TcorgaoIbge(self.company_id.state_id.ibge_code),
                tpAmb=Tamb(self.nfag_environment),
                CNPJ=punctuation_rm(self.company_id.vat),
                chNFAg=self.document_key,
                dhEvento=event_date.replace(microsecond=0).isoformat(),
                tpEvento=NFAG_CANCEL_EVENT,
                nSeqEvento=NFAG_EVENT_SEQUENCE,
                detEvento=EventoNfag.InfEvento.DetEvento(
                    versaoEvento=NFAG_VERSION,
                    any_element=EvCancNfag(
                        descEvento=EvCancNfagDescEvento.CANCELAMENTO,
                        nProt=self.authorization_protocol,
                        xJust=_clean_text(justification or ""),
                    ),
                ),
                Id=f"ID{NFAG_CANCEL_EVENT}{self.document_key}{NFAG_EVENT_SEQUENCE}",
            ),
        )
        signed_xml = self._nfag_sign(event, event.infEvento.Id)
        errors = EventoNfag.schema_validation(signed_xml, nfag_schema("eventoNFAg"))
        if errors:
            raise ValidationError("\n".join(errors))
        return signed_xml

    def _document_cancel(self, justificative=None):
        nfag_documents = self.filtered(filter_nfag)
        result = None
        if self - nfag_documents:
            result = super(NFAg, self - nfag_documents)._document_cancel(justificative)
        for record in nfag_documents:
            record.cancel_reason = justificative
            signed_xml = record._nfag_cancel_event_xml(justificative)
            event = record.event_ids.create_event_save_xml(
                company_id=record.company_id,
                environment=record._nfag_event_environment(),
                event_type="2",
                xml_file=signed_xml,
                document_id=record,
                sequence="1",
                justification=justificative,
            )
            record.cancel_event_id = event
            response = record._get_nfag_client().envia_evento(signed_xml).infEvento
            event.write({"status_code": response.cStat, "response": response.xMotivo})
            if response.cStat not in NFAG_EVENT_REGISTERED:
                # a refusal is reported, not raised, so the event is kept
                record.message_post(
                    body=_(
                        "NFAg cancellation refused: %(code)s - %(reason)s",
                        code=response.cStat,
                        reason=response.xMotivo,
                    )
                )
                continue
            event.set_done(
                status_code=response.cStat,
                response=response.xMotivo,
                protocol_date=tax_authority_date_to_utc(response.dhRegEvento),
                protocol_number=response.nProt,
                file_response_xml=False,
            )
            record.state_fiscal = SITUACAO_FISCAL_CANCELADO
            super(NFAg, record)._document_cancel(justificative)
        return result
