# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import gzip
import re
from datetime import datetime
from unittest import mock

from lxml import etree
from nfelib.bpe.bindings.v1_0.bpe_ta_v1_00 import BpeTa

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger

from odoo.addons.l10n_br_bpe.bpe_client.client import BpeClient

from ..models.document import BPE_TA_SCHEMA

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
    "<tpAmb>2</tpAmb><cUF>35</cUF><verAplic>SVRS-TESTE</verAplic>"
    "<cStat>100</cStat><xMotivo>Autorizado o uso do BP-e</xMotivo>"
    '<protBPe versao="1.00"><infProt>'
    "<tpAmb>2</tpAmb><verAplic>SVRS-TESTE</verAplic><chBPe>%(key)s</chBPe>"
    "<dhRecbto>2026-11-21T10:00:01-03:00</dhRecbto>"
    "<nProt>135260000000011</nProt>"
    "<digVal>bm90LWNoZWNrZWQtaW4tdGVzdHM=</digVal>"
    "<cStat>100</cStat><xMotivo>Autorizado o uso do BP-e</xMotivo>"
    "</infProt></protBPe></retBPe>"
)

RET_EVENTO = (
    '<retEventoBPe xmlns="http://www.portalfiscal.inf.br/bpe" versao="1.00">'
    "<infEvento><tpAmb>2</tpAmb><verAplic>SVRS-TESTE</verAplic><cOrgao>35</cOrgao>"
    "<cStat>135</cStat><xMotivo>Evento registrado</xMotivo><chBPe>%(key)s</chBPe>"
    "<tpEvento>%(event_type)s</tpEvento><xEvento>Evento</xEvento>"
    "<nSeqEvento>1</nSeqEvento><dhRegEvento>2026-11-21T10:05:00-03:00</dhRegEvento>"
    "<nProt>135260000000012</nProt></infEvento></retEventoBPe>"
)


