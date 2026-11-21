# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import random
import re
from importlib import import_module

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
from odoo.addons.l10n_br_nfgas_spec.bindings.v1_0.ev_canc_nfgas_v1_00 import (
    EvCancNfgas,
    EvCancNfgasDescEvento,
)
from odoo.addons.l10n_br_nfgas_spec.bindings.v1_0.evento_nfgas_tipos_basico_v1_00 import (  # noqa: E501
    Tevento,
)
from odoo.addons.l10n_br_nfgas_spec.bindings.v1_0.evento_nfgas_v1_00 import (
    EventoNfgas,
)
from odoo.addons.l10n_br_nfgas_spec.bindings.v1_0.nfgas_tipos_basico_v1_00 import (
    Tnfgas,
)
from odoo.addons.l10n_br_nfgas_spec.bindings.v1_0.nfgas_v1_00 import Nfgas
from odoo.addons.l10n_br_nfgas_spec.tools import schema_path
from odoo.addons.spec_driven_model.models import spec_models

from ..constants import (
    MODELO_FISCAL_NFGAS,
    NFGAS_AUTHORIZED,
    NFGAS_CANCEL_EVENT,
    NFGAS_CCLASS,
    NFGAS_CFOPS,
    NFGAS_ENVIRONMENTS,
    NFGAS_EVENT_REGISTERED,
    NFGAS_EVENT_VERSION,
    NFGAS_IBSCBS_IN_TOTAL_YEAR,
    NFGAS_MEASURED_ORIGINS,
    NFGAS_VERSION,
)
from ..nfgas_client.client import NfgasClient
from ..nfgas_client.servers import Endpoint, get_location

XML_DECLARATION = re.compile(r"^\s*<\?xml[^>]*\?>")


def filter_nfgas(record):
    return (
        record.processador_edoc == PROCESSADOR_OCA
        and record.document_type_id.code == MODELO_FISCAL_NFGAS
    )


def nfgas_check_digit(key):
    """Modulo 11 (weights 2 to 9) check digit of the access key; the
    characters of an alphanumeric CNPJ count as their ASCII code minus 48
    (MOC NFGas 1.00g, Visão Geral, cálculo do dígito verificador)."""
    total = sum(
        (ord(char) - 48) * (2 + index % 8) for index, char in enumerate(reversed(key))
    )
    rest = total % 11
    return "0" if rest < 2 else str(11 - rest)


