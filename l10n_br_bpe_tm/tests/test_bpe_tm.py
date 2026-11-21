# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import gzip
import os
import re
from datetime import datetime
from unittest import mock

import nfelib
from lxml import etree
from nfelib.bpe.bindings.v1_0.bpe_tm_v1_00 import BpeTm
from nfelib.bpe.bindings.v1_0.proc_bpe_tm_v1_00 import BpeTmproc

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger

from odoo.addons.l10n_br_bpe.bpe_client.client import BpeClient

from ..models.document import BPE_TM_SCHEMA

NS = {"bpe": "http://www.portalfiscal.inf.br/bpe"}

PROC_SCHEMA = os.path.join(
    os.path.dirname(nfelib.__file__), "bpe", "schemas", "v1_0", "procBPeTM_v1.00.xsd"
)

SOAP_RESPONSE = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">'
    "<soap:Body>"
    '<bpeResultMsg xmlns="http://www.portalfiscal.inf.br/bpe/wsdl/%(service)s">'
    "%(content)s</bpeResultMsg></soap:Body></soap:Envelope>"
)

RET_BPE = (
    '<retBPe xmlns="http://www.portalfiscal.inf.br/bpe" versao="1.00">'
    "<tpAmb>2</tpAmb><cUF>31</cUF><verAplic>MG-TESTE</verAplic>"
    "<cStat>100</cStat><xMotivo>Autorizado o uso do BP-e</xMotivo>"
    '<protBPe versao="1.00"><infProt>'
    "<tpAmb>2</tpAmb><verAplic>MG-TESTE</verAplic><chBPe>%(key)s</chBPe>"
    "<dhRecbto>2026-11-21T10:00:01-03:00</dhRecbto>"
    "<nProt>131260000000001</nProt>"
    "<digVal>bm90LWNoZWNrZWQtaW4tdGVzdHM=</digVal>"
    "<cStat>100</cStat><xMotivo>Autorizado o uso do BP-e</xMotivo>"
    "</infProt></protBPe></retBPe>"
)

RET_EVENTO = (
    '<retEventoBPe xmlns="http://www.portalfiscal.inf.br/bpe" versao="1.00">'
    "<infEvento><tpAmb>2</tpAmb><verAplic>MG-TESTE</verAplic><cOrgao>31</cOrgao>"
    "<cStat>135</cStat><xMotivo>Evento registrado</xMotivo><chBPe>%(key)s</chBPe>"
    "<tpEvento>110111</tpEvento><xEvento>Cancelamento</xEvento>"
    "<nSeqEvento>1</nSeqEvento><dhRegEvento>2026-11-21T10:05:00-03:00</dhRegEvento>"
    "<nProt>131260000000002</nProt></infEvento></retEventoBPe>"
)


