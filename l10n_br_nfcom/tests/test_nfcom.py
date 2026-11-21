# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from ..models.nfcom.document import key_check_digit

NS = {"n": "http://www.portalfiscal.inf.br/nfcom"}


@tagged("post_install", "-at_install")
class TestNFCom(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=True, tz="America/Sao_Paulo")
        )
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        if cls.company.processador_edoc != "oca":
            cls.company.processador_edoc = "oca"
        cls.document_type = cls.env.ref("l10n_br_nfcom.document_62")
        serie = cls.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "1",
                "name": "NFCom 1",
                "document_type_id": cls.document_type.id,
                "company_id": cls.company.id,
            }
        )
        partner = cls.env["res.partner"].create(
            {
                "name": "Cliente NFCom",
                "legal_name": "Cliente NFCom Ltda",
                "is_company": True,
                "vat": "45.723.174/0001-10",
                "ind_ie_dest": "9",
                "street_name": "Rua Teste",
                "street_number": "10",
                "district": "Centro",
                "zip": "01001-000",
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.env.ref("base.state_br_sp").id,
                "city_id": cls.env.ref("l10n_br_base.city_3550308").id,
            }
        )
        product = cls.env["product.product"].create(
            {
                "name": "Plano de internet",
                "default_code": "NET100",
                "nfcom_cclass": "0100101",
            }
        )
        operation = cls.env.ref("l10n_br_fiscal.fo_venda")
        operation_line = cls.env.ref("l10n_br_fiscal.fo_venda_venda")
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": cls.company.id,
                "partner_id": partner.id,
                "document_type_id": cls.document_type.id,
                "document_serie_id": serie.id,
                "fiscal_operation_type": "out",
                "fiscal_operation_id": operation.id,
                "nfcom10_iCodAssinante": "123",
                "nfcom10_tpAssinante": "1",
                "nfcom10_tpServUtil": "4",
                "fiscal_line_ids": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "name": "Plano de internet 100 MB",
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "fiscal_operation_id": operation.id,
                            "fiscal_operation_line_id": operation_line.id,
                        }
                    )
                ],
            }
        )
        # Taxes of the fiscal engine set after the operation line mapping
        cls.document.fiscal_line_ids.write(
            {
                "cfop_id": cls.env.ref("l10n_br_fiscal.cfop_5307").id,
                "tax_classification_id": cls.env.ref(
                    "l10n_br_fiscal.tax_classification_000001"
                ).id,
                "fiscal_tax_ids": [
                    Command.set(
                        [
                            cls.env.ref("l10n_br_fiscal.tax_icms_18").id,
                            cls.env.ref("l10n_br_fiscal.tax_ibs_0_1").id,
                            cls.env.ref("l10n_br_fiscal.tax_cbs_0_9").id,
                        ]
                    )
                ],
            }
        )

    def _signed_xml(self):
        attachment = self.document.authorization_event_id.file_request_id
        return etree.fromstring(base64.b64decode(attachment.datas))

    def test_nfcom_xml(self):
        # MOC NFCom 1.00a, item 7.3 example
        self.assertEqual(
            key_check_digit("5206043300991100250655012000000780026730161"), "5"
        )
        self.document.action_document_confirm()
        self.assertFalse(self.document.xml_error_message)
        key = self.document.document_key
        self.assertEqual(len(key), 44)
        self.assertEqual(key[20:22], "62")
        self.assertEqual(key[-1], key_check_digit(key[:-1]))

        xml = self._signed_xml()
        inf = xml.find("n:infNFCom", NS)
        self.assertEqual(inf.get("Id"), f"NFCom{key}")
        self.assertEqual(inf.findtext("n:ide/n:mod", namespaces=NS), "62")
        self.assertEqual(inf.findtext("n:dest/n:CNPJ", namespaces=NS), "45723174000110")
        self.assertEqual(inf.findtext("n:assinante/n:tpServUtil", namespaces=NS), "4")
        det = inf.find("n:det", NS)
        self.assertEqual(det.get("nItem"), "1")
        self.assertEqual(det.findtext("n:prod/n:vProd", namespaces=NS), "100.00")
        icms = det.find("n:imposto/n:ICMS00", NS)
        self.assertEqual(icms.findtext("n:vBC", namespaces=NS), "100.00")
        self.assertEqual(icms.findtext("n:vICMS", namespaces=NS), "18.00")
        line = self.document.fiscal_line_ids
        self.assertTrue(line.cbs_value)
        cbs = f"{line.cbs_value:.2f}"
        ibscbs = det.find("n:imposto/n:IBSCBS", NS)
        self.assertEqual(ibscbs.findtext("n:cClassTrib", namespaces=NS), "000001")
        self.assertEqual(ibscbs.findtext("n:gIBSCBS/n:gCBS/n:vCBS", namespaces=NS), cbs)
        total = inf.find("n:total", NS)
        self.assertEqual(total.findtext("n:ICMSTot/n:vICMS", namespaces=NS), "18.00")
        self.assertEqual(
            total.findtext("n:IBSCBSTot/n:gCBS/n:vCBS", namespaces=NS), cbs
        )
        self.assertEqual(total.findtext("n:vNF", namespaces=NS), "100.00")
        self.assertIn(
            f"chNFCom={key}&tpAmb=2",
            xml.findtext("n:infNFComSupl/n:qrCodNFCom", namespaces=NS),
        )
        self.assertIsNotNone(xml.find("{http://www.w3.org/2000/09/xmldsig#}Signature"))

        with self.assertRaises(UserError):
            self.document.action_document_send()

    def test_nfcom_cancel_event(self):
        self.document.action_document_confirm()
        self.document.authorization_event_id.protocol_number = "143260000000001"
        event = etree.fromstring(
            self.document._nfcom_cancel_event_xml("Cancelamento de teste da NFCom")
        )
        self.assertEqual(
            event.find("n:infEvento", NS).get("Id"),
            f"ID110111{self.document.document_key}001",
        )
        self.assertEqual(
            event.findtext(
                "n:infEvento/n:detEvento/n:evCancNFCom/n:nProt", namespaces=NS
            ),
            "143260000000001",
        )
