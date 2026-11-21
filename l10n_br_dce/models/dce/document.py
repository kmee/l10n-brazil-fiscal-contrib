# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import random
import re

from odoo import _, api, fields
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_dce_spec.bindings.v1_0.dce_tipos_basico_v1_00 import (
    Tdce,
    TendeDest,
    TendeEmi,
)
from odoo.addons.l10n_br_dce_spec.bindings.v1_0.dce_v1_00 import Dce
from odoo.addons.l10n_br_dce_spec.bindings.v1_0.ev_canc_dce_v1_00 import (
    EvCancDce,
    EvCancDceDescEvento,
)
from odoo.addons.l10n_br_dce_spec.bindings.v1_0.evento_dce_tipos_basico_v1_00 import (
    Tevento,
)
from odoo.addons.l10n_br_dce_spec.bindings.v1_0.evento_dce_v1_00 import EventoDce
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    NFE_IND_IE_DEST_1,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_FISCAL_CANCELADO,
)
from odoo.addons.l10n_br_fiscal_edi.tools import tax_authority_date_to_utc
from odoo.addons.spec_driven_model.models import spec_models

from ...constants import (
    DCE_AUTHORIZED,
    DCE_CANCEL_EVENT,
    DCE_DECLARATION_1,
    DCE_DECLARATION_2,
    DCE_EVENT_REGISTERED,
    DCE_HOMOLOGATION_NAME,
    DCE_ISSUER_CARRIER,
    DCE_ISSUER_MARKETPLACE,
    DCE_ISSUER_OWN,
    DCE_ISSUER_TYPES,
    DCE_MAX_ITEM_VALUE,
    DCE_MAX_TOTAL_VALUE,
    DCE_SCHEMAS,
    DCE_VERSION,
    MODELO_FISCAL_DCE,
)
from ...dce_client.client import DceClient
from ...dce_client.servers import Endpoint, get_location


def filter_dce(record):
    return (
        record.processador_edoc == PROCESSADOR_OCA
        and record.document_type_id.code == MODELO_FISCAL_DCE
    )


def _digits(value):
    return re.sub(r"\D", "", value or "")


def _phone(value):
    """DDD and number only (fone of the DC-e: [0-9]{7,12})."""
    digits = _digits(value)
    if len(digits) > 11 and digits.startswith("55"):
        digits = digits[2:]
    return digits if 7 <= len(digits) <= 12 else None


def _decimal(value, min_digits, max_digits):
    """Number with min_digits to max_digits decimal places."""
    text = f"{value or 0.0:.{max_digits}f}"
    integer, decimals = text.split(".")
    decimals = decimals.rstrip("0").ljust(min_digits, "0")
    return f"{integer}.{decimals}"


def _check_digit(key):
    """Modulo 11 (weights 2 to 9) check digit of the access key (MOC DC-e,
    Anexo I, field B09)."""
    total = sum(int(char) * (2 + index % 8) for index, char in enumerate(key[::-1]))
    rest = total % 11
    return "0" if rest < 2 else str(11 - rest)


def _random_code(number):
    """cDC of the access key: 6 digits, neither a repeated digit nor the
    number of the DC-e (MOC DC-e, Anexo I, rule B03-10)."""
    while True:
        code = str(random.randint(0, 999999)).zfill(6)
        if len(set(code)) > 1 and code != (number or "").zfill(6):
            return code


def _party_document(partner):
    """CNPJ or CPF tag of a party of the DC-e, by the size of its number."""
    vat = _digits(partner.vat)
    if len(vat) == 14:
        return {"CNPJ": vat}
    if len(vat) == 11:
        return {"CPF": vat}
    return {}


def _address(partner):
    return {
        "xLgr": partner.street_name or partner.street,
        "nro": partner.street_number or "SN",
        "xCpl": partner.street2 or None,
        "xBairro": partner.district,
        "cMun": partner.city_id.ibge_code,
        "xMun": partner.city_id.name,
        "UF": partner.state_id.code,
        "CEP": _digits(partner.zip) or None,
        "cPais": "1058",
        "xPais": "Brasil",
        "fone": _phone(partner.phone),
    }


