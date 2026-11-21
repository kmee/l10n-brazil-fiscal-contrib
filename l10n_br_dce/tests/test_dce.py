# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import re
from datetime import datetime
from unittest import mock

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger

from odoo.addons.l10n_br_dce_spec.bindings.v1_0.dce_v1_00 import Dce

from ..constants import DCE_DECLARATION_1, DCE_SCHEMAS
from ..dce_client.client import DceClient

NS = {"dce": "http://www.portalfiscal.inf.br/dce"}

SOAP_RESPONSE = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">'
    "<soap:Body>"
    '<%(result)s xmlns="http://www.portalfiscal.inf.br/dce/wsdl/%(service)s">'
    "%(content)s</%(result)s></soap:Body></soap:Envelope>"
)

RET_DCE = (
    '<retDCe xmlns="http://www.portalfiscal.inf.br/dce" versao="1.00">'
    "<tpAmb>2</tpAmb><verAplic>PR-TESTE</verAplic>"
    "<cStat>100</cStat><xMotivo>Autorizado o uso do DCe</xMotivo>"
    "<cUF>41</cUF><dhRecbto>2026-11-21T10:00:01-03:00</dhRecbto>"
    '<protDCe versao="1.00"><infProt>'
    "<tpAmb>2</tpAmb><verAplic>PR-TESTE</verAplic><chDCe>%(key)s</chDCe>"
    "<dhRecbto>2026-11-21T10:00:01-03:00</dhRecbto>"
    "<nProt>341260000000001</nProt>"
    "<digVal>bm90LWNoZWNrZWQtaW4tdGVzdHM=</digVal>"
    "<cStat>100</cStat><xMotivo>Autorizado o uso do DCe</xMotivo>"
    "</infProt></protDCe></retDCe>"
)

RET_EVENTO = (
    '<retEventoDCe xmlns="http://www.portalfiscal.inf.br/dce" versao="1.00">'
    "<infEvento><tpAmb>2</tpAmb><verAplic>PR-TESTE</verAplic><cOrgao>35</cOrgao>"
    "<cStat>%(status)s</cStat><xMotivo>%(reason)s</xMotivo><chDCe>%(key)s</chDCe>"
    "<tpEvento>110111</tpEvento><xEvento>Cancelamento</xEvento>"
    "<nSeqEvento>1</nSeqEvento><dhRegEvento>2026-11-21T10:05:00-03:00</dhRegEvento>"
    "<nProt>341260000000002</nProt></infEvento></retEventoDCe>"
)


