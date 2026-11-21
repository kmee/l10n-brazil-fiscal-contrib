# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import gzip
import importlib.resources
import re

import nfelib
from erpbrasil.base.fiscal.edoc import ChaveEdoc
from erpbrasil.base.misc import modulo11
from erpbrasil.edoc.cte import TransmissaoCTE
from lxml import etree
from nfelib.cte.bindings.v4_0.cte_tipos_basico_v4_00 import Tgtve
from nfelib.cte.bindings.v4_0.cte_v4_00 import Cte
from nfelib.cte.bindings.v4_0.gtve_v4_00 import Gtve
from nfelib.cte.bindings.v4_0.ret_gtve_v4_00 import RetGtve
from nfelib.nfe.ws.edoc_legacy import CTeAdapter
from requests import Session

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    AUTORIZADO,
    DENEGADO,
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_REJEITADA,
)
from odoo.addons.l10n_br_fiscal_edi.tools import tax_authority_date_to_utc

from .gtve.gtve import GTVE_VERSION

MODELO_FISCAL_GTVE = "64"

CTE_NS = "http://www.portalfiscal.inf.br/cte"

GTVE_SCHEMA = ("cte", "schemas", "v4_0", "GTVe_v4.00.xsd")

WS_GTVE_RECEPCAO = "CTeRecepcaoGTVeV4"

GTVE_HOMOLOGATION_NAME = "CTE EMITIDO EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL"