@tagged("post_install", "-at_install")
class TestBpeTa(TransactionCase):
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
                "code": "3",
                "name": "BP-e TA",
                "document_type_id": document_type.id,
                "company_id": cls.company.id,
            }
        )
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": cls.company.id,
                "document_type_id": document_type.id,
                "document_serie_id": serie.id,
                "fiscal_operation_type": "out",
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_venda").id,
                "bpe_layout": "ta",
                "bpe_environment": "2",
                "document_date": datetime(2026, 11, 21, 13, 0, 0),
                "bpe_origin_city_id": cls.env.ref("l10n_br_base.city_3550308").id,
                "bpe_destination_city_id": cls.env.ref("l10n_br_base.city_3304557").id,
                "bpe10_dhEmb": datetime(2026, 11, 22, 11, 0, 0),
                "bpe10_dhValidade": datetime(2027, 11, 22, 11, 0, 0),
                "bpe_ta_iata_number": "1234567890",
                "bpe10_infPassageiro": cls.env["bpe.10.tbpe_infpassageiro"]
                .create(
                    {
                        "bpe10_xNome": "Passageiro de Teste",
                        "bpe10_tpDoc": "1",
                        "bpe10_nDoc": "123456789",
                    }
                )
                .id,
                "bpe_ta_flight_ids": [
                    Command.create(
                        {
                            "sequence": 1,
                            "flight_number": "1001",
                            "airline_code": "zz",
                            "origin_airport": "GRU",
                            "destination_airport": "BSB",
                            "leg_type": "2",
                            "departure_date": datetime(2026, 11, 22, 11, 0, 0),
                        }
                    ),
                    Command.create(
                        {
                            "sequence": 2,
                            "flight_number": "1002",
                            "airline_code": "ZZ",
                            "origin_airport": "BSB",
                            "destination_airport": "SDU",
                            "leg_type": "3",
                            "departure_date": datetime(2026, 11, 22, 15, 0, 0),
                            "connection_date": datetime(2026, 11, 22, 15, 0, 0),
                        }
                    ),
                ],
                "bpe10_pag": [
                    Command.create({"bpe10_tPag": "06", "bpe10_vPag": 530.0})
                ],
                "manual_customer_additional_data": "Bilhete aereo de teste",
            }
        )
        product = cls.env["product.product"].create(
            {"name": "Passagem aerea", "type": "service"}
        )
        for name, value, component in (
            ("Tarifa", 500.0, "01"),
            ("Taxa de embarque", 30.0, "03"),
        ):
            cls.env["l10n_br_fiscal.document.line"].create(
                {
                    "document_id": cls.document.id,
                    "product_id": product.id,
                    "name": name,
                    "quantity": 1.0,
                    "price_unit": value,
                    "fiscal_operation_type": "out",
                    "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_venda").id,
                    "fiscal_operation_line_id": cls.env.ref(
                        "l10n_br_fiscal.fo_venda_servico"
                    ).id,
                    "bpe_ta_component_type": component,
                }
            )
        cls.lines = cls.document.fiscal_line_ids

    def _signed_xml(self):
        attachment = self.document.authorization_event_id.file_request_id
        return base64.b64decode(attachment.datas).decode("utf-8")

    def _soap(self, service, content):
        return (SOAP_RESPONSE % {"service": service, "content": content}).encode()

    def test_xml_signed_and_valid(self):
        """The BP-e TA is signed, valid against bpeTA_v1.00.xsd and carries
        the flights, the IBSCBS group and the QR Code of SVRS."""
        self.document.action_document_confirm()
        self.assertFalse(self.document.xml_error_message)
        xml = self._signed_xml()
        self.assertEqual(BpeTa.schema_validation(xml, schema_path=BPE_TA_SCHEMA), [])
        tree = etree.fromstring(xml.encode())
        self.assertEqual(tree.tag, "{http://www.portalfiscal.inf.br/bpe}BPeTA")
        key = self.document.document_key

        def text(path):
            return tree.xpath(f"string({path})", namespaces=NS)

        self.assertEqual(text("//bpe:infBPe/@Id"), f"BPe{key}")
        self.assertEqual(text("//bpe:ide/bpe:modal"), "2")
        self.assertEqual(text("//bpe:ide/bpe:tpCompra"), "0")
        self.assertEqual(text("//bpe:ide/bpe:cMunIni"), "3550308")
        self.assertEqual(text("//bpe:ide/bpe:UFFim"), "RJ")
        self.assertEqual(text("//bpe:ide/bpe:nroBPIATA"), "1234567890")
        self.assertEqual(text("//bpe:infPassageiro/bpe:xNome"), "Passageiro de Teste")
        flights = tree.xpath("//bpe:infViagem", namespaces=NS)
        self.assertEqual(len(flights), 2)
        self.assertEqual(text("//bpe:infViagem[1]/bpe:SiglaCiaOperVoo"), "ZZ")
        self.assertEqual(text("//bpe:infViagem[1]/bpe:tpTrecho"), "2")
        self.assertEqual(text("//bpe:infViagem[2]/bpe:tpTrecho"), "3")
        self.assertTrue(text("//bpe:infViagem[2]/bpe:dhConexao"))
        self.assertEqual(text("//bpe:infValorBPe/bpe:vBP"), "530.00")
        self.assertEqual(text("//bpe:infValorBPe/bpe:Comp[2]/bpe:tpComp"), "03")
        # no ICMS in the BP-e TA: IBSCBS (required) and vTotDFe
        self.assertFalse(tree.xpath("//bpe:imp/bpe:ICMS", namespaces=NS))
        self.assertTrue(all(self.lines.mapped("cbs_value")))
        self.assertEqual(text("//bpe:imp/bpe:IBSCBS/bpe:cClassTrib"), "000001")
        self.assertEqual(
            text("//bpe:imp/bpe:IBSCBS/bpe:gIBSCBS/bpe:gCBS/bpe:vCBS"),
            f"{sum(self.lines.mapped('cbs_value')):.2f}",
        )
        # NT BP-e 2025.002 v2.00, rule F140: vTotDFe = vBP in 2026
        self.assertEqual(text("//bpe:imp/bpe:vTotDFe"), "530.00")
        self.assertEqual(text("//bpe:pag/bpe:tPag"), "06")
        self.assertEqual(
            text("//bpe:qrCodBPe"),
            f"https://dfe-portal.svrs.rs.gov.br/bpe/qrCode?chBPe={key}&tpAmb=2",
        )

    def test_flight_and_purchase_rules(self):
        """Rules of the NT BP-e 2025.002 v2.00 checked on confirmation."""
        flights = self.document.bpe_ta_flight_ids
        flights[1].leg_type = "1"
        with self.assertRaisesRegex(UserError, "Initial Leg"):
            self.document.action_document_confirm()
        flights[1].leg_type = "3"
        self.document.bpe_ta_purchase_type = "1"
        with self.assertRaisesRegex(UserError, "buyer"):
            self.document.action_document_confirm()
        self.document.bpe_ta_purchase_type = "0"
        self.document.bpe10_pag.bpe10_vPag = 400.0
        with self.assertRaisesRegex(UserError, "payments must add up"):
            self.document.action_document_confirm()

    def test_linked_to_multiple(self):
        """A purchase linked to a multiple BP-e carries the key of the multiple
        BP-e instead of values, taxes and payments (rules F53 and F54)."""
        self.document.write(
            {
                "bpe_ta_purchase_type": "2",
                "bpe_ta_multiple_key": "3526118158305400012963003000000001"
                "1000000017",
            }
        )
        self.document.action_document_confirm()
        self.assertFalse(self.document.xml_error_message)
        tree = etree.fromstring(self._signed_xml().encode())
        self.assertTrue(tree.xpath("//bpe:infBPeVinculado", namespaces=NS))
        self.assertFalse(tree.xpath("//bpe:infValorBPe", namespaces=NS))

    @mute_logger("brazil_fiscal_client.fiscal_client")
    def test_send_no_boarding_and_cancel(self):
        """Authorization by BPeRecepcaoTA and the events on SVRS, against a
        simulated authorizer."""
        self.document.action_document_confirm()
        key = self.document.document_key
        with mock.patch.object(
            BpeClient,
            "_post",
            return_value=self._soap("BPeRecepcaoTA", RET_BPE % {"key": key}),
        ) as post:
            self.document.action_document_send()
        self.assertEqual(
            post.call_args.args[0],
            "https://bpe-homologacao.svrs.rs.gov.br/WS/BPeRecepcaoTA/BPeRecepcaoTA.asmx",
        )
        headers = post.call_args.kwargs["headers"]
        self.assertIn("wsdl/BPeRecepcaoTA/bpeRecepcaoTA", headers["content-type"])
        sent = re.search(r"bpeDadosMsg[^>]*>([^<]+)<", post.call_args.kwargs["data"])
        sent_xml = gzip.decompress(base64.b64decode(sent.group(1))).decode()
        self.assertIn("<BPeTA", sent_xml)
        self.assertEqual(self.document.state_edoc, "autorizada")
        self.assertEqual(self.document.authorization_protocol, "135260000000011")

        def event_response(event_type):
            return self._soap(
                "BPeRecepcaoEvento",
                RET_EVENTO % {"key": key, "event_type": event_type},
            )

        with mock.patch.object(
            BpeClient, "_post", return_value=event_response("110115")
        ) as post:
            event = self.document._bpe_no_boarding("Passageiro nao embarcou")
        self.assertIn("bpe-homologacao.svrs.rs.gov.br", post.call_args.args[0])
        self.assertEqual(event.state, "done")

        with mock.patch.object(
            BpeClient, "_post", return_value=event_response("110111")
        ) as post:
            self.document._document_cancel("Cancelamento de teste do BP-e TA")
        self.assertIn("bpeRecepcaoEvento", post.call_args.args[0])
        self.assertEqual(self.document.state_edoc, "cancelada")