@tagged("post_install", "-at_install")
class TestDce(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=True, tz="America/Sao_Paulo")
        )
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.company.write(
            {
                "processador_edoc": "oca",
                "dce_environment": "2",
                "dce_issuer_type": "1",
                "dce_marketplace_site": "https://loja.example.com",
            }
        )
        cls.document_type = cls.env.ref("l10n_br_dce.document_99")
        serie = cls.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "1",
                "name": "DC-e",
                "document_type_id": cls.document_type.id,
                "company_id": cls.company.id,
            }
        )
        address = {
            "country_id": cls.env.ref("base.br").id,
            "street_name": "Rua de Teste",
            "street_number": "100",
            "district": "Centro",
            "zip": "01001-000",
        }
        cls.sender = cls.env["res.partner"].create(
            {
                **address,
                "name": "Remetente Pessoa Fisica",
                "is_company": False,
                "vat": "714.269.531-51",
                "ind_ie_dest": "9",
                "state_id": cls.env.ref("base.state_br_sp").id,
                "city_id": cls.env.ref("l10n_br_base.city_3550308").id,
            }
        )
        cls.recipient = cls.env["res.partner"].create(
            {
                **address,
                "name": "Destinatario Teste Ltda",
                "is_company": True,
                "vat": "71.953.842/0001-06",
                "email": "destinatario@example.com",
                "state_id": cls.env.ref("base.state_br_rj").id,
                "city_id": cls.env.ref("l10n_br_base.city_3304557").id,
                "zip": "20010-000",
            }
        )
        product = cls.env["product.product"].create(
            {"name": "Livro usado", "type": "consu"}
        )
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": cls.company.id,
                "document_type_id": cls.document_type.id,
                "document_serie_id": serie.id,
                "fiscal_operation_type": "out",
                "partner_id": cls.recipient.id,
                "dce_environment": "2",
                "dce_issuer_type": "1",
                "dce_sender_id": cls.sender.id,
                "dce10_modTrans": "1",
                "document_date": datetime(2026, 11, 21, 13, 0, 0),
                "manual_customer_additional_data": "Envio de teste",
            }
        )
        cls.line = cls.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": cls.document.id,
                "product_id": product.id,
                "name": product.name,
                "quantity": 2.0,
                "price_unit": 35.5,
                "fiscal_operation_type": "out",
                "ncm_id": cls.env.ref("l10n_br_fiscal.ncm_94031000").id,
            }
        )

    def _signed_xml(self):
        attachment = self.document.authorization_event_id.file_request_id
        return base64.b64decode(attachment.datas).decode("utf-8")

    def _soap(self, service, result, content):
        return (
            SOAP_RESPONSE % {"service": service, "result": result, "content": content}
        ).encode()

    def _tree(self):
        self.document.action_document_confirm()
        self.assertFalse(self.document.xml_error_message)
        xml = self._signed_xml()
        self.assertEqual(Dce.schema_validation(xml, schema_path=DCE_SCHEMAS["dce"]), [])
        return etree.fromstring(xml.encode())

    def test_marketplace_xml_signed_and_valid(self):
        """A DC-e issued by a marketplace on behalf of a person is signed,
        valid against the xsd and has the main groups."""
        tree = self._tree()
        self.assertTrue(
            tree.xpath(
                "//ds:Signature",
                namespaces={"ds": "http://www.w3.org/2000/09/xmldsig#"},
            )
        )

        def text(path):
            return tree.xpath(f"string({path})", namespaces=NS)

        # NT 2024.001 v1.30, item 3.1: cUF, AAMM, CNPJ, mod, serie, nDC,
        # tpEmis, tpEmit, nSiteAutoriz, cDC and cDV
        key = self.document.document_key
        self.assertEqual(len(key), 44)
        self.assertEqual(key[:2], "35")
        self.assertEqual(key[2:6], "2611")
        self.assertEqual(key[6:20], re.sub(r"\D", "", self.company.vat))
        self.assertEqual(key[20:25], "99001")
        self.assertEqual(key[34:37], "110")
        self.assertEqual(key[37:43], self.document.key_random_code)
        self.assertEqual(text("//dce:infDCe/@Id"), f"DCe{key}")
        self.assertEqual(text("//dce:ide/dce:mod"), "99")
        self.assertEqual(text("//dce:ide/dce:tpEmit"), "1")
        self.assertEqual(text("//dce:ide/dce:cDV"), key[-1])
        self.assertEqual(text("//dce:emit/dce:CPF"), "71426953151")
        self.assertEqual(text("//dce:emit/dce:enderEmit/dce:UF"), "SP")
        self.assertEqual(text("//dce:Marketplace/dce:Site"), "https://loja.example.com")
        self.assertFalse(tree.xpath("//dce:Transportadora", namespaces=NS))
        self.assertEqual(text("//dce:dest/dce:CNPJ"), "71953842000106")
        self.assertEqual(
            text("//dce:dest/dce:xNome"), "DCE EMITIDA EM AMBIENTE DE HOMOLOGACAO"
        )
        self.assertEqual(text("//dce:det/@nItem"), "1")
        self.assertEqual(text("//dce:prod/dce:NCM"), "94031000")
        self.assertEqual(text("//dce:prod/dce:qCom"), "2.0000")
        self.assertEqual(text("//dce:prod/dce:vUnCom"), "35.50")
        self.assertEqual(text("//dce:prod/dce:vProd"), "71.00")
        self.assertEqual(text("//dce:total/dce:vDC"), "71.00")
        self.assertEqual(text("//dce:transp/dce:modTrans"), "1")
        self.assertEqual(text("//dce:infAdic/dce:infCpl"), "Envio de teste")
        self.assertEqual(text("//dce:infDec/dce:xObs1"), DCE_DECLARATION_1)
        self.assertEqual(
            text("//dce:qrCodDCe"),
            f"https://www.fazenda.pr.gov.br/dce/qrcode?chDCe={key}&tpAmb=2",
        )

    def test_own_issuer(self):
        """In its own DC-e the company is the emit, with no issuer group, and
        an ICMS taxpayer is refused (MOC DC-e, Anexo I, rule C02-30)."""
        self.document.dce_issuer_type = "2"
        partner = self.company.partner_id
        partner.ind_ie_dest = "1"
        with self.assertRaisesRegex(UserError, "ICMS taxpayer"):
            self.document.action_document_confirm()
        partner.ind_ie_dest = "9"
        self.document.document_key = False
        tree = self._tree()
        cnpj = re.sub(r"\D", "", self.company.vat)
        self.assertEqual(tree.xpath("string(//dce:emit/dce:CNPJ)", namespaces=NS), cnpj)
        self.assertEqual(tree.xpath("string(//dce:ide/dce:tpEmit)", namespaces=NS), "2")
        self.assertFalse(tree.xpath("//dce:Marketplace", namespaces=NS))

    @mute_logger("brazil_fiscal_client.fiscal_client")
    def test_send_and_cancel(self):
        """Authorization and the cancel event against a simulated authorizer."""
        self.document.action_document_confirm()
        key = self.document.document_key
        with mock.patch.object(
            DceClient,
            "_post",
            return_value=self._soap(
                "DCeAutorizacao", "dceAutorizacaoResult", RET_DCE % {"key": key}
            ),
        ) as post:
            self.document.action_document_send()
        self.assertEqual(
            post.call_args.args[0],
            "https://homologacao.dce.fazenda.pr.gov.br/dce/DCeAutorizacao",
        )
        headers = post.call_args.kwargs["headers"]
        self.assertIn("DCeAutorizacao/dceAutorizacao", headers["content-type"])
        sent = post.call_args.kwargs["data"]
        self.assertRegex(sent, r"<(\w+:)?dceDadosMsg[^>]*><DCe ")
        self.assertIn(f'Id="DCe{key}"', sent)
        self.assertEqual(self.document.state_edoc, "autorizada")
        self.assertEqual(self.document.authorization_protocol, "341260000000001")

        def event_response(status, reason):
            return self._soap(
                "DCeRecepcaoEvento",
                "dceRecepcaoEventoResult",
                RET_EVENTO % {"status": status, "reason": reason, "key": key},
            )

        # a refusal keeps the document authorized and the event recorded
        with mock.patch.object(
            DceClient, "_post", return_value=event_response("501", "Rejeicao: prazo")
        ):
            self.document._document_cancel("Cancelamento de teste da DC-e")
        self.assertEqual(self.document.state_edoc, "autorizada")
        self.assertEqual(self.document.cancel_event_id.status_code, "501")

        with mock.patch.object(
            DceClient,
            "_post",
            return_value=event_response("135", "Cancelamento homologado"),
        ) as post:
            self.document._document_cancel("Cancelamento de teste da DC-e")
        sent = post.call_args.kwargs["data"]
        self.assertIn(f"ID110111{key}001", sent)
        self.assertIn("<CPFUsEmit>71426953151</CPFUsEmit>", sent)
        self.assertIn("<descEvento>Cancelamento</descEvento>", sent)
        self.assertEqual(self.document.state_edoc, "cancelada")
        self.assertEqual(self.document.cancel_event_id.state, "done")