def filter_gtve(record):
    return (
        record.processador_edoc == PROCESSADOR_OCA
        and record.document_type_id.code == MODELO_FISCAL_GTVE
    )


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    gtve_id = fields.Many2one(comodel_name="l10n_br_gtve.gtve", copy=False)

    gtve_service_taker = fields.Selection(
        selection=[("0", "Sender"), ("1", "Recipient"), ("4", "Other")],
        string="GTV-e Service Taker",
        default="0",
        help="With Other, the service taker is the partner of the document.",
    )

    gtve_cfop_id = fields.Many2one(comodel_name="l10n_br_fiscal.cfop", string="CFOP")

    gtve_departure_date = fields.Datetime(string="Departure from Origin")

    gtve_arrival_date = fields.Datetime(string="Arrival at Destination")

    gtve_load_quantity = fields.Float(
        string="Volumes/Pouches", digits=(11, 4), copy=False
    )

    gtve_species_ids = fields.One2many(
        comodel_name="l10n_br_gtve.species",
        inverse_name="document_id",
        string="Transported Species",
        copy=True,
    )

    gtve_vehicle_ids = fields.One2many(
        comodel_name="l10n_br_gtve.vehicle",
        inverse_name="document_id",
        string="Vehicles",
        copy=True,
    )

    def _gtve_record(self):
        self.ensure_one()
        if not self.gtve_id:
            self.gtve_id = self.gtve_id.create({"document_id": self.id})
        return self.gtve_id

    def _check_gtve(self):
        """Data the GTV-e layout requires (MOC 4.00, Annex I, chapter 6)."""
        self.ensure_one()
        required = [
            "partner_sendering_id",
            "partner_shipping_id",
            "gtve_cfop_id",
            "gtve_departure_date",
            "gtve_arrival_date",
            "gtve_species_ids",
            "gtve_vehicle_ids",
        ]
        missing = [self._fields[name].string for name in required if not self[name]]
        if missing:
            raise UserError(
                _(
                    "GTV-e %(document)s: fill in %(fields)s.",
                    document=self.display_name,
                    fields=", ".join(missing),
                )
            )
        if self.transport_modal not in ("01", "06"):
            raise UserError(_("The GTV-e modal must be road (01) or multimodal (06)."))
        # MOC 4.00 Annex I, rule I04 (rejection 670)
        if 890 <= int(self.document_serie or 0) <= 899:
            raise UserError(_("The series 890 to 899 cannot be used in a GTV-e."))

    def _gtve_binding(self):
        self.ensure_one()
        inf_cte = self._gtve_record()._build_binding("cte", "40")
        # MOC 4.00 Annex I, rules I02 and I03 (rejections 646 and 649)
        if self.cte_environment == "2":
            inf_cte.rem.xNome = GTVE_HOMOLOGATION_NAME
            inf_cte.dest.xNome = GTVE_HOMOLOGATION_NAME
        inf_cte_supl = None
        if self.cte40_infCTeSupl.qrcode:
            inf_cte_supl = Tgtve.InfCteSupl(qrCodCTe=self.cte40_infCTeSupl.qrcode)
        return Gtve(infCte=inf_cte, infCTeSupl=inf_cte_supl, versao=GTVE_VERSION)

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filter_gtve):
            edocs.append(record._gtve_binding())
        return edocs

    def _edoc_processor(self):
        if not self.filtered(filter_gtve):
            return super()._edoc_processor()
        session = Session()
        session.verify = False
        return CTeAdapter(
            transmissao=TransmissaoCTE(self.company_id._get_br_ecertificate(), session),
            uf=self.company_id.state_id.ibge_code,
            versao=GTVE_VERSION,
            ambiente=self.cte_environment,
            mod=MODELO_FISCAL_GTVE,
        )

    def _generate_key(self):
        gtve = self.filtered(lambda d: d.document_type_id.code == MODELO_FISCAL_GTVE)
        result = super(Document, self - gtve)._generate_key()
        for record in gtve:
            date = fields.Datetime.context_timestamp(record, record.document_date)
            key = ChaveEdoc(
                ano_mes=date.strftime("%y%m"),
                cnpj_cpf_emitente=record.company_id.vat,
                codigo_uf=record.company_id.state_id.ibge_code or "",
                forma_emissao=1,
                modelo_documento=MODELO_FISCAL_GTVE,
                numero_documento=record.document_number or "",
                numero_serie=record.document_serie or "",
                validar=False,
            )
            record.key_random_code = key.codigo_aleatorio
            record.key_check_digit = key.digito_verificador
            record.document_key = key.chave
        return result

    @api.constrains("document_key")
    def _check_key(self):
        # erpbrasil.base does not know the model 64 yet
        gtve = self.filtered(lambda d: d.document_type_id.code == MODELO_FISCAL_GTVE)
        result = super(Document, self - gtve)._check_key()
        for record in gtve.filtered("document_key"):
            key = record.document_key
            # MOC 4.00 Annex I, rules I10 and I12 (rejections 875 and 253)
            if not (
                re.fullmatch(r"[0-9]{6}[A-Z0-9]{12}[0-9]{26}", key)
                and key[20:22] == MODELO_FISCAL_GTVE
                and str(modulo11(key[:43])) == key[43]
            ):
                raise ValidationError(_("Invalid GTV-e access key: %(key)s", key=key))
        return result

    def _document_qrcode(self):
        result = super()._document_qrcode()
        for record in self.filtered(filter_gtve):
            qrcode = record._edoc_processor().monta_qrcode(record.document_key)
            if record.cte40_infCTeSupl:
                record.cte40_infCTeSupl.qrcode = qrcode
            else:
                record.cte40_infCTeSupl = self.env[
                    "l10n_br_fiscal.document.supplement"
                ].create({"qrcode": qrcode})
        return result

    def _document_export(self, pretty_print=True):
        result = super()._document_export(pretty_print=pretty_print)
        for record in self.filtered(filter_gtve):
            record._check_gtve()
            record._document_qrcode()
            edoc = record._gtve_binding()
            signed_xml = record._edoc_processor().assina_raiz(edoc, edoc.infCte.Id)
            record.authorization_event_id = self.event_ids.create_event_save_xml(
                company_id=record.company_id,
                environment=(
                    EVENT_ENV_PROD if record.cte_environment == "1" else EVENT_ENV_HML
                ),
                event_type="0",
                xml_file=signed_xml,
                document_id=record,
            )
            record._validate_xml(signed_xml)
        return result

    def _validate_xml(self, xml_file):
        self.ensure_one()
        if not filter_gtve(self):
            return super()._validate_xml(xml_file)
        schema = importlib.resources.files(nfelib.__name__).joinpath(*GTVE_SCHEMA)
        with importlib.resources.as_file(schema) as schema_path:
            errors = Cte.schema_validation(xml_file, schema_path=str(schema_path))
        self.xml_error_message = "\n".join(errors) or False

    def _eletronic_document_send(self):
        result = super()._eletronic_document_send()
        for record in self.filtered(filter_gtve):
            if not record.xml_error_message:
                record._gtve_send()
        return result

    def _gtve_send(self):
        """Synchronous CTeRecepcaoGTVe web service (MOC 4.00, item 4.4)."""
        self.ensure_one()
        processor = self._edoc_processor()
        signed_xml = base64.b64decode(self.send_file_id.datas)
        process = processor._post(
            raiz=base64.b64encode(gzip.compress(signed_xml)).decode(),
            url=processor._get_ws_endpoint(WS_GTVE_RECEPCAO),
            operacao="cteRecepcaoGTVe",
            classe=RetGtve,
        )
        response = process.resposta
        protocol = response.protCTe and response.protCTe.infProt
        status = protocol or response
        self.write({"status_code": status.cStat, "status_name": status.xMotivo})
        if status.cStat in AUTORIZADO:
            self.authorization_event_id.set_done(
                status_code=protocol.cStat,
                response=protocol.xMotivo,
                protocol_date=tax_authority_date_to_utc(protocol.dhRecbto),
                protocol_number=protocol.nProt,
                file_response_xml=self._gtve_proc_xml(
                    signed_xml, process.retorno.content
                ),
            )
            self._change_state(SITUACAO_EDOC_AUTORIZADA)
        elif status.cStat in DENEGADO:
            self._change_state(SITUACAO_EDOC_DENEGADA)
        else:
            self._change_state(SITUACAO_EDOC_REJEITADA)

    def _gtve_proc_xml(self, signed_xml, response_xml):
        """GTVeProc: the signed GTV-e with its authorization protocol."""
        protocol = etree.fromstring(response_xml).xpath(
            "//cte:protCTe", namespaces={"cte": CTE_NS}
        )[0]
        proc = etree.Element(
            f"{{{CTE_NS}}}GTVeProc", versao=GTVE_VERSION, nsmap={None: CTE_NS}
        )
        proc.append(etree.fromstring(signed_xml))
        proc.append(protocol)
        return etree.tostring(proc, encoding="unicode")

    def _document_cancel(self, justificative):
        result = super()._document_cancel(justificative)
        for record in self.filtered(filter_gtve):
            # event 110111 through CTeRecepcaoEvento (MOC 4.00, item 3.7.1)
            record._cte_cancel()
        return result

    def _document_correction(self, justificative):
        # MOC 4.00, item 5: the correction letter is only for models 57 and 67
        if self.filtered(filter_gtve):
            raise UserError(_("The GTV-e has no correction letter."))
        return super()._document_correction(justificative)
