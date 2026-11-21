# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import date, datetime

from erpbrasil.assinatura import misc
from lxml import etree

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_br_nfeabi_spec.bindings.v1_0 import Evento

from ..constants.nfeabi import NFEABI_HOMOLOGATION_NAME
from ..models.nfeabi.document import nfeabi_check_digit, nfeabi_schema

NS = {"abi": "http://www.portalfiscal.inf.br/nfeabi"}


@tagged("post_install", "-at_install")
class TestNFeABI(TransactionCase):
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
                "nfeabi_qrcode_url": "https://www.example.com.br/nfeabi/qrcode",
                "nfeabi_key_query_url": "https://www.example.com.br/nfeabi/consulta",
                "nfeabi_technical_partner_id": cls.env["res.partner"]
                .create(
                    {
                        "name": "Sistemas Teste NF-e ABI",
                        "is_company": True,
                        "vat": "71.538.264/0001-41",
                        "email": "suporte@example.com.br",
                        "phone": "(11) 3333-4444",
                    }
                )
                .id,
            }
        )
        cls.company.certificate_id = cls.env["certificate.certificate"].create(
            {
                "pkcs12_password": "123456",
                "content": misc.create_fake_certificate_file(
                    valid=True,
                    passwd="123456",
                    issuer="EMISSOR A TESTE",
                    country="BR",
                    subject="CERTIFICADO VALIDO TESTE",
                ),
                "company_id": cls.company.id,
            }
        )
        cls.document_type = cls.env.ref("l10n_br_nfeabi.document_77")
        cls.serie = cls.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "1",
                "name": "NF-e ABI",
                "document_type_id": cls.document_type.id,
                "company_id": cls.company.id,
            }
        )
        address = {
            "street_name": "Rua das Palmeiras",
            "street_number": "100",
            "district": "Centro",
            "city_id": cls.env.ref("l10n_br_base.city_3550308").id,
            "state_id": cls.env.ref("base.state_br_sp").id,
            "country_id": cls.env.ref("base.br").id,
            "zip": "01001-000",
        }
        cls.acquirer = cls.env["res.partner"].create(
            dict(address, name="Adquirente NF-e ABI", vat="528.641.937-28")
        )
        cls.co_owner = cls.env["res.partner"].create(
            dict(address, name="Coproprietario NF-e ABI", vat="639.174.285-55")
        )
        cls.property = cls.env["l10n_br_nfeabi.property"].create(
            {
                "name": "Apartamento 101",
                "nfeabi10_espImovel": "03",
                "nfeabi10_enquadramento": "01",
                "nfeabi10_nIPTU": "0123456789",
                "nfeabi10_cartorioRegistro": "1o Registro de Imoveis",
                "nfeabi10_matricTransc": "12345",
                "street_name": "Avenida Paulista",
                "street_number": "1000",
                "street2": "Apto 101",
                "district": "Bela Vista",
                "city_id": cls.env.ref("l10n_br_base.city_3550308").id,
                "zip": "01310-100",
            }
        )
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.product = cls.env["product.product"].create(
            {"name": "Alienacao de imovel", "default_code": "IMOVEL"}
        )

    def _create_document(self, **values):
        document_values = {
            "company_id": self.company.id,
            "partner_id": self.acquirer.id,
            "document_type_id": self.document_type.id,
            "document_serie_id": self.serie.id,
            "fiscal_operation_type": "out",
            "fiscal_operation_id": self.operation.id,
            "document_date": datetime(2026, 11, 20, 15),
            "nfeabi10_natOper": "01",
            "nfeabi10_detOper": "02",
            "nfeabi10_imovel": self.property.id,
            "nfeabi10_dtInstrumento": date(2026, 11, 20),
            "nfeabi10_vInicial": 200000,
            "nfeabi10_vITBI": 6000,
            "nfeabi10_vRedSocial": 100000,
            "nfeabi10_transmit": [
                Command.create({"partner_id": self.company.partner_id.id})
            ],
            "nfeabi10_adquirente": [Command.create({"partner_id": self.acquirer.id})],
            "fiscal_line_ids": [
                Command.create(
                    {
                        "product_id": self.product.id,
                        "name": "Alienacao do Apartamento 101",
                        "quantity": 1,
                        "price_unit": 500000,
                        "fiscal_operation_id": self.operation.id,
                        "fiscal_operation_line_id": self.operation.line_ids[:1].id,
                        "tax_classification_id": self.env.ref(
                            "l10n_br_fiscal.tax_classification_000001"
                        ).id,
                    }
                )
            ],
        }
        document_values.update(values)
        return self.env["l10n_br_fiscal.document"].create(document_values)

    def _xml(self, document):
        self.assertFalse(document.xml_error_message)
        return etree.fromstring(
            base64.b64decode(document.authorization_event_id.file_request_id.datas)
        )

    def test_nfeabi_simplified(self):
        document = self._create_document(
            nfeabi10_gIntermedCorret=[
                Command.create(
                    {
                        "partner_id": self.company.nfeabi_technical_partner_id.id,
                        "nfeabi10_vCorretagem": 25000,
                    }
                )
            ]
        )
        document.action_document_confirm()
        root = self._xml(document)

        def text(path):
            return root.findtext(path, namespaces=NS)

        key = document.document_key
        self.assertEqual(len(key), 44)
        self.assertEqual(key[20:22], "77")
        self.assertEqual(key[-1], nfeabi_check_digit(key[:-1]))
        self.assertEqual(root.find("abi:infNFeABI", NS).get("Id"), f"NFeABI{key}")
        self.assertEqual(text(".//abi:ide/abi:mod"), "77")
        self.assertEqual(text(".//abi:ide/abi:tpNF"), "0")
        self.assertEqual(text(".//abi:gModNat/abi:modOper"), "01")
        self.assertEqual(text(".//abi:emit/abi:tpEmit"), "01")
        self.assertEqual(text(".//abi:emit/abi:xNome"), NFEABI_HOMOLOGATION_NAME)
        self.assertEqual(
            text(".//abi:emit/abi:CNPJ"), self.company.partner_id.cnpj_cpf_stripped
        )
        transmitters = root.findall(".//abi:transmit", NS)
        self.assertEqual(len(transmitters), 1)
        self.assertEqual(transmitters[0].get("nTransmit"), "1")
        self.assertIsNone(transmitters[0].find("abi:indDeclarante", NS))
        self.assertEqual(text(".//abi:adquirente/abi:CPF"), "52864193728")
        self.assertEqual(text(".//abi:imovel/abi:cadastro/abi:nIPTU"), "0123456789")
        self.assertEqual(text(".//abi:imovel/abi:enderImovel/abi:cMun"), "3550308")
        self.assertEqual(text(".//abi:infOper/abi:vTotalOperacao"), "500000.00")
        self.assertEqual(
            text(".//abi:gRedAjusteImovel/abi:vRedAjusteImovel"), "206000.00"
        )
        self.assertEqual(text(".//abi:infOper/abi:indRedSocial"), "1")
        self.assertEqual(text(".//abi:infOper/abi:indIntermedCorret"), "1")
        broker = root.find(".//abi:gIntermedCorret", NS)
        self.assertEqual(broker.get("nCorretagem"), "1")
        self.assertEqual(broker.findtext("abi:vCorretagem", namespaces=NS), "25000.00")
        self.assertEqual(text(".//abi:IBSCBS/abi:CST"), "000")
        self.assertEqual(text(".//abi:IBSCBS/abi:cClassTrib"), "000001")
        # Tabela de Códigos NF-e ABI v1.01, sheet vBC (modOper 01)
        self.assertEqual(text(".//abi:gIBSCBS/abi:vBC"), "194000.00")
        line = document.fiscal_line_ids
        self.assertEqual(line.ibs_base, 194000)
        self.assertEqual(text(".//abi:gIBSUF/abi:vIBSUF"), f"{line.ibs_value:.2f}")
        self.assertEqual(text(".//abi:gCBS/abi:vCBS"), f"{line.cbs_value:.2f}")
        self.assertEqual(text(".//abi:gIBSUF/abi:vIBSUF"), "194.00")
        self.assertEqual(text(".//abi:gCBS/abi:vCBS"), "1746.00")
        self.assertEqual(text(".//abi:gCBS/abi:gRed/abi:pAliqEfet"), "0.9000")
        self.assertEqual(text(".//abi:tribTot/abi:vBC"), "194000.00")
        self.assertEqual(text(".//abi:total/abi:vNF"), "501940.00")
        self.assertEqual(
            text(".//abi:qrCode"),
            f"https://www.example.com.br/nfeabi/qrcode?chNFeABI={key}&tpAmb=2",
        )
        self.assertIsNotNone(root.find("{http://www.w3.org/2000/09/xmldsig#}Signature"))
        with self.assertRaises(UserError):
            document.action_document_send()

    def test_nfeabi_complete(self):
        """Two transmitters with half of the property each: the declarant
        informs its share (rules U10-20, U12-20 and U13-20)."""
        document = self._create_document(
            nfeabi10_tpNF="1",
            nfeabi10_transmit=[
                Command.create(
                    {"partner_id": self.co_owner.id, "transfer_percent": 50}
                ),
                Command.create(
                    {"partner_id": self.company.partner_id.id, "transfer_percent": 50}
                ),
            ],
        )
        document.action_document_confirm()
        root = self._xml(document)
        transmitters = root.findall(".//abi:transmit", NS)
        self.assertEqual(len(transmitters), 2)
        declarant, other = transmitters
        self.assertEqual(declarant.get("nTransmit"), "1")
        self.assertEqual(declarant.findtext("abi:indDeclarante", namespaces=NS), "1")
        self.assertEqual(
            declarant.findtext("abi:pTransIndiv", namespaces=NS), "50.0000"
        )
        self.assertIsNotNone(declarant.find("abi:enderTransmit", NS))
        self.assertEqual(other.get("nTransmit"), "2")
        self.assertEqual(other.findtext("abi:indDeclarante", namespaces=NS), "0")
        self.assertEqual(other.findtext("abi:CPF", namespaces=NS), "63917428555")
        self.assertEqual(
            root.findtext(".//abi:pTransImovel", namespaces=NS), "100.0000"
        )
        group = root.find(".//abi:gIBSCBS", NS)
        self.assertEqual(group.findtext("abi:vOperacIndiv", namespaces=NS), "250000.00")
        self.assertEqual(
            group.findtext("abi:vRedAjusteIndiv", namespaces=NS), "103000.00"
        )
        self.assertEqual(
            group.findtext("abi:vRedSocialIndiv", namespaces=NS), "50000.00"
        )
        self.assertEqual(group.findtext("abi:vBC", namespaces=NS), "97000.00")
        self.assertEqual(
            root.findtext(".//abi:total/abi:vNF", namespaces=NS), "250970.00"
        )

    def test_nfeabi_assignment(self):
        """Assignment of rights: no reducers and vBC = vOperacIndiv."""
        document = self._create_document(
            nfeabi10_modOper="03", nfeabi10_natOper="09", nfeabi10_detOper="17"
        )
        document.nfeabi10_vRedSocial = 0
        document.action_document_confirm()
        root = self._xml(document)
        self.assertIsNone(root.find(".//abi:gRedAjusteImovel", NS))
        self.assertIsNone(root.find(".//abi:indRedSocial", NS))
        self.assertIsNone(root.find(".//abi:indIntermedCorret", NS))
        self.assertEqual(
            root.findtext(".//abi:gIBSCBS/abi:vBC", namespaces=NS), "500000.00"
        )

    def test_nfeabi_checks(self):
        document = self._create_document(nfeabi10_modOper="02", nfeabi10_natOper="06")
        with self.assertRaisesRegex(UserError, "auction"):
            document.action_document_confirm()
        document = self._create_document(
            nfeabi10_tpNF="1",
            nfeabi10_pTransImovel=100,
            nfeabi10_transmit=[
                Command.create(
                    {"partner_id": self.company.partner_id.id, "transfer_percent": 40}
                )
            ],
        )
        with self.assertRaisesRegex(UserError, "add up"):
            document.action_document_confirm()

    def test_nfeabi_events(self):
        document = self._create_document()
        document.action_document_confirm()
        document.authorization_protocol = "1352600000000012"
        events = (
            (
                document._nfeabi_cancel_event_xml("Alienacao emitida em duplicidade"),
                "evCancNFeABI",
                "evCancNFeABI_v1.00.xsd",
                "110111",
            ),
            (
                document._nfeabi_undo_event_xml("01", date(2026, 11, 25)),
                "evDesfazimAlienac",
                "evDesfazimAlienacNFeABI_v1.00.xsd",
                "112320",
            ),
        )
        for xml, tag, schema, event_type in events:
            # NT 2026.001: the envelope and the detail are validated apart
            self.assertFalse(
                Evento.schema_validation(xml, nfeabi_schema("eventoNFeABI_v1.00.xsd"))
            )
            root = etree.fromstring(xml.encode())
            detail = root.find(f".//abi:{tag}", NS)
            self.assertFalse(
                Evento.schema_validation(
                    etree.tostring(detail).decode(), nfeabi_schema(schema)
                )
            )
            self.assertEqual(
                root.find("abi:infEvento", NS).get("Id"),
                f"ID{event_type}{document.document_key}001",
            )
