# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import os
import re
from random import SystemRandom

import nfelib
from nfelib.nfcom.bindings.v1_0.ev_canc_nfcom_v1_00 import (
    EvCancNfcom,
    EvCancNfcomDescEvento,
)
from nfelib.nfcom.bindings.v1_0.evento_nfcom_v1_00 import EventoNfcom
from nfelib.nfcom.bindings.v1_0.nfcom_tipos_basico_v1_00 import Tnfcom
from nfelib.nfcom.bindings.v1_0.nfcom_v1_00 import Nfcom

from odoo import _, api, fields
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    PROCESSADOR_OCA,
)
from odoo.addons.spec_driven_model.models import spec_models

MODELO_FISCAL_NFCOM = "62"
NFCOM_VERSION = "1.00"
NFCOM_SCHEMAS = os.path.join(os.path.dirname(nfelib.__file__), "nfcom", "schemas")
NFCOM_XSD = os.path.join(NFCOM_SCHEMAS, "v1_0", "nfcom_v1.00.xsd")
NFCOM_EVENT_XSD = os.path.join(NFCOM_SCHEMAS, "v1_0", "eventoNFCom_v1.00.xsd")
NFCOM_EVENT_CANCEL = "110111"

# QR Code query URLs per authorizer, from the services page of the Portal
# NFCom (dfe-portal.svrs.rs.gov.br/Nfcom/Servicos); the other states use SVRS.
NFCOM_QRCODE_URLS = {
    "31": {"1": "https://portalnfcom.fazenda.mg.gov.br/qrcode"},
    "50": {"1": "https://www.dfe.ms.gov.br/nfcom/qrcode"},
    "51": {
        "1": "https://www.sefaz.mt.gov.br/nfcom-ext-fe/qrcode",
        "2": "https://homologacao.sefaz.mt.gov.br/nfcom-ext-fe/qrcode",
    },
}
NFCOM_QRCODE_URL_SVRS = "https://dfe-portal.svrs.rs.gov.br/nfcom/qrCode"


def filter_processador_edoc_nfcom(record):
    return (
        record.processador_edoc == PROCESSADOR_OCA
        and record.document_type_id.code == MODELO_FISCAL_NFCOM
    )


def only_digits(value):
    return re.sub(r"\W", "", value or "").upper()


def key_check_digit(key):
    """Modulo 11 check digit of the access key (MOC NFCom 1.00a, item 7.3).

    Letters of the alphanumeric CNPJ are weighted by their ASCII code minus 48.
    """
    total = sum((ord(char) - 48) * (2 + i % 8) for i, char in enumerate(reversed(key)))
    remainder = total % 11
    return "0" if remainder < 2 else str(11 - remainder)