class NFGas(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document"
    _inherit = ["l10n_br_fiscal.document", "nfgas.10.infnfgas"]

    _nfgas10_odoo_module = (
        "odoo.addons.l10n_br_nfgas_spec.models.v1_0.nfgas_tipos_basico_v1_00"
    )
    _nfgas10_stacking_mixin = "nfgas.10.infnfgas"
    # optional in the XSD, but required for the normal billing (tpFat 1):
    # instalacao (XSD annotation), gFat (rule G167) and gAgencia (rule G169)
    _nfgas10_stacking_force_paths = [
        "infnfgas.instalacao",
        "infnfgas.gFat",
        "infnfgas.gAgencia",
        "infnfgas.infAdic",
    ]
    # the force paths also match the children: PIX of the invoice is optional
    _nfgas10_stacking_skip_paths = ["nfgas10_gPIX"]

    nfgas_environment = fields.Selection(
        selection=NFGAS_ENVIRONMENTS,
        string="NFGas Environment",
        copy=False,
        default=lambda self: self.env.company.nfgas_environment,
    )

    ##########################
    # NFGas tag: infNFGas
    ##########################

    nfgas10_versao = fields.Char(compute="_compute_nfgas10_versao")

    nfgas10_Id = fields.Char(compute="_compute_nfgas10_Id")

    def _compute_nfgas10_versao(self):
        self.nfgas10_versao = NFGAS_VERSION

    @api.depends("document_type_id", "document_key")
    def _compute_nfgas10_Id(self):
        for record in self:
            record.nfgas10_Id = (
                f"{record.document_type_id.prefix}{record.document_key}"
                if record.document_key and record.document_type_id.prefix
                else False
            )

    ##########################
    # NFGas tag: ide
    ##########################

    nfgas10_cUF = fields.Selection(compute="_compute_nfgas10_ide")
    nfgas10_tpAmb = fields.Selection(related="nfgas_environment")
    nfgas10_mod = fields.Char(related="document_type_id.code")
    nfgas10_serie = fields.Char(related="document_serie")
    nfgas10_nNF = fields.Char(related="document_number")
    nfgas10_cNF = fields.Char(related="key_random_code")
    nfgas10_cDV = fields.Char(related="key_check_digit")
    nfgas10_dhEmi = fields.Datetime(related="document_date")
    nfgas10_tpEmis = fields.Selection(default="1")
    nfgas10_nSiteAutoriz = fields.Char(default="0")
    nfgas10_cMunFG = fields.Char(compute="_compute_nfgas10_ide")
    nfgas10_finNFGas = fields.Selection(default="0")
    nfgas10_tpFat = fields.Selection(default="1")
    nfgas10_verProc = fields.Char(
        copy=False,
        default=lambda self: self.env["ir.config_parameter"]
        .sudo()
        .get_param("l10n_br_nfgas.version.name", default="Odoo Brasil OCA v16"),
    )

    @api.depends("company_id")
    def _compute_nfgas10_ide(self):
        for record in self:
            record.nfgas10_cUF = record.company_id.state_id.ibge_code
            record.nfgas10_cMunFG = record.company_id.city_id.ibge_code

    ##########################
    # NFGas tags: emit and dest
    ##########################

    nfgas10_emit = fields.Many2one(comodel_name="res.company", related="company_id")

    nfgas10_dest = fields.Many2one(comodel_name="res.partner", related="partner_id")

    ##########################
    # NFGas tags: gMed and gAgencia
    ##########################

    nfgas10_gMed = fields.One2many(comodel_name="l10n_br_nfgas.meter")

    nfgas10_gHistCons = fields.One2many(
        comodel_name="l10n_br_nfgas.consumption.history"
    )

    ##########################
    # NFGas tag: total
    ##########################

    nfgas10_vProd = fields.Monetary(compute="_compute_nfgas10_total")
    nfgas10_vBC = fields.Monetary(related="amount_icms_base")
    nfgas10_vICMS = fields.Monetary(related="amount_icms_value")
    nfgas10_vICMSDeson = fields.Monetary(compute="_compute_nfgas10_total")
    nfgas10_vFCP = fields.Monetary(related="amount_icmsfcp_value")
    nfgas10_vBCST = fields.Monetary(related="amount_icmsst_base")
    nfgas10_vST = fields.Monetary(related="amount_icmsst_value")
    nfgas10_vFCPST = fields.Monetary(related="amount_icmsfcpst_value")
    nfgas10_vRetPIS = fields.Monetary(related="amount_pis_wh_value")
    nfgas10_vRetCofins = fields.Monetary(related="amount_cofins_wh_value")
    nfgas10_vRetCSLL = fields.Monetary(related="amount_csll_wh_value")
    nfgas10_vIRRF = fields.Monetary(related="amount_irpj_wh_value")
    nfgas10_vCOFINS = fields.Monetary(related="amount_cofins_value")
    nfgas10_vPIS = fields.Monetary(related="amount_pis_value")
    nfgas10_vTxReg = fields.Monetary(compute="_compute_nfgas10_total")
    nfgas10_vNF = fields.Monetary(compute="_compute_nfgas10_total")
    nfgas10_vTotDFe = fields.Monetary(compute="_compute_nfgas10_total")

    @api.depends(
        "document_date",
        "fiscal_line_ids.nfgas10_vProd",
        "fiscal_line_ids.ibs_value",
        "fiscal_line_ids.cbs_value",
        "amount_pis_wh_value",
        "amount_cofins_wh_value",
        "amount_csll_wh_value",
        "amount_irpj_wh_value",
    )
    def _compute_nfgas10_total(self):
        for record in self:
            lines = record.fiscal_line_ids
            record.nfgas10_vProd = sum(lines.mapped("nfgas10_vProd"))
            record.nfgas10_vICMSDeson = 0.0
            record.nfgas10_vTxReg = 0.0
            # MOC NFGas 1.00g, Anexo I, rule G150
            record.nfgas10_vNF = (
                record.nfgas10_vProd
                - record.amount_pis_wh_value
                - record.amount_cofins_wh_value
                - record.amount_csll_wh_value
                - record.amount_irpj_wh_value
            )
            # NT 2026.004 v1.01, item 4, rule 365: vNF in 2026, plus IBS and
            # CBS from 2027 on
            record.nfgas10_vTotDFe = record.nfgas10_vNF
            if record._nfgas_issue_year() >= NFGAS_IBSCBS_IN_TOTAL_YEAR:
                record.nfgas10_vTotDFe += sum(lines.mapped("ibs_value")) + sum(
                    lines.mapped("cbs_value")
                )

    def _nfgas_issue_year(self):
        self.ensure_one()
        issue_date = self.document_date or fields.Datetime.now()
        return fields.Datetime.context_timestamp(self, issue_date).year

    def _export_tag_nfgas_10_ibscbstot(self, xsd_fields, class_obj, export_dict):
        export_dict["vBCIBSCBS"] = sum(self.fiscal_line_ids.mapped("ibs_base"))

    def _export_tag_nfgas_10_gibs(self, xsd_fields, class_obj, export_dict):
        export_dict["vIBS"] = sum(self.fiscal_line_ids.mapped("ibs_value"))

    def _export_tag_nfgas_10_gibsuf(self, xsd_fields, class_obj, export_dict):
        export_dict["vDif"] = 0.0
        export_dict["vDevTrib"] = 0.0
        export_dict["vIBSUF"] = sum(self.fiscal_line_ids.mapped("ibs_value"))

    def _export_tag_nfgas_10_gibsmun(self, xsd_fields, class_obj, export_dict):
        export_dict["vDif"] = 0.0
        export_dict["vDevTrib"] = 0.0
        export_dict["vIBSMun"] = 0.0

    def _export_tag_nfgas_10_gcbs(self, xsd_fields, class_obj, export_dict):
        export_dict["vDif"] = 0.0
        export_dict["vDevTrib"] = 0.0
        export_dict["vCBS"] = sum(self.fiscal_line_ids.mapped("cbs_value"))

    ##########################
    # NFGas tag: infAdic
    ##########################

    nfgas10_infAdFisco = fields.Char(compute="_compute_nfgas10_infAdic")

    nfgas10_infCpl = fields.Char(compute="_compute_nfgas10_infAdic")

    @api.depends("fiscal_additional_data", "customer_additional_data")
    def _compute_nfgas10_infAdic(self):
        for record in self:
            record.nfgas10_infAdFisco = " ".join(
                (record.fiscal_additional_data or "").split()
            )
            record.nfgas10_infCpl = " ".join(
                (record.customer_additional_data or "").split()
            )

    ################################
    # Framework Spec model's methods
    ################################

    def _register_hook(self):
        res = super()._register_hook()
        # the hook only runs for the schema of the last module stacked here
        for schema, version in self._nfgas_stacked_schemas():
            self.with_context(
                spec_schema=schema, spec_version=version
            )._register_remaining_schema_models_hook()
        return res

    @classmethod
    def _nfgas_stacked_schemas(cls):
        schemas = []
        for ancestor in cls.mro():
            if not ancestor.__module__.startswith("odoo.addons."):
                continue
            package = import_module(ancestor.__module__.rsplit(".", 1)[0])
            schema = getattr(package, "spec_schema", None)
            if schema and (schema, package.spec_version) not in schemas:
                schemas.append((schema, package.spec_version))
        return schemas

    def _export_fields_nfgas_10_infnfgas(self, xsd_fields, class_obj, export_dict):
        if not (self.nfgas10_infAdFisco or self.nfgas10_infCpl):
            xsd_fields.remove("nfgas10_infAdic")

    def _export_fields_nfgas_10_infadic(self, xsd_fields, class_obj, export_dict):
        # infCpl is a list (0-5) in the XSD
        xsd_fields.remove("nfgas10_infCpl")
        if self.nfgas10_infCpl:
            export_dict["infCpl"] = [self.nfgas10_infCpl]

    def _export_fields_nfgas_10_gfat(self, xsd_fields, class_obj, export_dict):
        if self.nfgas10_codDebAuto:
            xsd_fields.remove("nfgas10_codBanco")
            xsd_fields.remove("nfgas10_codAgencia")

    def _export_one2many(self, field_name, class_obj=None):
        if field_name != "nfgas10_det":
            return super()._export_one2many(field_name, class_obj)
        return [
            line._build_binding(class_name="nfgas.10.det")
            for line in self.fiscal_line_ids
        ]

    ################################
    # Business Model Methods
    ################################

    def _nfgas_qrcode(self):
        """MOC NFGas 1.00g, Visão Geral, item 9 (normal emission)."""
        self.ensure_one()
        url = get_location(self.nfgas_environment, Endpoint.QRCODE)
        return f"{url}?chNFGas={self.document_key}&tpAmb={self.nfgas_environment}"

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filter_nfgas):
            edocs.append(
                Nfgas(
                    infNFGas=record._build_binding("nfgas", "10"),
                    infNFGasSupl=Tnfgas.InfNfgasSupl(qrCodNFGas=record._nfgas_qrcode()),
                )
            )
        return edocs

    def _nfgas_sign(self, binding, doc_id):
        certificate = self.company_id.sudo().certificate
        return binding.to_xml(
            pkcs12_data=certificate.with_context(bin_size=False).file,
            pkcs12_password=certificate.password,
            doc_id=doc_id,
        )

    def _nfgas_event_environment(self):
        return EVENT_ENV_PROD if self.nfgas_environment == "1" else EVENT_ENV_HML

    def _document_export(self, **kwargs):
        result = super()._document_export(**kwargs)
        for record in self.filtered(filter_nfgas):
            edoc = record.serialize()[0]
            signed_xml = record._nfgas_sign(edoc, edoc.infNFGas.Id)
            if (
                record.authorization_event_id
                and record.authorization_event_id.state == "draft"
            ):
                record.sudo().authorization_event_id.unlink()
            record.authorization_event_id = record.event_ids.create_event_save_xml(
                company_id=record.company_id,
                environment=record._nfgas_event_environment(),
                event_type="0",
                xml_file=signed_xml,
                document_id=record,
            )
            record._validate_xml(signed_xml)
        return result

    def _validate_xml(self, xml_file):
        self.ensure_one()
        if not filter_nfgas(self):
            return super()._validate_xml(xml_file)
        errors = Nfgas.schema_validation(xml_file, schema_path())
        self.write({"xml_error_message": "\n".join(errors) or False})

    def _generate_key(self):
        nfgas = self.filtered(filter_nfgas)
        result = super(NFGas, self - nfgas)._generate_key()
        for record in nfgas:
            # MOC NFGas 1.00g, Visão Geral, access key
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
                    record.nfgas10_tpEmis or "1",
                    record.nfgas10_nSiteAutoriz or "0",
                    record.key_random_code,
                )
            )
            if len(key) != 43:
                raise ValidationError(
                    _(
                        "Cannot build the NFGas access key of %(document)s: check "
                        "the company CNPJ and state, the serie and the number.",
                        document=record.display_name,
                    )
                )
            record.key_check_digit = nfgas_check_digit(key)
            record.document_key = key + record.key_check_digit
        return result

    def _document_number(self):
        if (
            filter_nfgas(self)
            and self.issuer == DOCUMENT_ISSUER_COMPANY
            and not self.document_serie_id
        ):
            self.document_serie_id = self.document_type_id.get_document_serie(
                self.company_id, self.fiscal_operation_id
            )
        return super()._document_number()

    def _document_check(self):
        result = super()._document_check()
        for record in self.filtered(filter_nfgas):
            record._check_nfgas_required_fields()
        return result

    def _check_nfgas_required_fields(self):
        self.ensure_one()
        missing = []

        def check(value, label):
            if not value:
                missing.append(label)

        company = self.company_id
        check(company.vat, _("Company CNPJ"))
        check(company.state_id, _("Company State"))
        check(company.city_id, _("Company City"))
        check(company.nfgas10_IE, _("Company State Tax Number"))
        check(
            company.sudo().certificate_nfe_id or company.sudo().certificate_ecnpj_id,
            _("Digital Certificate"),
        )
        check(self.partner_id, _("Customer"))
        check(self.document_serie_id, _("Document Serie"))
        if self.nfgas10_tpFat != "1" or self.nfgas10_finNFGas != "0":
            missing.append(_("Only the normal NFGas with normal billing is supported"))
        for field_name in (
            "nfgas10_idInstalacao",
            "nfgas10_tpInstalacao",
            "nfgas10_tpClasse",
            "nfgas10_CompetFat",
            "nfgas10_dVencFat",
            "nfgas10_dProxLeitura",
            "nfgas10_codBarras",
        ):
            check(self[field_name], self._fields[field_name].string)
        # gFat takes codDebAuto or codBanco and codAgencia (XSD choice)
        check(
            self.nfgas10_codDebAuto
            or (self.nfgas10_codBanco and self.nfgas10_codAgencia),
            _("Automatic debit code or bank and branch of the invoice"),
        )
        # gAgencia/gHistCons: 1 to 5 histories with 1 to 13 months (XSD)
        histories = self.nfgas10_gHistCons
        if not 1 <= len(histories) <= 5 or any(
            not 1 <= len(history.nfgas10_gCons) <= 13 for history in histories
        ):
            missing.append(_("Consumption history (1 to 5, with 1 to 13 months)"))
        check(self.fiscal_line_ids, _("Document Lines"))
        cclass_codes = dict(NFGAS_CCLASS)
        for line in self.fiscal_line_ids:
            label = line.name or line.product_id.display_name
            # rule G57 (table of the NFGas portal)
            if line.nfgas10_cClass not in cclass_codes:
                missing.append(_("Item classification code (cClass) of %s") % label)
            if line.nfgas10_indDevolucao:
                missing.append(_("Returned items are not supported yet: %s") % label)
            # rules G66 and G66a (MOC NFGas 1.00g, Anexo I, item 2.5)
            if line.cfop_id.code not in NFGAS_CFOPS:
                missing.append(_("CFOP allowed in the NFGas for %s") % label)
            if not line._nfgas_icms_group():
                missing.append(
                    _("Supported ICMS CST (00, 20, 40, 41 or 90) of %s") % label
                )
            # the IBSCBS group is mandatory in the item (1-1 in the XSD)
            check(line.ibs_cst_id, _("IBS/CBS CST of %s") % label)
            check(line.tax_classification_id, _("IBS/CBS cClassTrib of %s") % label)
            check(line.nfgas10_uMed, _("Unit of measure of %s") % label)
            check(line.nfgas10_indOrigemQtd, _("Origin of the quantity of %s") % label)
            if line.nfgas10_indOrigemQtd in NFGAS_MEASURED_ORIGINS:
                check(line.nfgas_meter_id, _("Meter of %s") % label)
        if missing:
            raise UserError(
                _("Fill in the required NFGas fields:\n- %s") % "\n- ".join(missing)
            )

    ################################
    # Transmission (MOC NFGas 1.00g, Visão Geral, items 4 and 5)
    ################################

    def _get_nfgas_client(self):
        self.ensure_one()
        certificate = self.company_id.sudo().certificate
        return NfgasClient(
            ambiente=self.nfgas_environment,
            uf=self.company_id.state_id.ibge_code,
            pkcs12_data=certificate.with_context(bin_size=False).file,
            pkcs12_password=certificate.password,
        )

    def _eletronic_document_send(self):
        nfgas_documents = self.filtered(filter_nfgas)
        result = super(NFGas, self - nfgas_documents)._eletronic_document_send()
        for record in nfgas_documents:
            if record.xml_error_message:
                continue
            signed_xml = base64.b64decode(
                record.authorization_event_id.file_request_id.datas
            ).decode("utf-8")
            response = record._get_nfgas_client().envia_nfgas(signed_xml)
            record._nfgas_process_response(response, signed_xml)
        return result

    def _nfgas_process_response(self, response, signed_xml):
        """Authorization answer of the synchronous NFGasRecepcao."""
        self.ensure_one()
        status = response.cStat
        reason = response.xMotivo
        inf_prot = response.protNFGas and response.protNFGas.infProt
        if inf_prot:
            status = inf_prot.cStat
            reason = inf_prot.xMotivo
        self.write({"status_code": status, "status_name": reason})
        if status in NFGAS_AUTHORIZED and inf_prot:
            self.authorization_event_id.set_done(
                status_code=status,
                response=reason,
                protocol_date=tax_authority_date_to_utc(inf_prot.dhRecbto),
                protocol_number=inf_prot.nProt,
                file_response_xml=self._nfgas_proc_xml(signed_xml, response),
            )
            self._change_state(SITUACAO_EDOC_AUTORIZADA)
        else:
            self._change_state(SITUACAO_EDOC_REJEITADA)

    def _nfgas_proc_xml(self, signed_xml, response):
        """nfgasProc: the signed NFGas with the authorization protocol."""
        namespace = Nfgas.Meta.namespace
        prot_xml = response.protNFGas.to_xml(ns_map={None: namespace})
        prot_xml = XML_DECLARATION.sub("", prot_xml).strip()
        nfgas_xml = XML_DECLARATION.sub("", signed_xml).strip()
        return (
            f'<nfgasProc xmlns="{namespace}" versao="{NFGAS_VERSION}">'
            f"{nfgas_xml}{prot_xml}</nfgasProc>"
        )

    def _nfgas_cancel_event_xml(self, justification):
        """Signed XML of the cancellation event (110111, MOC NFGas 1.00g,
        Visão Geral, items 5 and 6)."""
        self.ensure_one()
        if not self.authorization_protocol:
            raise UserError(_("Authorization Protocol Not Found!"))
        sequence = "001"
        event_date = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        event = EventoNfgas(
            versao=NFGAS_EVENT_VERSION,
            infEvento=Tevento.InfEvento(
                cOrgao=self.company_id.state_id.ibge_code,
                tpAmb=self.nfgas_environment,
                CNPJ=punctuation_rm(self.company_id.vat),
                chNFGas=self.document_key,
                dhEvento=event_date.replace(microsecond=0).isoformat(),
                tpEvento=NFGAS_CANCEL_EVENT,
                nSeqEvento=sequence,
                detEvento=Tevento.InfEvento.DetEvento(
                    versaoEvento=NFGAS_EVENT_VERSION,
                    any_element=EvCancNfgas(
                        descEvento=EvCancNfgasDescEvento.CANCELAMENTO,
                        nProt=self.authorization_protocol,
                        xJust=" ".join((justification or "").split()),
                    ),
                ),
                Id=f"ID{NFGAS_CANCEL_EVENT}{self.document_key}{sequence}",
            ),
        )
        signed_xml = self._nfgas_sign(event, event.infEvento.Id)
        errors = EventoNfgas.schema_validation(
            signed_xml, schema_path("eventoNFGas_v1.00.xsd")
        )
        if errors:
            raise ValidationError("\n".join(errors))
        return signed_xml

    def _document_cancel(self, justificative):
        nfgas_documents = self.filtered(filter_nfgas)
        result = None
        if self - nfgas_documents:
            result = super(NFGas, self - nfgas_documents)._document_cancel(
                justificative
            )
        for record in nfgas_documents:
            record.cancel_reason = justificative
            signed_xml = record._nfgas_cancel_event_xml(justificative)
            event = record.event_ids.create_event_save_xml(
                company_id=record.company_id,
                environment=record._nfgas_event_environment(),
                event_type="2",
                xml_file=signed_xml,
                document_id=record,
                sequence="1",
                justification=justificative,
            )
            record.cancel_event_id = event
            response = record._get_nfgas_client().envia_evento(signed_xml).infEvento
            event.write({"status_code": response.cStat, "response": response.xMotivo})
            if response.cStat not in NFGAS_EVENT_REGISTERED:
                # a refusal keeps the document authorized and the event recorded
                record.message_post(
                    body=_(
                        "NFGas cancellation refused: %(code)s - %(reason)s",
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
            super(NFGas, record)._document_cancel(justificative)
        return result
