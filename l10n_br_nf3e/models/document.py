# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import random
import re

from erpbrasil.base.misc import punctuation_rm
from nfelib.nf3e.bindings.v1_0.ev_canc_nf3e_v1_00 import (
    EvCancNf3E,
    EvCancNf3EDescEvento,
)
from nfelib.nf3e.bindings.v1_0.evento_nf3e_tipos_basico_v1_00 import Tevento
from nfelib.nf3e.bindings.v1_0.evento_nf3e_v1_00 import EventoNf3E
from nfelib.nf3e.bindings.v1_0.nf3e_tipos_basico_v1_00 import Tnf3E
from nfelib.nf3e.bindings.v1_0.nf3e_v1_00 import Nf3E

from odoo import _, api, fields
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    PROCESSADOR_OCA,
)
from odoo.addons.spec_driven_model.models import spec_models

from ..constants.nf3e import (
    MODELO_FISCAL_NF3E,
    NF3E_CANCEL_EVENT,
    NF3E_ENVIRONMENTS,
    NF3E_EVENT_VERSION,
    NF3E_VERSION,
)


def filter_nf3e(record):
    return (
        record.processador_edoc == PROCESSADOR_OCA
        and record.document_type_id.code == MODELO_FISCAL_NF3E
    )


def nf3e_check_digit(key):
    """Modulo 11 (weights 2 to 9) check digit of the access key; the
    characters of an alphanumeric CNPJ count as their ASCII code minus 48."""
    total = sum(
        (ord(char) - 48) * (2 + index % 8) for index, char in enumerate(reversed(key))
    )
    rest = total % 11
    return "0" if rest < 2 else str(11 - rest)


