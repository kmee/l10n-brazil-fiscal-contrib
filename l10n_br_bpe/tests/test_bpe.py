# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import gzip
import re
from datetime import datetime
from unittest import mock

from lxml import etree
from nfelib.bpe.bindings.v1_0.bpe_v1_00 import Bpe

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger

from ..bpe_client.client import BpeClient

NS = {"bpe": "http://www.portalfiscal.inf.br/bpe"}

SOAP_RESPONSE = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">'
    "<soap:Body>"
    '<bpeResultMsg xmlns="http://www.portalfiscal.inf.br/bpe/wsdl/%(service)s">'
    "%(content)s</bpeResultMsg></soap:Body></soap:Envelope>"
)

RET_BPE = (
    '<retBPe xmlns="http://www.portalfiscal.inf.br/bpe" versao="1.00">'
    "<tpAmb>2</tpAmb><cUF>35</cUF><verAplic>SP-TESTE</verAplic>"
    "<cStat>100</cStat><xMotivo>Autorizado o uso do BP-e</xMotivo>"
    '<protBPe versao="1.00"><infProt>'
    "<tpAmb>2</tpAmb><verAplic>SP-TESTE</verAplic><chBPe>%(key)s</chBPe>"
    "<dhRecbto>2026-11-21T10:00:01-03:00</dhRecbto>"
    "<nProt>135260000000001</nProt>"
    "<digVal>bm90LWNoZWNrZWQtaW4tdGVzdHM=</digVal>"
    "<cStat>100</cStat><xMotivo>Autorizado o uso do BP-e</xMotivo>"
    "</infProt></protBPe></retBPe>"
)

RET_EVENTO = (
    '<retEventoBPe xmlns="http://www.portalfiscal.inf.br/bpe" versao="1.00">'
    "<infEvento><tpAmb>2</tpAmb><verAplic>SP-TESTE</verAplic><cOrgao>35</cOrgao>"
    "<cStat>%(status)s</cStat><xMotivo>%(reason)s</xMotivo><chBPe>%(key)s</chBPe>"
    "<tpEvento>%(event_type)s</tpEvento><xEvento>Evento</xEvento>"
    "<nSeqEvento>1</nSeqEvento><dhRegEvento>2026-11-21T10:05:00-03:00</dhRegEvento>"
    "<nProt>135260000000002</nProt></infEvento></retEventoBPe>"
)