class DCe(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document"
    _inherit = ["l10n_br_fiscal.document", "dce.10.infdce"]

    _dce10_odoo_module = (
        "odoo.addons.l10n_br_dce_spec.models.v1_0.dce_tipos_basico_v1_00"
    )
    _dce10_stacking_mixin = "dce.10.infdce"
    # emit and dest share their tag names (CNPJ, xNome, the address...), so
    # they are not stacked: the per tag hooks below export them
    _dce10_stacking_skip_paths = ["dce10_emit", "dce10_dest"]
    _dce_search_keys = ["dce10_Id"]

    # When dynamic stacking is applied the DC-e structure is:
    # (+ stacked in the document / - exported by tag hooks)
    INFDCE_TREE = """
+ <infDCe>
    + <ide>
    - <emit> (company or sender)
    - <Marketplace> or <Transportadora> (company)
    - <dest> (partner_id)
    = <det> (fiscal lines)
    + <total>
    + <transp>
    - <infAdic>
    + <infDec>"""

    def _register_hook(self):
        # the fiscal document stacks several schemas and _spec_prefix only
        # finds the first one in the MRO: run the hook that makes the
        # remaining DC-e spec models concrete for the dce schema itself
        res = super()._register_hook()
        self.with_context(
            spec_schema="dce", spec_version="10"
        )._register_remaining_schema_models_hook()
        return res

    dce_environment = fields.Selection(
        selection=[("1", "Production"), ("2", "Homologation")],
        string="DC-e Environment",
        copy=False,
        default=lambda self: self.env.company.dce_environment,
    )

    dce_issuer_type = fields.Selection(
        selection=DCE_ISSUER_TYPES,
        string="DC-e Issuer Type",
        default=lambda self: self.env.company.dce_issuer_type,
    )

    dce_sender_id = fields.Many2one(
        comodel_name="res.partner",
        string="DC-e Sender",
        help="Person or company that sends the goods, when the company "
        "issues the DC-e as a marketplace or as a carrier.",
    )

    dce_carrier_id = fields.Many2one(
        comodel_name="res.partner",
        string="DC-e Carrier",
        help="Carrier of the goods (transp/CNPJTransp).",
    )

    ##########################
    # DC-e tag: infDCe
    ##########################

    dce10_versao = fields.Char(compute="_compute_dce10_versao")

    dce10_Id = fields.Char(compute="_compute_dce10_id_tag")

    def _compute_dce10_versao(self):
        self.dce10_versao = DCE_VERSION

    @api.depends("document_type_id", "document_key")
    def _compute_dce10_id_tag(self):
        for record in self:
            record.dce10_Id = (
                f"{record.document_type_id.prefix}{record.document_key}"
                if record.document_type_id.prefix and record.document_key
                else False
            )

    def _get_dce_sender(self):
        """The usuário emitente (MOC DC-e, Anexo I, group C): the company in
        its own DC-e, the sender when it issues as marketplace or carrier."""
        self.ensure_one()
        if self.dce_issuer_type == DCE_ISSUER_OWN:
            return self.company_id.partner_id
        return self.dce_sender_id

    ##########################
    # DC-e tag: ide
    ##########################

    dce10_cUF = fields.Selection(compute="_compute_dce10_ide")
    dce10_cDC = fields.Char(related="key_random_code")
    dce10_mod = fields.Selection(compute="_compute_dce10_ide")
    dce10_serie = fields.Char(related="document_serie")
    dce10_nDC = fields.Char(related="document_number")
    dce10_dhEmi = fields.Datetime(related="document_date")
    dce10_tpEmis = fields.Selection(default="1")
    dce10_tpEmit = fields.Char(compute="_compute_dce10_ide")
    dce10_nSiteAutoriz = fields.Char(default="0")
    dce10_cDV = fields.Char(related="key_check_digit")
    dce10_tpAmb = fields.Selection(related="dce_environment")
    dce10_verProc = fields.Char(
        copy=False,
        default=lambda self: self.env["ir.config_parameter"]
        .sudo()
        .get_param("l10n_br_dce.version.name", default="Odoo Brasil OCA v16"),
    )

    @api.depends(
        "document_type_id",
        "dce_issuer_type",
        "dce_sender_id.state_id",
        "company_id.partner_id.state_id",
    )
    def _compute_dce10_ide(self):
        for record in self:
            # rule B02-20 (NT 2024.001 v1.30): cUF is the UF of the emit
            record.dce10_cUF = record._get_dce_sender().state_id.ibge_code or False
            record.dce10_mod = (
                MODELO_FISCAL_DCE
                if record.document_type_id.code == MODELO_FISCAL_DCE
                else False
            )
            record.dce10_tpEmit = record.dce_issuer_type or False

    ##########################
    # DC-e tags: emit, Marketplace, Transportadora and dest
    ##########################

    def _export_tag_dce_10_emit(self, xsd_fields, class_obj, export_dict):
        sender = self._get_dce_sender()
        export_dict.update(_party_document(sender))
        export_dict["xNome"] = sender.legal_name or sender.name
        export_dict["enderEmit"] = TendeEmi(**_address(sender))

    def _export_tag_dce_10_marketplace(self, xsd_fields, class_obj, export_dict):
        if self.dce_issuer_type != DCE_ISSUER_MARKETPLACE:
            return
        company = self.company_id
        export_dict.update(
            {
                "CNPJ": _digits(company.vat),
                "xNome": company.legal_name or company.name,
                "Site": company.dce_marketplace_site,
            }
        )

    def _export_tag_dce_10_transportadora(self, xsd_fields, class_obj, export_dict):
        if self.dce_issuer_type != DCE_ISSUER_CARRIER:
            return
        company = self.company_id
        export_dict.update(
            {
                "CNPJ": _digits(company.vat),
                "xNome": company.legal_name or company.name,
            }
        )

    def _export_tag_dce_10_dest(self, xsd_fields, class_obj, export_dict):
        partner = self.partner_id
        export_dict.update(_party_document(partner))
        # MOC DC-e, Anexo I, rule E04-20
        export_dict["xNome"] = (
            DCE_HOMOLOGATION_NAME
            if self.dce_environment == "2"
            else partner.legal_name or partner.name
        )
        export_dict["enderDest"] = TendeDest(
            **_address(partner), email=partner.email or None
        )

    ##########################
    # DC-e tags: det and total
    ##########################

    def _export_fields_dce_10_infdce(self, xsd_fields, class_obj, export_dict):
        """One det per fiscal line, numbered from 1 (rule H02-10)."""
        for tag in ("dce10_det", "dce10_autXML"):
            if tag in xsd_fields:
                xsd_fields.remove(tag)
        export_dict["det"] = [
            Tdce.InfDce.Det(
                nItem=str(index),
                prod=Tdce.InfDce.Det.Prod(
                    xProd=(line.name or line.product_id.display_name)[:120],
                    # NT 2024.001 v1.30, rule I03-10: 00000000 when the good
                    # has no NCM
                    NCM=_digits(line.ncm_id.code) or "00000000",
                    qCom=_decimal(line.quantity, 4, 4),
                    vUnCom=_decimal(line.price_unit, 2, 8),
                    vProd=_decimal(line.price_gross, 2, 2),
                ),
                infAdProd=(line.additional_data or "").strip()[:500] or None,
            )
            for index, line in enumerate(self.fiscal_line_ids, start=1)
        ]

    dce10_vDC = fields.Monetary(
        compute="_compute_dce10_vdc", currency_field="brl_currency_id"
    )

    @api.depends("fiscal_line_ids.price_gross")
    def _compute_dce10_vdc(self):
        """vDC is the sum of the vProd (NT 2024.001 v1.30, rule W16-20)."""
        for record in self:
            record.dce10_vDC = sum(record.fiscal_line_ids.mapped("price_gross"))

    ##########################
    # DC-e tags: transp, infAdic and infDec
    ##########################

    def _export_fields_dce_10_transp(self, xsd_fields, class_obj, export_dict):
        # CNPJTransp is required by the xsd and may be empty (TCnpjOpc)
        export_dict["CNPJTransp"] = _digits(self.dce_carrier_id.vat)

    def _export_tag_dce_10_infadic(self, xsd_fields, class_obj, export_dict):
        if self.fiscal_additional_data:
            export_dict["infAdFisco"] = self.fiscal_additional_data.strip()
        if self.customer_additional_data:
            export_dict["infCpl"] = self.customer_additional_data.strip()

    def _export_fields_dce_10_infdec(self, xsd_fields, class_obj, export_dict):
        """Fixed texts of the declaration (MOC DC-e, Anexo I, group ZA)."""
        for tag in ("dce10_xObs1", "dce10_xObs2"):
            if tag in xsd_fields:
                xsd_fields.remove(tag)
        export_dict["xObs1"] = DCE_DECLARATION_1
        export_dict["xObs2"] = DCE_DECLARATION_2

    ################################
    # Business Model Methods
    ################################

    def _get_dce_qrcode(self):
        """QR Code of the DACE (MOC DC-e, Anexo II, item 3.2)."""
        self.ensure_one()
        if self.dce10_tpEmis != "1":
            raise UserError(
                _("The QR Code of a DC-e issued in contingency is not supported yet.")
            )
        url = get_location(self.dce_environment, Endpoint.QRCODE)
        return f"{url}?chDCe={self.document_key}&tpAmb={self.dce_environment}"

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filter_dce):
            edocs.append(
                Dce(
                    infDCe=record._build_binding("dce", "10"),
                    # infSolicDCe is required by the xsd and only filled by the
                    # app of the tax authority (MOC DC-e, Anexo I, group ZB)
                    infSolicDCe=Tdce.InfSolicDce(xSolic=""),
                    infDCeSupl=Tdce.InfDceSupl(
                        qrCodDCe=record._get_dce_qrcode(),
                        urlChave=get_location(record.dce_environment, Endpoint.QRCODE),
                    ),
                )
            )
        return edocs

    def _dce_sign(self, binding, doc_id):
        certificate = self.company_id.sudo().certificate
        return binding.to_xml(
            pkcs12_data=certificate.with_context(bin_size=False).file,
            pkcs12_password=certificate.password,
            doc_id=doc_id,
        )

    def _dce_event_environment(self):
        return EVENT_ENV_PROD if self.dce_environment == "1" else EVENT_ENV_HML

    def _document_export(self, **kwargs):
        result = super()._document_export(**kwargs)
        for record in self.filtered(filter_dce):
            edoc = record.serialize()[0]
            signed_xml = record._dce_sign(edoc, edoc.infDCe.Id)
            if (
                record.authorization_event_id
                and record.authorization_event_id.state == "draft"
            ):
                record.sudo().authorization_event_id.unlink()
            record.authorization_event_id = record.event_ids.create_event_save_xml(
                company_id=record.company_id,
                environment=record._dce_event_environment(),
                event_type="0",
                xml_file=signed_xml,
                document_id=record,
            )
            record._validate_xml(signed_xml)
        return result

    def _validate_xml(self, xml_file):
        self.ensure_one()
        if not filter_dce(self):
            return super()._validate_xml(xml_file)
        errors = Dce.schema_validation(xml_file, schema_path=DCE_SCHEMAS["dce"])
        self.write({"xml_error_message": "\n".join(errors) or False})

    def _get_dce_client(self):
        self.ensure_one()
        certificate = self.company_id.sudo().certificate
        return DceClient(
            ambiente=self.dce_environment,
            uf=self.company_id.state_id.ibge_code,
            pkcs12_data=certificate.with_context(bin_size=False).file,
            pkcs12_password=certificate.password,
        )

    def _eletronic_document_send(self):
        dce_documents = self.filtered(filter_dce)
        result = super(DCe, self - dce_documents)._eletronic_document_send()
        for record in dce_documents:
            if record.xml_error_message:
                continue
            signed_xml = base64.b64decode(
                record.authorization_event_id.file_request_id.datas
            ).decode("utf-8")
            response = record._get_dce_client().envia_dce(signed_xml)
            record._dce_process_response(response, signed_xml)
        return result

    def _dce_process_response(self, response, signed_xml):
        """Answer of the synchronous DCeAutorizacao (MOC DC-e, Visão Geral,
        item 5.1.2)."""
        self.ensure_one()
        status = response.cStat
        reason = response.xMotivo
        inf_prot = response.protDCe and response.protDCe.infProt
        if inf_prot:
            status = inf_prot.cStat
            reason = inf_prot.xMotivo
        self.write({"status_code": status, "status_name": reason})
        if status in DCE_AUTHORIZED and inf_prot:
            self.authorization_event_id.set_done(
                status_code=status,
                response=reason,
                protocol_date=tax_authority_date_to_utc(inf_prot.dhRecbto),
                protocol_number=inf_prot.nProt,
                file_response_xml=self._dce_proc_xml(signed_xml, response),
            )
            self._change_state(SITUACAO_EDOC_AUTORIZADA)
        else:
            self._change_state(SITUACAO_EDOC_REJEITADA)

    def _dce_proc_xml(self, signed_xml, response):
        """dceProc: the signed DC-e with the authorization protocol."""
        prot_xml = response.protDCe.to_xml(ns_map={None: Dce.Meta.namespace})
        prot_xml = re.sub(r"^\s*<\?xml[^>]*\?>", "", prot_xml).strip()
        # the binding is the TProtDCe type: the element is protDCe
        prot_xml = re.sub(r"^<TProtDCe\b", "<protDCe", prot_xml)
        prot_xml = re.sub(r"</TProtDCe>$", "</protDCe>", prot_xml)
        dce_xml = re.sub(r"^\s*<\?xml[^>]*\?>", "", signed_xml).strip()
        return (
            f'<dceProc xmlns="{Dce.Meta.namespace}" versao="{DCE_VERSION}">'
            f"{dce_xml}{prot_xml}</dceProc>"
        )

    ################################
    # Cancellation event (MOC DC-e, Visão Geral, items 5.4 and 5.5)
    ################################

    def _dce_build_event(self, event_type, detail, sequence=1):
        self.ensure_one()
        if not self.authorization_protocol:
            raise UserError(_("Authorization Protocol Not Found!"))
        now = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        user = _party_document(self._get_dce_sender())
        return EventoDce(
            versao=DCE_VERSION,
            infEvento=Tevento.InfEvento(
                # P07-10: "ID" + tpEvento + chDCe + nSeqEvento (3 digits)
                Id=f"ID{event_type}{self.document_key}{sequence:03d}",
                # P05-10 and P09-30: the UF of the access key
                cOrgao=self.document_key[:2],
                tpAmb=self.dce_environment,
                tpEmit=self.dce10_tpEmit,
                # P09-44: the CNPJ of the access key
                CNPJAutor=_digits(self.company_id.vat),
                CNPJUsEmit=user.get("CNPJ"),
                CPFUsEmit=user.get("CPF"),
                chDCe=self.document_key,
                dhEvento=now.replace(microsecond=0).isoformat("T"),
                tpEvento=event_type,
                nSeqEvento=str(sequence),
                detEvento=Tevento.InfEvento.DetEvento(
                    versaoEvento=DCE_VERSION, any_element=detail
                ),
            ),
        )

    def _dce_send_event(self, event_type, detail, odoo_event_type, justification):
        """Sign, validate and send an event; return the Odoo event and the
        answer. A refusal is returned, not raised, so the event is kept."""
        self.ensure_one()
        evento = self._dce_build_event(event_type, detail)
        signed_xml = self._dce_sign(evento, evento.infEvento.Id)
        errors = EventoDce.schema_validation(
            signed_xml, schema_path=DCE_SCHEMAS["evento"]
        )
        if errors:
            raise ValidationError("\n".join(errors))
        event = self.event_ids.create_event_save_xml(
            company_id=self.company_id,
            environment=self._dce_event_environment(),
            event_type=odoo_event_type,
            xml_file=signed_xml,
            document_id=self,
            sequence="1",
            justification=justification,
        )
        response = self._get_dce_client().envia_evento(signed_xml).infEvento
        event.write({"status_code": response.cStat, "response": response.xMotivo})
        if response.cStat in DCE_EVENT_REGISTERED:
            event.set_done(
                status_code=response.cStat,
                response=response.xMotivo,
                protocol_date=tax_authority_date_to_utc(response.dhRegEvento),
                protocol_number=response.nProt,
                file_response_xml=False,
            )
        return event, response

    def _document_cancel(self, justificative=None):
        dce_documents = self.filtered(filter_dce)
        result = None
        if self - dce_documents:
            result = super(DCe, self - dce_documents)._document_cancel(justificative)
        for record in dce_documents:
            justification = (justificative or "").strip()
            # MOC DC-e, Visão Geral, item 5.5.1: xJust has 15 to 255 characters
            if not 15 <= len(justification) <= 255:
                raise UserError(
                    _("The DC-e cancellation reason must have 15 to 255 characters.")
                )
            record.cancel_reason = justification
            detail = EvCancDce(
                descEvento=EvCancDceDescEvento.CANCELAMENTO,
                nProt=record.authorization_protocol,
                xJust=justification,
            )
            event, response = record._dce_send_event(
                DCE_CANCEL_EVENT, detail, "2", justification
            )
            record.cancel_event_id = event
            if response.cStat not in DCE_EVENT_REGISTERED:
                record.message_post(
                    body=_(
                        "DC-e cancellation refused: %(code)s - %(reason)s",
                        code=response.cStat,
                        reason=response.xMotivo,
                    )
                )
                continue
            record.state_fiscal = SITUACAO_FISCAL_CANCELADO
            super(DCe, record)._document_cancel(justificative)
        return result

    ################################
    # Key, number and checks
    ################################

    def _generate_key(self):
        dce_documents = self.filtered(
            lambda doc: doc.document_type_id.code == MODELO_FISCAL_DCE
        )
        result = None
        if self - dce_documents:
            result = super(DCe, self - dce_documents)._generate_key()
        for record in dce_documents:
            # NT 2024.001 v1.30, item 3.1 (chave de acesso): the CNPJ is the
            # one of the company, that signs the DC-e
            date = fields.Datetime.context_timestamp(record, record.document_date)
            record.key_random_code = _random_code(record.document_number)
            key = "".join(
                (
                    record.dce10_cUF or "",
                    date.strftime("%y%m"),
                    _digits(record.company_id.vat),
                    MODELO_FISCAL_DCE,
                    (record.document_serie or "").zfill(3),
                    (record.document_number or "").zfill(9),
                    record.dce10_tpEmis or "1",
                    record.dce10_tpEmit or "",
                    record.dce10_nSiteAutoriz or "0",
                    record.key_random_code,
                )
            )
            if len(key) != 43:
                raise ValidationError(
                    _(
                        "Cannot build the DC-e access key of %(document)s: check "
                        "the company CNPJ, the state of the sender, the serie and "
                        "the number.",
                        document=record.display_name,
                    )
                )
            record.key_check_digit = _check_digit(key)
            record.document_key = key + record.key_check_digit
        return result

    @api.constrains("document_key")
    def _check_key(self):
        # erpbrasil.base does not know the model 99 yet
        dce_documents = self.filtered(
            lambda doc: doc.document_type_id.code == MODELO_FISCAL_DCE
        )
        result = super(DCe, self - dce_documents)._check_key()
        for record in dce_documents.filtered("document_key"):
            key = record.document_key
            # MOC DC-e, Anexo I, rules A03-10 and B09-10
            if not (
                re.fullmatch(r"[0-9]{44}", key)
                and key[20:22] == MODELO_FISCAL_DCE
                and _check_digit(key[:43]) == key[43]
            ):
                raise ValidationError(_("Invalid DC-e access key: %(key)s", key=key))
        return result

    def _document_number(self):
        if (
            self.document_type_id.code == MODELO_FISCAL_DCE
            and self.issuer == DOCUMENT_ISSUER_COMPANY
            and not self.document_serie_id
        ):
            serie = self.document_type_id.get_document_serie(
                self.company_id, self.fiscal_operation_id
            )
            if serie:
                self.document_serie_id = serie
        return super()._document_number()

    def _document_check(self):
        result = super()._document_check()
        for record in self.filtered(filter_dce):
            record._check_dce_required_fields()
        return result

    def _check_dce_required_fields(self):
        self.ensure_one()
        company = self.company_id
        sender = self._get_dce_sender()
        partner = self.partner_id
        checks = [
            (len(_digits(company.vat)) == 14, _("Company CNPJ")),
            (company.sudo().certificate, _("Digital Certificate")),
            (self.dce_environment, _("DC-e Environment")),
            (self.dce_issuer_type, _("DC-e Issuer Type")),
            (_party_document(sender), _("CNPJ or CPF of the sender")),
            (sender.state_id and sender.city_id, _("City of the sender")),
            (_party_document(partner), _("CNPJ or CPF of the recipient")),
            (partner.state_id and partner.city_id, _("City of the recipient")),
            (self.dce10_modTrans, _("Transport Mode")),
            (self.fiscal_line_ids, _("Goods (fiscal lines)")),
        ]
        if self.dce_issuer_type == DCE_ISSUER_MARKETPLACE:
            checks.append((company.dce_marketplace_site, _("Marketplace Site")))
        missing = [label for value, label in checks if not value]
        if missing:
            raise UserError(
                _("Fill in the required DC-e fields:\n- %s") % "\n- ".join(missing)
            )
        # MOC DC-e, Anexo I, rule C02-30: an ICMS taxpayer cannot issue a DC-e
        if sender.ind_ie_dest == NFE_IND_IE_DEST_1:
            raise UserError(
                _(
                    "%(sender)s is an ICMS taxpayer and cannot be the sender of a "
                    "DC-e: issue an NF-e.",
                    sender=sender.display_name,
                )
            )
        # MOC DC-e, Anexo I, group H: up to 999 items
        if len(self.fiscal_line_ids) > 999:
            raise UserError(_("A DC-e has at most 999 items."))
        # NT 2024.001 v1.30, rules I06-10 and W16-10
        if any(
            price > DCE_MAX_ITEM_VALUE
            for price in self.fiscal_line_ids.mapped("price_gross")
        ):
            raise UserError(_("The value of a DC-e item is above R$ 100,000,000.00."))
        if self.dce10_vDC > DCE_MAX_TOTAL_VALUE:
            raise UserError(_("The total of the DC-e is above R$ 100,000,000.00."))