class NF3e(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document"
    _inherit = ["l10n_br_fiscal.document", "nf3e.10.infnf3e"]

    _nf3e10_odoo_module = (
        "odoo.addons.l10n_br_nf3e_spec.models.v1_0.nf3e_tipos_basico_v1_00"
    )
    _nf3e10_stacking_mixin = "nf3e.10.infnf3e"
    _nf3e10_stacking_force_paths = ["infnf3e.infAdic"]

    nf3e_environment = fields.Selection(
        selection=NF3E_ENVIRONMENTS,
        string="NF3e Environment",
        copy=False,
        default=lambda self: self.env.company.nf3e_environment,
    )

    ##########################
    # NF3e tag: infNF3e
    ##########################

    nf3e10_versao = fields.Char(compute="_compute_nf3e10_versao")

    nf3e10_Id = fields.Char(compute="_compute_nf3e10_Id")

    def _compute_nf3e10_versao(self):
        self.nf3e10_versao = NF3E_VERSION

    @api.depends("document_type_id", "document_key")
    def _compute_nf3e10_Id(self):
        for record in self:
            record.nf3e10_Id = (
                f"{record.document_type_id.prefix}{record.document_key}"
                if record.document_key and record.document_type_id.prefix
                else False
            )

    ##########################
    # NF3e tag: ide
    ##########################

    nf3e10_cUF = fields.Selection(compute="_compute_nf3e10_ide")
    nf3e10_tpAmb = fields.Selection(related="nf3e_environment")
    nf3e10_mod = fields.Char(related="document_type_id.code")
    nf3e10_serie = fields.Char(related="document_serie")
    nf3e10_nNF = fields.Char(related="document_number")
    nf3e10_cNF = fields.Char(related="key_random_code")
    nf3e10_cDV = fields.Char(related="key_check_digit")
    nf3e10_dhEmi = fields.Datetime(related="document_date")
    nf3e10_tpEmis = fields.Selection(default="1")
    nf3e10_nSiteAutoriz = fields.Char(default="0")
    nf3e10_cMunFG = fields.Char(compute="_compute_nf3e10_ide")
    nf3e10_finNF3e = fields.Selection(default="1")
    nf3e10_verProc = fields.Char(
        copy=False,
        default=lambda self: self.env["ir.config_parameter"]
        .sudo()
        .get_param("l10n_br_nf3e.version.name", default="Odoo Brasil OCA v18"),
    )

    @api.depends("company_id")
    def _compute_nf3e10_ide(self):
        for record in self:
            record.nf3e10_cUF = record.company_id.state_id.ibge_code
            record.nf3e10_cMunFG = record.company_id.city_id.ibge_code

    ##########################
    # NF3e tags: emit and dest
    ##########################

    nf3e10_emit = fields.Many2one(comodel_name="res.company", related="company_id")

    nf3e10_dest = fields.Many2one(comodel_name="res.partner", related="partner_id")

    ##########################
    # NF3e tags: gMed and gANEEL
    ##########################

    nf3e10_gMed = fields.One2many(comodel_name="l10n_br_nf3e.meter")

    nf3e10_gHistFat = fields.One2many(comodel_name="l10n_br_nf3e.billing.history")

    ##########################
    # NF3e tag: total
    ##########################

    nf3e10_vProd = fields.Monetary(compute="_compute_nf3e10_total")
    nf3e10_vBC = fields.Monetary(related="amount_icms_base")
    nf3e10_vICMS = fields.Monetary(related="amount_icms_value")
    nf3e10_vICMSDeson = fields.Monetary(compute="_compute_nf3e10_total")
    nf3e10_vFCP = fields.Monetary(related="amount_icmsfcp_value")
    nf3e10_vBCST = fields.Monetary(related="amount_icmsst_base")
    nf3e10_vST = fields.Monetary(related="amount_icmsst_value")
    nf3e10_vFCPST = fields.Monetary(related="amount_icmsfcpst_value")
    nf3e10_vRetPIS = fields.Monetary(related="amount_pis_wh_value")
    nf3e10_vRetCofins = fields.Monetary(related="amount_cofins_wh_value")
    nf3e10_vRetCSLL = fields.Monetary(related="amount_csll_wh_value")
    nf3e10_vIRRF = fields.Monetary(related="amount_irpj_wh_value")
    nf3e10_vCOFINS = fields.Monetary(related="amount_cofins_value")
    nf3e10_vCOFINSEfet = fields.Monetary(compute="_compute_nf3e10_total")
    nf3e10_vPIS = fields.Monetary(related="amount_pis_value")
    nf3e10_vPISEfet = fields.Monetary(compute="_compute_nf3e10_total")
    nf3e10_vNF = fields.Monetary(compute="_compute_nf3e10_total")
    nf3e10_vTotDFe = fields.Monetary(compute="_compute_nf3e10_total")

    @api.depends(
        "document_date",
        "fiscal_line_ids.nf3e10_vProd",
        "fiscal_line_ids.ibs_value",
        "fiscal_line_ids.cbs_value",
        "fiscal_line_ids.ibs_cst_id",
        "amount_pis_wh_value",
        "amount_cofins_wh_value",
        "amount_csll_wh_value",
        "amount_irpj_wh_value",
    )
    def _compute_nf3e10_total(self):
        for record in self:
            lines = record.fiscal_line_ids
            record.nf3e10_vProd = sum(lines.mapped("nf3e10_vProd"))
            record.nf3e10_vICMSDeson = 0.0
            record.nf3e10_vCOFINSEfet = 0.0
            record.nf3e10_vPISEfet = 0.0
            # MOC NF3e 1.00a, rule G157
            record.nf3e10_vNF = (
                record.nf3e10_vProd
                - record.amount_pis_wh_value
                - record.amount_cofins_wh_value
                - record.amount_csll_wh_value
                - record.amount_irpj_wh_value
            )
            record.nf3e10_vTotDFe = False
            if lines.filtered("ibs_cst_id"):
                # NT 2025.001 RTC v1.14a, item 9, rules 360 and 365
                record.nf3e10_vTotDFe = record.nf3e10_vNF
                if record._nf3e_issue_year() > 2026:
                    record.nf3e10_vTotDFe += sum(lines.mapped("ibs_value")) + sum(
                        lines.mapped("cbs_value")
                    )

    def _nf3e_issue_year(self):
        self.ensure_one()
        issue_date = self.document_date or fields.Datetime.now()
        return fields.Datetime.context_timestamp(self, issue_date).year

    def _nf3e_ibscbs_lines(self):
        return self.fiscal_line_ids.filtered("ibs_cst_id")

    def _export_tag_nf3e_10_ibscbstot(self, xsd_fields, class_obj, export_dict):
        lines = self._nf3e_ibscbs_lines()
        if lines:
            export_dict["vBCIBSCBS"] = sum(lines.mapped("ibs_base"))

    def _export_tag_nf3e_10_gibs(self, xsd_fields, class_obj, export_dict):
        export_dict["vIBS"] = sum(self._nf3e_ibscbs_lines().mapped("ibs_value"))

    def _export_tag_nf3e_10_gibsuf(self, xsd_fields, class_obj, export_dict):
        export_dict["vDif"] = 0.0
        export_dict["vDevTrib"] = 0.0
        export_dict["vIBSUF"] = sum(self._nf3e_ibscbs_lines().mapped("ibs_value"))

    def _export_tag_nf3e_10_gibsmun(self, xsd_fields, class_obj, export_dict):
        export_dict["vDif"] = 0.0
        export_dict["vDevTrib"] = 0.0
        export_dict["vIBSMun"] = 0.0

    def _export_tag_nf3e_10_gcbs(self, xsd_fields, class_obj, export_dict):
        export_dict["vDif"] = 0.0
        export_dict["vDevTrib"] = 0.0
        export_dict["vCBS"] = sum(self._nf3e_ibscbs_lines().mapped("cbs_value"))

    ##########################
    # NF3e tag: infAdic
    ##########################

    nf3e10_infAdFisco = fields.Char(compute="_compute_nf3e10_infAdic")

    nf3e10_infCpl = fields.Char(compute="_compute_nf3e10_infAdic")

    @api.depends("fiscal_additional_data", "customer_additional_data")
    def _compute_nf3e10_infAdic(self):
        for record in self:
            record.nf3e10_infAdFisco = " ".join(
                (record.fiscal_additional_data or "").split()
            )
            record.nf3e10_infCpl = " ".join(
                (record.customer_additional_data or "").split()
            )

    ################################
    # Framework Spec model's methods
    ################################

    def _export_fields_nf3e_10_infnf3e(self, xsd_fields, class_obj, export_dict):
        if not (self.nf3e10_infAdFisco or self.nf3e10_infCpl):
            xsd_fields.remove("nf3e10_infAdic")

    def _export_fields_nf3e_10_gfat(self, xsd_fields, class_obj, export_dict):
        if self.nf3e10_codDebAuto:
            xsd_fields.remove("nf3e10_codBanco")
            xsd_fields.remove("nf3e10_codAgencia")

    def _export_one2many(self, field_name, class_obj=None):
        if field_name != "nf3e10_NFdet":
            return super()._export_one2many(field_name, class_obj)
        # a single NFdet group with one det per document line
        return [
            Tnf3E.InfNf3E.Nfdet(
                det=[
                    line._build_binding(class_name="nf3e.10.det")
                    for line in self.fiscal_line_ids
                ]
            )
        ]

    ################################
    # Business Model Methods
    ################################

    def _nf3e_qrcode(self):
        """MOC NF3e 1.00a, Visão Geral, item 9.2 (normal emission)."""
        self.ensure_one()
        return (
            f"{self.company_id.nf3e_qrcode_url}?chNF3e={self.document_key}"
            f"&tpAmb={self.nf3e_environment}"
        )

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filter_nf3e):
            edocs.append(
                Nf3E(
                    infNF3e=record._build_binding("nf3e", "10"),
                    infNF3eSupl=Tnf3E.InfNf3ESupl(qrCodNF3e=record._nf3e_qrcode()),
                )
            )
        return edocs

    def _nf3e_sign(self, binding, doc_id):
        certificate = self.company_id._get_br_certificate()
        return binding.to_xml(
            pkcs12_data=certificate.with_context(bin_size=False).content,
            pkcs12_password=certificate.pkcs12_password,
            doc_id=doc_id,
        )

    def _nf3e_event_environment(self):
        return EVENT_ENV_PROD if self.nf3e_environment == "1" else EVENT_ENV_HML

    def _document_export(self, **kwargs):
        result = super()._document_export(**kwargs)
        for record in self.filtered(filter_nf3e):
            edoc = record.serialize()[0]
            signed_xml = record._nf3e_sign(edoc, edoc.infNF3e.Id)
            if (
                record.authorization_event_id
                and record.authorization_event_id.state == "draft"
            ):
                record.sudo().authorization_event_id.unlink()
            record.authorization_event_id = record.event_ids.create_event_save_xml(
                company_id=record.company_id,
                environment=record._nf3e_event_environment(),
                event_type="0",
                xml_file=signed_xml,
                document_id=record,
            )
            record._validate_xml(signed_xml)
        return result

    def _validate_xml(self, xml_file):
        self.ensure_one()
        if not filter_nf3e(self):
            return super()._validate_xml(xml_file)
        errors = Nf3E.schema_validation(xml_file)
        self.write({"xml_error_message": "\n".join(errors) or False})

    def _generate_key(self):
        nf3e = self.filtered(filter_nf3e)
        result = super(NF3e, self - nf3e)._generate_key()
        for record in nf3e:
            # MOC NF3e 1.00a, Visão Geral, item 2.1 (chave de acesso)
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
                    record.nf3e10_tpEmis or "1",
                    record.nf3e10_nSiteAutoriz or "0",
                    record.key_random_code,
                )
            )
            if len(key) != 43:
                raise ValidationError(
                    _(
                        "Cannot build the NF3e access key of %(document)s: check "
                        "the company CNPJ and state, the serie and the number.",
                        document=record.display_name,
                    )
                )
            record.key_check_digit = nf3e_check_digit(key)
            record.document_key = key + record.key_check_digit
        return result

    def _document_number(self):
        if (
            filter_nf3e(self)
            and self.issuer == DOCUMENT_ISSUER_COMPANY
            and not self.document_serie_id
        ):
            self.document_serie_id = self.document_type_id.get_document_serie(
                self.company_id, self.fiscal_operation_id
            )
        return super()._document_number()

    def _document_check(self):
        result = super()._document_check()
        for record in self.filtered(filter_nf3e):
            record._check_nf3e_required_fields()
        return result

    def _check_nf3e_required_fields(self):
        self.ensure_one()
        missing = []

        def check(value, label):
            if not value:
                missing.append(label)

        company = self.company_id
        check(company.vat, _("Company CNPJ"))
        check(company.state_id, _("Company State"))
        check(company.city_id, _("Company City"))
        check(company.nf3e10_IE, _("Company State Tax Number"))
        check(company.sudo().certificate, _("Digital Certificate"))
        check(self.partner_id, _("Customer"))
        check(self.document_serie_id, _("Document Serie"))
        for field_name in (
            "nf3e10_idAcesso",
            "nf3e10_tpAcesso",
            "nf3e10_tpFase",
            "nf3e10_tpGrpTensao",
            "nf3e10_tpModTar",
            "nf3e10_latGPS",
            "nf3e10_longGPS",
            "nf3e10_CompetFat",
            "nf3e10_dVencFat",
            "nf3e10_dProxLeitura",
            "nf3e10_codBarras",
        ):
            check(self[field_name], self._fields[field_name].string)
        # nfelib NF3e XSD: gFat takes codDebAuto or codBanco and codAgencia
        check(
            self.nf3e10_codDebAuto or (self.nf3e10_codBanco and self.nf3e10_codAgencia),
            _("Automatic debit code or bank and branch of the invoice"),
        )
        check(self.fiscal_line_ids, _("Document Lines"))
        # nfelib NF3e XSD: gANEEL needs 1 to 5 gHistFat with 13 gGrandFat each
        if not self.nf3e10_gHistFat or any(
            len(history.nf3e10_gGrandFat) != 13 for history in self.nf3e10_gHistFat
        ):
            missing.append(_("Billing history with the 13 months (gHistFat)"))
        for line in self.fiscal_line_ids:
            label = line.name or line.product_id.display_name
            check(line.nf3e10_cClass, _("Item classification code of %s") % label)
            check(line.nf3e10_uMed, _("Unit of measure of %s") % label)
            check(line.cfop_id, _("CFOP of %s") % label)
            check(line.nf3e10_indOrigemQtd, _("Origin of the quantity of %s") % label)
            if line.nf3e10_indOrigemQtd == "3":
                # MOC NF3e 1.00a, rule G116 needs the gMedicao group
                missing.append(
                    _("The contracted quantity origin of %s is not supported yet")
                    % label
                )
        if missing:
            raise UserError(
                _("Fill in the required NF3e fields:\n- %s") % "\n- ".join(missing)
            )

    def _eletronic_document_send(self):
        if self.filtered(filter_nf3e):
            raise UserError(
                _(
                    "The NF3e transmission to the tax authority is not available "
                    "yet. Use the signed XML of the document authorization event."
                )
            )
        return super()._eletronic_document_send()

    def _document_cancel(self, justificative):
        if self.filtered(filter_nf3e):
            raise UserError(
                _(
                    "The NF3e transmission to the tax authority is not available "
                    "yet, so the NF3e cannot be cancelled from Odoo."
                )
            )
        return super()._document_cancel(justificative)

    def _nf3e_cancel_event_xml(self, justification):
        """Signed XML of the cancellation event (110111) of the NF3e."""
        self.ensure_one()
        sequence = "001"
        event_date = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        event = EventoNf3E(
            versao=NF3E_EVENT_VERSION,
            infEvento=Tevento.InfEvento(
                cOrgao=self.company_id.state_id.ibge_code,
                tpAmb=self.nf3e_environment,
                CNPJ=punctuation_rm(self.company_id.vat),
                chNF3e=self.document_key,
                dhEvento=event_date.replace(microsecond=0).isoformat(),
                tpEvento=NF3E_CANCEL_EVENT,
                nSeqEvento=sequence,
                detEvento=Tevento.InfEvento.DetEvento(
                    versaoEvento=NF3E_EVENT_VERSION,
                    any_element=EvCancNf3E(
                        descEvento=EvCancNf3EDescEvento.CANCELAMENTO,
                        nProt=self.authorization_protocol,
                        xJust=justification,
                    ),
                ),
                Id=f"ID{NF3E_CANCEL_EVENT}{self.document_key}{sequence}",
            ),
        )
        return self._nf3e_sign(event, event.infEvento.Id)