@tagged("post_install", "-at_install")
class TestBpe(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=True, tz="America/Sao_Paulo")
        )
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.company.processador_edoc = "oca"
        cls.company.bpe_environment = "2"
        document_type = cls.env.ref("l10n_br_fiscal.document_63")
        serie = cls.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "1",
                "name": "BP-e",
                "document_type_id": document_type.id,
                "company_id": cls.company.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Passagem Sao Paulo x Rio de Janeiro", "type": "service"}
        )
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": cls.company.id,
                "document_type_id": document_type.id,
                "document_serie_id": serie.id,
                "fiscal_operation_type": "out",
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_venda").id,
                "bpe_environment": "2",
                "document_date": datetime(2026, 11, 21, 13, 0, 0),
                "bpe_origin_city_id": cls.env.ref("l10n_br_base.city_3550308").id,
                "bpe_destination_city_id": cls.env.ref("l10n_br_base.city_3304557").id,
                "bpe10_dhEmb": datetime(2026, 11, 22, 11, 0, 0),
                "bpe10_dhValidade": datetime(2027, 11, 22, 11, 0, 0),
                "bpe10_infPassageiro": cls.env["bpe.10.tbpe_infpassageiro"]
                .create(
                    {
                        "bpe10_xNome": "Passageiro de Teste",
                        "bpe10_tpDoc": "1",
                        "bpe10_nDoc": "123456789",
                    }
                )
                .id,
                "bpe10_infViagem": [
                    Command.create(
                        {
                            "bpe10_cPercurso": "SP-RJ",
                            "bpe10_xPercurso": "Sao Paulo x Rio de Janeiro",
                            "bpe10_tpViagem": "00",
                            "bpe10_tpServ": "1",
                            "bpe10_tpAcomodacao": "1",
                            "bpe10_tpTrecho": "1",
                            "bpe10_dhViagem": datetime(2026, 11, 22, 11, 0, 0),
                            "bpe10_poltrona": "12",
                        }
                    )
                ],
                "bpe10_pag": [
                    Command.create({"bpe10_tPag": "01", "bpe10_vPag": 120.0})
                ],
                "manual_customer_additional_data": "Bilhete de teste",
            }
        )
        line = cls.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": cls.document.id,
                "product_id": cls.product.id,
                "name": cls.product.name,
                "quantity": 1.0,
                "price_unit": 120.0,
                "fiscal_operation_type": "out",
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_venda").id,
                "fiscal_operation_line_id": cls.env.ref(
                    "l10n_br_fiscal.fo_venda_servico"
                ).id,
            }
        )
        # IBS and CBS come from the operation line (cClassTrib 000001)
        line.icms_tax_id = cls.env.ref("l10n_br_fiscal.tax_icms_12")
        cls.line = line

    def _signed_xml(self):
        attachment = self.document.authorization_event_id.file_request_id
        return base64.b64decode(attachment.datas).decode("utf-8")

    def _soap(self, service, content):
        return (SOAP_RESPONSE % {"service": service, "content": content}).encode()

    def test_xml_signed_and_valid(self):
        """The BP-e is signed, valid against the XSD and has the main groups."""
        self.document.action_document_confirm()
        self.assertFalse(self.document.xml_error_message)
        xml = self._signed_xml()
        self.assertEqual(Bpe.schema_validation(xml), [])
        tree = etree.fromstring(xml.encode())
        self.assertTrue(
            tree.xpath(
                "//ds:Signature",
                namespaces={"ds": "http://www.w3.org/2000/09/xmldsig#"},
            )
        )
        key = self.document.document_key
        self.assertEqual(len(key), 44)
        self.assertEqual(key[20:22], "63")

        def text(path):
            return tree.xpath(f"string({path})", namespaces=NS)

        self.assertEqual(text("//bpe:infBPe/@Id"), f"BPe{key}")
        self.assertEqual(text("//bpe:ide/bpe:mod"), "63")
        self.assertEqual(text("//bpe:ide/bpe:cMunIni"), "3550308")
        self.assertEqual(text("//bpe:ide/bpe:UFFim"), "RJ")
        self.assertEqual(text("//bpe:emit/bpe:CNPJ"), "81583054000129")
        self.assertEqual(text("//bpe:infPassagem/bpe:xLocDest"), "Rio de Janeiro")
        self.assertEqual(text("//bpe:infValorBPe/bpe:vBP"), "120.00")
        self.assertEqual(text("//bpe:infValorBPe/bpe:Comp/bpe:vComp"), "120.00")
        self.assertEqual(text("//bpe:imp/bpe:ICMS/bpe:ICMS00/bpe:vICMS"), "14.40")
        # IBS/CBS (NT 2025.001 RTC) and vTotDFe = vBP in 2026 (NT 2026.004)
        line = self.line
        self.assertTrue(line.ibs_value and line.cbs_value)
        self.assertEqual(text("//bpe:IBSCBS/bpe:CST"), "000")
        self.assertEqual(text("//bpe:IBSCBS/bpe:cClassTrib"), "000001")
        self.assertEqual(text("//bpe:gIBSCBS/bpe:vBC"), f"{line.ibs_base:.2f}")
        self.assertEqual(text("//bpe:gIBSUF/bpe:pIBSUF"), "0.1000")
        self.assertEqual(text("//bpe:gIBSUF/bpe:vIBSUF"), f"{line.ibs_value:.2f}")
        self.assertEqual(text("//bpe:gIBSMun/bpe:vIBSMun"), "0.00")
        self.assertEqual(text("//bpe:gCBS/bpe:pCBS"), "0.9000")
        self.assertEqual(text("//bpe:gCBS/bpe:vCBS"), f"{line.cbs_value:.2f}")
        self.assertEqual(text("//bpe:imp/bpe:vTotDFe"), "120.00")
        self.assertEqual(text("//bpe:infAdic/bpe:infCpl"), "Bilhete de teste")
        self.assertEqual(
            text("//bpe:qrCodBPe"),
            "https://homologacao.bpe.fazenda.sp.gov.br/BPe/qrcode"
            f"?chBPe={key}&tpAmb=2",
        )

    def test_vtotdfe_from_2027(self):
        """From 2027 on vTotDFe adds IBS and CBS to vBP (NT 2026.004 v1.01)."""
        self.assertEqual(self.document.bpe10_vTotDFe, 120.0)
        self.document.document_date = datetime(2027, 1, 1, 3, 0, 0)
        self.assertAlmostEqual(
            self.document.bpe10_vTotDFe,
            120.0 + self.line.ibs_value + self.line.cbs_value,
        )

    def test_interstate_requires_passenger(self):
        """The passenger is identified in the interstate trip (MOC rule 211)."""
        self.document.bpe10_infPassageiro = False
        with self.assertRaisesRegex(UserError, "Passenger"):
            self.document.action_document_confirm()

    @mute_logger("brazil_fiscal_client.fiscal_client")
    def test_send_cancel_and_no_boarding(self):
        """Authorization, then the no boarding and the cancel events, against
        a simulated authorizer."""
        self.document.action_document_confirm()
        key = self.document.document_key
        with mock.patch.object(
            BpeClient,
            "_post",
            return_value=self._soap("BPeRecepcao", RET_BPE % {"key": key}),
        ) as post:
            self.document.action_document_send()
        location = post.call_args.args[0]
        self.assertIn("homologacao.bpe.fazenda.sp.gov.br", location)
        headers = post.call_args.kwargs["headers"]
        self.assertIn("BPeRecepcao/bpeRecepcao", headers["content-type"])
        sent = re.search(r"bpeDadosMsg[^>]*>([^<]+)<", post.call_args.kwargs["data"])
        sent_xml = gzip.decompress(base64.b64decode(sent.group(1))).decode()
        self.assertIn(f'Id="BPe{key}"', sent_xml)
        self.assertEqual(self.document.state_edoc, "autorizada")
        self.assertEqual(self.document.authorization_protocol, "135260000000001")

        def event_response(status, reason, event_type):
            return self._soap(
                "BPeRecepcaoEvento",
                RET_EVENTO
                % {
                    "status": status,
                    "reason": reason,
                    "key": key,
                    "event_type": event_type,
                },
            )

        with mock.patch.object(
            BpeClient,
            "_post",
            return_value=event_response("135", "Evento registrado", "110115"),
        ) as post:
            event = self.document._bpe_no_boarding("Passageiro nao embarcou")
        self.assertIn("ID110115", post.call_args.kwargs["data"])
        self.assertEqual(event.state, "done")
        self.assertEqual(self.document.state_edoc, "autorizada")

        # a refusal keeps the document authorized and the event recorded
        with mock.patch.object(
            BpeClient,
            "_post",
            return_value=event_response("220", "Rejeicao: prazo", "110111"),
        ):
            self.document._document_cancel("Cancelamento de teste do BP-e")
        self.assertEqual(self.document.state_edoc, "autorizada")
        self.assertEqual(self.document.cancel_event_id.status_code, "220")

        with mock.patch.object(
            BpeClient,
            "_post",
            return_value=event_response("135", "Evento registrado", "110111"),
        ) as post:
            self.document._document_cancel("Cancelamento de teste do BP-e")
        self.assertIn(
            "<descEvento>Cancelamento</descEvento>", post.call_args.kwargs["data"]
        )
        self.assertEqual(self.document.state_edoc, "cancelada")
        self.assertEqual(self.document.cancel_event_id.state, "done")