class NFCom(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document"
    _inherit = ["l10n_br_fiscal.document", "nfcom.10.infnfcom"]

    _nfcom10_odoo_module = (
        "odoo.addons.l10n_br_nfcom_spec.models.v1_0.nfcom_tipos_basico_v1_00"
    )
    _nfcom10_stacking_mixin = "nfcom.10.infnfcom"
    # emit and dest are exported by their tag hooks from the company and the
    # partner: stacked, their CNPJ, IE and xNome fields would collide. gFat and
    # gFatCentral are an optional choice that would be stacked as required.
    _nfcom10_stacking_skip_paths = (
        "nfcom10_emit",
        "nfcom10_dest",
        "nfcom10_gFat",
        "nfcom10_gFatCentral",
    )
    _nfcom10_stacking_force_paths = ("infnfcom.infAdic",)

    # When dynamic stacking is applied the NFCom structure is:
    # (+ content of the m2o is stacked in the parent / - standard m2o /
    # = o2m; the mapped Odoo model may follow the tag)
    INFNFCOM_TREE = """
+ <infnfcom>
    + <ide>
    - <emit> tag hooks (res.company)
    - <dest> tag hooks (res.partner)
    + <assinante>
    - <gSub>
    - <gCofat>
    = <det> l10n_br_fiscal.document.line
    - <pgtoVinc>
    + <total>
        + <ICMSTot>
        + <vRetTribTot>
        - <IBSCBSTot> tag hooks
    - <gFidelidade>
    - <gFat>
    - <gFatCentral>
    = <autXML>
    + <infAdic>
    - <gRespTec>"""

    def _register_hook(self):
        """Build the concrete NFCom spec models whatever the MRO resolves to.

        The hook of spec_driven_model takes the schema from the MRO: with
        another spec driven module extending the fiscal document after this
        one, it resolves to that schema and the NFCom models (gSub, gCofat,
        pgtoVinc, gFidelidade...) would get no table.
        """
        res = super()._register_hook()
        self.with_context(
            spec_schema="nfcom", spec_version="10"
        )._register_remaining_schema_models_hook()
        return res

    nfcom_environment = fields.Selection(
        related="company_id.nfcom_environment",
        string="NFCom Environment",
    )

    ##########################
    # NFCom tag: infNFCom
    ##########################

    nfcom10_versao = fields.Char(compute="_compute_nfcom10_infnfcom")

    nfcom10_Id = fields.Char(compute="_compute_nfcom10_infnfcom")

    @api.depends("document_type_id", "document_key")
    def _compute_nfcom10_infnfcom(self):
        self.nfcom10_versao = False
        self.nfcom10_Id = False
        for record in self.filtered(filter_processador_edoc_nfcom):
            record.nfcom10_versao = NFCOM_VERSION
            if record.document_key:
                record.nfcom10_Id = f"NFCom{record.document_key}"

    ##########################
    # NFCom tag: ide
    ##########################

    nfcom10_cUF = fields.Selection(compute="_compute_nfcom10_ide")

    nfcom10_tpAmb = fields.Selection(related="nfcom_environment")

    nfcom10_mod = fields.Selection(compute="_compute_nfcom10_ide")

    nfcom10_serie = fields.Char(related="document_serie")

    nfcom10_nNF = fields.Char(related="document_number")

    nfcom10_cNF = fields.Char(related="key_random_code")

    nfcom10_cDV = fields.Char(related="key_check_digit")

    nfcom10_dhEmi = fields.Datetime(related="document_date")

    nfcom10_tpEmis = fields.Selection(default="1")

    nfcom10_nSiteAutoriz = fields.Char(default="0")

    nfcom10_cMunFG = fields.Char(compute="_compute_nfcom10_ide")

    nfcom10_finNFCom = fields.Selection(default="0")

    nfcom10_tpFat = fields.Selection(default="0")

    nfcom10_verProc = fields.Char(
        default=lambda self: self.env["ir.config_parameter"]
        .sudo()
        .get_param("l10n_br_nfcom.version.name", default="Odoo Brasil OCA v16")
    )

    @api.depends("company_id", "document_type_id")
    def _compute_nfcom10_ide(self):
        self.nfcom10_cUF = False
        self.nfcom10_mod = False
        self.nfcom10_cMunFG = False
        for record in self.filtered(filter_processador_edoc_nfcom):
            record.nfcom10_cUF = record.company_id.state_id.ibge_code
            record.nfcom10_mod = MODELO_FISCAL_NFCOM
            record.nfcom10_cMunFG = record.company_id.city_id.ibge_code

    ##########################
    # NFCom tag: det
    ##########################

    nfcom10_det = fields.One2many(
        comodel_name="l10n_br_fiscal.document.line",
        inverse_name="document_id",
        related="fiscal_line_ids",
    )

    ##########################
    # NFCom tag: total
    ##########################

    nfcom10_vProd = fields.Monetary(compute="_compute_nfcom10_total")
    nfcom10_vBC = fields.Monetary(compute="_compute_nfcom10_total")
    nfcom10_vICMS = fields.Monetary(compute="_compute_nfcom10_total")
    nfcom10_vICMSDeson = fields.Monetary(compute="_compute_nfcom10_total")
    nfcom10_vFCP = fields.Monetary(compute="_compute_nfcom10_total")
    nfcom10_vCOFINS = fields.Monetary(compute="_compute_nfcom10_total")
    nfcom10_vPIS = fields.Monetary(compute="_compute_nfcom10_total")
    nfcom10_vFUNTTEL = fields.Monetary(compute="_compute_nfcom10_total")
    nfcom10_vFUST = fields.Monetary(compute="_compute_nfcom10_total")
    nfcom10_vRetPIS = fields.Monetary(compute="_compute_nfcom10_total")
    nfcom10_vRetCofins = fields.Monetary(compute="_compute_nfcom10_total")
    nfcom10_vRetCSLL = fields.Monetary(compute="_compute_nfcom10_total")
    nfcom10_vIRRF = fields.Monetary(compute="_compute_nfcom10_total")
    nfcom10_vDesc = fields.Monetary(compute="_compute_nfcom10_total")
    nfcom10_vOutro = fields.Monetary(compute="_compute_nfcom10_total")
    nfcom10_vNF = fields.Monetary(compute="_compute_nfcom10_total")

    @api.depends(
        "fiscal_line_ids.nfcom_amount_item",
        "amount_icms_base",
        "amount_icms_value",
        "amount_icmsfcp_value",
        "amount_pis_value",
        "amount_cofins_value",
        "amount_pis_wh_value",
        "amount_cofins_wh_value",
        "amount_csll_wh_value",
        "amount_irpj_wh_value",
        "amount_discount_value",
        "amount_other_value",
    )
    def _compute_nfcom10_total(self):
        for record in self:
            amount_item = sum(record.fiscal_line_ids.mapped("nfcom_amount_item"))
            retentions = (
                record.amount_pis_wh_value
                + record.amount_cofins_wh_value
                + record.amount_csll_wh_value
                + record.amount_irpj_wh_value
            )
            record.update(
                {
                    "nfcom10_vProd": amount_item,
                    "nfcom10_vBC": record.amount_icms_base,
                    "nfcom10_vICMS": record.amount_icms_value,
                    "nfcom10_vICMSDeson": 0.0,
                    "nfcom10_vFCP": record.amount_icmsfcp_value,
                    "nfcom10_vCOFINS": record.amount_cofins_value,
                    "nfcom10_vPIS": record.amount_pis_value,
                    "nfcom10_vFUNTTEL": 0.0,
                    "nfcom10_vFUST": 0.0,
                    "nfcom10_vRetPIS": record.amount_pis_wh_value,
                    "nfcom10_vRetCofins": record.amount_cofins_wh_value,
                    "nfcom10_vRetCSLL": record.amount_csll_wh_value,
                    "nfcom10_vIRRF": record.amount_irpj_wh_value,
                    "nfcom10_vDesc": record.amount_discount_value,
                    "nfcom10_vOutro": record.amount_other_value,
                    # MOC NFCom 1.00a, Anexo I, rule G137
                    "nfcom10_vNF": amount_item - retentions,
                }
            )

    ##########################
    # NFCom tag: infAdic
    ##########################

    nfcom10_infAdFisco = fields.Char(compute="_compute_nfcom10_infadic")

    nfcom10_infCpl = fields.Char(compute="_compute_nfcom10_infadic")

    @api.depends("fiscal_additional_data", "customer_additional_data")
    def _compute_nfcom10_infadic(self):
        for record in self:
            record.nfcom10_infAdFisco = _one_line(record.fiscal_additional_data)
            record.nfcom10_infCpl = _one_line(record.customer_additional_data)

    ################################
    # Export: tag hooks
    ################################

    def _export_field(self, xsd_field, class_obj, member_spec, export_value=None):
        if xsd_field == "nfcom10_infCpl":
            # infCpl may repeat up to 5 times: the binding takes a list
            return [self.nfcom10_infCpl] if self.nfcom10_infCpl else False
        return super()._export_field(xsd_field, class_obj, member_spec, export_value)

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        if field_name == "nfcom10_infAdic" and not (
            self.nfcom10_infCpl or self.nfcom10_infAdFisco
        ):
            return False
        return super()._export_many2one(field_name, xsd_required, class_obj)

    def _export_one2many(self, field_name, class_obj=None):
        res = super()._export_one2many(field_name, class_obj)
        if class_obj._fields[field_name].comodel_name == "nfcom.10.det":
            for i, det in enumerate(res, start=1):
                det.nItem = str(i)
        return res

    def _export_tag_nfcom_10_emit(self, xsd_fields, class_obj, export_dict):
        company = self.company_id
        export_dict.update(
            {
                "CNPJ": only_digits(company.vat),
                "IE": only_digits(company.l10n_br_ie_code),
                "CRT": company.tax_framework,
                "xNome": company.legal_name or company.name,
                "xFant": company.name,
            }
        )

    def _export_tag_nfcom_10_enderemit(self, xsd_fields, class_obj, export_dict):
        export_dict.update(_address_values(self.company_id.partner_id))

    def _export_tag_nfcom_10_dest(self, xsd_fields, class_obj, export_dict):
        partner = self.partner_id
        vat = only_digits(partner.vat)
        export_dict.update(
            {
                "xNome": partner.legal_name or partner.name,
                "CNPJ" if len(vat) == 14 else "CPF": vat or None,
                "indIEDest": partner.ind_ie_dest or "9",
                "IE": only_digits(partner.l10n_br_ie_code) or None,
            }
        )

    def _export_tag_nfcom_10_enderdest(self, xsd_fields, class_obj, export_dict):
        export_dict.update(_address_values(self.partner_id))

    def _nfcom_export_ibscbs_totals(self):
        self.ensure_one()
        return bool(self.fiscal_line_ids.filtered("tax_classification_id"))

    def _export_tag_nfcom_10_ibscbstot(self, xsd_fields, class_obj, export_dict):
        if not self._nfcom_export_ibscbs_totals():
            return
        lines = self.fiscal_line_ids
        export_dict["vBCIBSCBS"] = sum(lines.mapped("ibs_base")) or sum(
            lines.mapped("cbs_base")
        )

    def _export_tag_nfcom_10_gibs(self, xsd_fields, class_obj, export_dict):
        export_dict["vIBS"] = sum(self.fiscal_line_ids.mapped("ibs_value"))

    def _export_tag_nfcom_10_gibsuf(self, xsd_fields, class_obj, export_dict):
        export_dict.update(
            {
                "vDif": 0.0,
                "vDevTrib": 0.0,
                "vIBSUF": sum(self.fiscal_line_ids.mapped("ibs_value")),
            }
        )

    def _export_tag_nfcom_10_gibsmun(self, xsd_fields, class_obj, export_dict):
        export_dict.update({"vDif": 0.0, "vDevTrib": 0.0, "vIBSMun": 0.0})

    def _export_tag_nfcom_10_gcbs(self, xsd_fields, class_obj, export_dict):
        export_dict.update(
            {
                "vDif": 0.0,
                "vDevTrib": 0.0,
                "vCBS": sum(self.fiscal_line_ids.mapped("cbs_value")),
            }
        )

    ################################
    # Business Model Methods
    ################################

    def _nfcom_qrcode_url(self):
        self.ensure_one()
        urls = NFCOM_QRCODE_URLS.get(self.company_id.state_id.ibge_code, {})
        url = urls.get(self.nfcom_environment) or urls.get("1")
        return (
            f"{url or NFCOM_QRCODE_URL_SVRS}"
            f"?chNFCom={self.document_key}&tpAmb={self.nfcom_environment}"
        )

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filter_processador_edoc_nfcom):
            record.flush_model()
            inf_nfcom = record._build_binding("nfcom", "10")
            edocs.append(
                Nfcom(
                    infNFCom=inf_nfcom,
                    infNFComSupl=Tnfcom.InfNfcomSupl(
                        qrCodNFCom=record._nfcom_qrcode_url()
                    ),
                )
            )
        return edocs

    def _nfcom_sign(self, edoc, xml, doc_id):
        certificate = self.company_id.sudo().certificate
        return edoc.sign_xml(
            xml,
            certificate.with_context(bin_size=False).file,
            certificate.password,
            doc_id,
        )

    def _nfcom_event_environment(self):
        return EVENT_ENV_PROD if self.nfcom_environment == "1" else EVENT_ENV_HML

    def _document_export(self, pretty_print=True):
        result = super()._document_export()
        for record in self.filtered(filter_processador_edoc_nfcom):
            edoc = record.serialize()[0]
            signed_xml = record._nfcom_sign(edoc, edoc.to_xml(), edoc.infNFCom.Id)
            if (
                record.authorization_event_id
                and record.authorization_event_id.state == "draft"
            ):
                record.sudo().authorization_event_id.unlink()
            record.authorization_event_id = record.event_ids.create_event_save_xml(
                company_id=record.company_id,
                environment=record._nfcom_event_environment(),
                event_type="0",
                xml_file=signed_xml,
                document_id=record,
            )
            record._validate_xml(signed_xml)
        return result

    def _validate_xml(self, xml_file):
        self.ensure_one()
        if not filter_processador_edoc_nfcom(self):
            return super()._validate_xml(xml_file)
        errors = Nfcom.schema_validation(xml_file, NFCOM_XSD)
        self.write({"xml_error_message": "\n".join(errors) or False})

    def _nfcom_cancel_event_xml(self, justificative):
        """Signed eventoNFCom of the cancellation (tpEvento 110111, MOC NFCom
        1.00a, item 6.1), validated against the XSD."""
        self.ensure_one()
        protocol = self.authorization_event_id.protocol_number
        if not protocol:
            raise UserError(_("The NFCom has no authorization protocol to cancel."))
        sequence = "001"
        tz_date = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        event = EventoNfcom(
            versao=NFCOM_VERSION,
            infEvento=EventoNfcom.InfEvento(
                Id=f"ID{NFCOM_EVENT_CANCEL}{self.document_key}{sequence}",
                cOrgao=self.company_id.state_id.ibge_code,
                tpAmb=self.nfcom_environment,
                CNPJ=only_digits(self.company_id.vat),
                chNFCom=self.document_key,
                dhEvento=tz_date.isoformat("T", "seconds"),
                tpEvento=NFCOM_EVENT_CANCEL,
                nSeqEvento=str(int(sequence)),
                detEvento=EventoNfcom.InfEvento.DetEvento(
                    versaoEvento=NFCOM_VERSION,
                    any_element=EvCancNfcom(
                        descEvento=EvCancNfcomDescEvento.CANCELAMENTO,
                        nProt=protocol,
                        xJust=(_one_line(justificative) or "")[:255],
                    ),
                ),
            ),
        )
        signed_xml = self._nfcom_sign(event, event.to_xml(), event.infEvento.Id)
        errors = EventoNfcom.schema_validation(signed_xml, NFCOM_EVENT_XSD)
        if errors:
            raise ValidationError("\n".join(errors))
        return signed_xml

    def _nfcom_transmission_unavailable(self):
        raise UserError(
            _(
                "The NFCom transmission to the tax authority is not available "
                "yet: the XML is generated, signed and validated, but it has "
                "to be sent by other means (see the module roadmap)."
            )
        )

    def _eletronic_document_send(self):
        nfcom = self.filtered(filter_processador_edoc_nfcom)
        if nfcom:
            nfcom._nfcom_transmission_unavailable()
        return super(NFCom, self - nfcom)._eletronic_document_send()

    def _document_cancel(self, justificative=None):
        if filter_processador_edoc_nfcom(self):
            self._nfcom_cancel_event_xml(justificative)
            self._nfcom_transmission_unavailable()
        return super()._document_cancel(justificative)

    def _document_number(self):
        if (
            self.document_type_id.code == MODELO_FISCAL_NFCOM
            and self.issuer == DOCUMENT_ISSUER_COMPANY
            and not self.document_serie_id
        ):
            self.document_serie_id = self.document_type_id.get_document_serie(
                self.company_id, self.fiscal_operation_id
            )
        return super()._document_number()

    def _generate_key(self):
        nfcom = self.filtered(
            lambda doc: doc.document_type_id.code == MODELO_FISCAL_NFCOM
        )
        for record in nfcom:
            record._nfcom_generate_key()
        return super(NFCom, self - nfcom)._generate_key()

    def _nfcom_generate_key(self):
        """Access key of the NFCom (MOC NFCom 1.00a, item 2.1.3): cUF, AAMM,
        CNPJ, mod, serie, nNF, tpEmis, nSiteAutoriz, cNF and cDV."""
        self.ensure_one()
        cnpj = only_digits(self.company_id.vat)
        uf = self.company_id.state_id.ibge_code
        if len(cnpj) != 14 or not uf:
            raise ValidationError(
                _(
                    "To generate the NFCom key the company %s needs a CNPJ "
                    "and a state.",
                    self.company_id.display_name,
                )
            )
        if not self.document_serie or not self.document_number:
            raise ValidationError(
                _("To generate the NFCom key fill the serie and the number.")
            )
        date = fields.Datetime.context_timestamp(
            self, self.document_date or fields.Datetime.now()
        )
        random_code = self.key_random_code or str(
            SystemRandom().randrange(1, 10**7)
        ).zfill(7)
        key = (
            f"{uf}{date:%y%m}{cnpj}{MODELO_FISCAL_NFCOM}"
            f"{self.document_serie.zfill(3)}{self.document_number.zfill(9)}"
            f"{self.nfcom10_tpEmis or '1'}{self.nfcom10_nSiteAutoriz or '0'}"
            f"{random_code}"
        )
        check_digit = key_check_digit(key)
        self.key_random_code = random_code
        self.key_check_digit = check_digit
        self.document_key = key + check_digit


def _one_line(text):
    if not text:
        return False
    return " ".join(text.split()) or False


def _address_values(partner):
    phone = only_digits(partner.phone)
    if phone.startswith("55") and len(phone) > 11:
        phone = phone[2:]
    return {
        "xLgr": partner.street_name or partner.street,
        "nro": partner.street_number or "SN",
        "xCpl": partner.street2 or None,
        "xBairro": partner.district,
        "cMun": partner.city_id.ibge_code,
        "xMun": partner.city_id.name,
        "CEP": only_digits(partner.zip),
        "UF": partner.state_id.code,
        "fone": phone if 7 <= len(phone) <= 12 else None,
        "email": partner.email or None,
    }