@tagged("post_install", "-at_install")
class TestBpeTm(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=True, tz="America/Sao_Paulo")
        )
        # The BP-e TM is authorized by MG and SVRS only (Portal BP-e): the
        # demo company moves to Belo Horizonte, keeping its demo IE
        cls.env["ir.config_parameter"].sudo().set_param(
            "l10n_br_base.disable_ie_validation", True
        )
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.company.write(
            {
                "state_id": cls.env.ref("base.state_br_mg").id,
                "city_id": cls.env.ref("l10n_br_base.city_3106200").id,
                "processador_edoc": "oca",
                "bpe_environment": "2",
                "bpe_tm_tar": "TAR123",
            }
        )
        document_type = cls.env.ref("l10n_br_fiscal.document_63")
        serie = cls.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "2",
                "name": "BP-e TM",
                "document_type_id": document_type.id,
                "company_id": cls.company.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Viagem metropolitana", "type": "service"}
        )
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": cls.company.id,
                "document_type_id": document_type.id,
                "document_serie_id": serie.id,
                "fiscal_operation_type": "out",
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_venda").id,
                "bpe_layout": "tm",
                "bpe_environment": "2",
                "document_date": datetime(2026, 11, 21, 13, 0, 0),
            }
        )
        bh = cls.env.ref("l10n_br_base.city_3106200")
        contagem = cls.env.ref("l10n_br_base.city_3118601")
        trips = [
            # equipment, trip, passengers, fare, components
            (1, 0, 40, 4.5, [("VT", 30), ("ISENTOS", 10)]),
            (1, 0, 20, 4.5, [("DINHEIRO", 20)]),
            (2, 7, 10, 5.0, [("CARTAO", 10)]),
        ]
        for equipment, trip, passengers, fare, components in trips:
            line = cls.env["l10n_br_fiscal.document.line"].create(
                {
                    "document_id": cls.document.id,
                    "product_id": cls.product.id,
                    "name": cls.product.name,
                    "quantity": passengers,
                    "price_unit": fare,
                    "fiscal_operation_type": "out",
                    "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_venda").id,
                    "fiscal_operation_line_id": cls.env.ref(
                        "l10n_br_fiscal.fo_venda_servico"
                    ).id,
                    "bpe_tm_equipment": equipment,
                    "bpe_tm_plate": "ABC-1D23",
                    "bpe_tm_line_prefix": f"L{equipment}",
                    "bpe_tm_trip": trip,
                    "bpe_tm_start_city_id": bh.id,
                    "bpe_tm_end_city_id": contagem.id,
                    "bpe_tm_component_ids": [
                        Command.create({"name": name, "quantity": quantity})
                        for name, quantity in components
                    ],
                }
            )
            line.icms_tax_id = cls.env.ref("l10n_br_fiscal.tax_icms_12")
            line.cfop_id = cls.env.ref("l10n_br_fiscal.cfop_5357")
        cls.lines = cls.document.fiscal_line_ids

    def _signed_xml(self):
        attachment = self.document.authorization_event_id.file_request_id
        return base64.b64decode(attachment.datas).decode("utf-8")

    def _soap(self, service, content):
        return (SOAP_RESPONSE % {"service": service, "content": content}).encode()

    def test_xml_signed_and_valid(self):
        """The BP-e TM is signed, valid against bpeTM_v1.00.xsd and groups the
        trips by counter equipment (NT BP-e 2020.002 v1.01)."""
        self.assertEqual(self.document.bpe_tm_cfop_id.code, "5357")
        self.document.action_document_confirm()
        self.assertFalse(self.document.xml_error_message)
        xml = self._signed_xml()
        self.assertEqual(
            etree.fromstring(xml.encode()).tag,
            "{http://www.portalfiscal.inf.br/bpe}BPeTM",
        )
        self.assertEqual(BpeTm.schema_validation(xml, schema_path=BPE_TM_SCHEMA), [])
        tree = etree.fromstring(xml.encode())
        key = self.document.document_key

        def text(path):
            return tree.xpath(f"string({path})", namespaces=NS)

        self.assertEqual(text("//bpe:infBPe/@Id"), f"BPe{key}")
        self.assertEqual(key[:2], "31")
        self.assertEqual(text("//bpe:ide/bpe:tpBPe"), "4")
        self.assertEqual(text("//bpe:ide/bpe:dCompet"), "2026-11-21")
        self.assertEqual(text("//bpe:ide/bpe:CFOP"), "5357")
        self.assertEqual(text("//bpe:emit/bpe:TAR"), "TAR123")
        self.assertFalse(tree.xpath("//bpe:infBPeSupl", namespaces=NS))
        groups = tree.xpath("//bpe:detBPeTM", namespaces=NS)
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0].get("idEqpCont"), "1")
        self.assertEqual(
            [det.get("nViagem") for det in groups[0].xpath("bpe:det", namespaces=NS)],
            ["1", "2"],
        )
        self.assertEqual(
            groups[1].xpath("string(bpe:det/@nViagem)", namespaces=NS), "7"
        )
        self.assertEqual(text("//bpe:detBPeTM[1]/bpe:UFIniViagem"), "MG")
        self.assertEqual(text("//bpe:detBPeTM[1]/bpe:placa"), "ABC1D23")
        first = "//bpe:detBPeTM[1]/bpe:det[1]"
        self.assertEqual(text(f"{first}/bpe:cMunIni"), "3106200")
        self.assertEqual(text(f"{first}/bpe:cMunFim"), "3118601")
        self.assertEqual(text(f"{first}/bpe:qPass"), "40")
        self.assertEqual(text(f"{first}/bpe:vBP"), "180.00")
        self.assertEqual(
            text(f"{first}/bpe:imp/bpe:ICMS/bpe:ICMS00/bpe:vICMS"), "21.60"
        )
        self.assertEqual(text(f"{first}/bpe:Comp[2]/bpe:xNome"), "ISENTOS")
        self.assertEqual(text(f"{first}/bpe:Comp[2]/bpe:qComp"), "00010")
        # IBS and CBS by trip (NT 2025.001 RTC) and their totals
        line = self.lines[0]
        self.assertTrue(line.ibs_value and line.cbs_value)
        self.assertEqual(text(f"{first}/bpe:imp/bpe:IBSCBS/bpe:CST"), "000")
        self.assertEqual(
            text(f"{first}/bpe:imp/bpe:IBSCBS/bpe:gIBSCBS/bpe:gCBS/bpe:vCBS"),
            f"{line.cbs_value:.2f}",
        )
        self.assertEqual(text("//bpe:total/bpe:qPass"), "70")
        self.assertEqual(text("//bpe:total/bpe:vBP"), "320.00")
        self.assertEqual(text("//bpe:total/bpe:ICMSTot/bpe:vICMS"), "38.40")
        self.assertEqual(
            text("//bpe:total/bpe:IBSCBSTot/bpe:gCBS/bpe:vCBS"),
            f"{sum(self.lines.mapped('cbs_value')):.2f}",
        )
        # NT BP-e 2026.004 v1.01: vTotDFe = vBP in 2026
        self.assertEqual(text("//bpe:total/bpe:vTotDFe"), "320.00")

    def test_trip_rules(self):
        """Trip rules of the NT BP-e 2020.002 v1.01 checked on confirmation."""
        line = self.lines[0]
        line.bpe_tm_component_ids[0].quantity = 10
        with self.assertRaisesRegex(UserError, "components quantities"):
            self.document.action_document_confirm()
        line.bpe_tm_component_ids[0].quantity = 30
        line.write({"bpe_tm_counter_start": "500", "bpe_tm_counter_end": "400"})
        with self.assertRaisesRegex(UserError, "end counter"):
            self.document.action_document_confirm()
        line.write({"bpe_tm_counter_start": False, "bpe_tm_counter_end": False})
        self.company.bpe_tm_tar = False
        with self.assertRaisesRegex(UserError, "TAR"):
            self.document.action_document_confirm()

    def test_authorizer_without_tm_service(self):
        """SP publishes no BPeRecepcaoTM on the Portal BP-e."""
        self.company.write(
            {
                "state_id": self.env.ref("base.state_br_sp").id,
                "city_id": self.env.ref("l10n_br_base.city_3550308").id,
            }
        )
        with self.assertRaisesRegex(UserError, "BPeRecepcaoTM"):
            self.document.action_document_confirm()

    @mute_logger("brazil_fiscal_client.fiscal_client")
    def test_send_and_cancel(self):
        """Authorization by BPeRecepcaoTM and cancel event, against a
        simulated authorizer; the BP-e TM has no no boarding event."""
        self.document.action_document_confirm()
        key = self.document.document_key
        with mock.patch.object(
            BpeClient,
            "_post",
            return_value=self._soap("BPeRecepcaoTM", RET_BPE % {"key": key}),
        ) as post:
            self.document.action_document_send()
        self.assertEqual(
            post.call_args.args[0],
            "https://hbpe.fazenda.mg.gov.br/bpe/services/BPeRecepcaoTM",
        )
        headers = post.call_args.kwargs["headers"]
        self.assertIn("wsdl/BPeRecepcaoTM/bpeRecepcaoTM", headers["content-type"])
        sent = re.search(r"bpeDadosMsg[^>]*>([^<]+)<", post.call_args.kwargs["data"])
        sent_xml = gzip.decompress(base64.b64decode(sent.group(1))).decode()
        self.assertIn("<BPeTM", sent_xml)
        self.assertEqual(self.document.state_edoc, "autorizada")
        self.assertEqual(self.document.authorization_protocol, "131260000000001")
        proc = base64.b64decode(
            self.document.authorization_event_id.file_response_id.datas
        ).decode()
        self.assertTrue(proc.startswith("<bpeTMProc "))
        self.assertEqual(BpeTmproc.schema_validation(proc, schema_path=PROC_SCHEMA), [])

        with self.assertRaisesRegex(UserError, "no boarding"):
            self.document._bpe_no_boarding("Nao se aplica")

        with mock.patch.object(
            BpeClient,
            "_post",
            return_value=self._soap("BPeRecepcaoEvento", RET_EVENTO % {"key": key}),
        ) as post:
            self.document._document_cancel("Cancelamento de teste do BP-e TM")
        self.assertIn("BPeRecepcaoEvento", post.call_args.args[0])
        self.assertIn("ID110111", post.call_args.kwargs["data"])
        self.assertEqual(self.document.state_edoc, "cancelada")
