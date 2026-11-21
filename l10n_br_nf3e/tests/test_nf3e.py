# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import datetime
from importlib import resources

import nfelib
from erpbrasil.assinatura import misc
from lxml import etree
from nfelib.nf3e.bindings.v1_0.evento_nf3e_v1_00 import EventoNf3E

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from ..models.document import nf3e_check_digit

NS = {"nf3e": "http://www.portalfiscal.inf.br/nf3e"}


@tagged("post_install", "-at_install")
class TestNF3e(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=True, tz="America/Sao_Paulo")
        )
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.company.processador_edoc = "oca"
        cls.company.certificate_nfe_id = cls.env["l10n_br_fiscal.certificate"].create(
            {
                "type": "nf-e",
                "subtype": "a1",
                "password": "123456",
                "file": misc.create_fake_certificate_file(
                    valid=True,
                    passwd="123456",
                    issuer="EMISSOR A TESTE",
                    country="BR",
                    subject="CERTIFICADO VALIDO TESTE",
                ),
            }
        )
        document_type = cls.env.ref("l10n_br_fiscal.document_66")
        serie = cls.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "1",
                "name": "NF3e",
                "document_type_id": document_type.id,
                "company_id": cls.company.id,
            }
        )
        partner = cls.env["res.partner"].create(
            {
                "name": "Consumidor NF3e",
                "is_company": True,
                "vat": "33.627.564/0001-08",
                "street_name": "Rua das Flores",
                "street_number": "10",
                "district": "Centro",
                "city_id": cls.env.ref("l10n_br_base.city_3550308").id,
                "state_id": cls.env.ref("base.state_br_sp").id,
                "country_id": cls.env.ref("base.br").id,
                "zip": "01001-000",
                "ind_ie_dest": "9",
            }
        )
        operation = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": cls.company.id,
                "partner_id": partner.id,
                "document_type_id": document_type.id,
                "document_serie_id": serie.id,
                "fiscal_operation_type": "out",
                "fiscal_operation_id": operation.id,
                "nf3e10_idAcesso": "123456789",
                "nf3e10_tpAcesso": "1",
                "nf3e10_tpFase": "1",
                "nf3e10_tpGrpTensao": "01",
                "nf3e10_tpModTar": "01",
                "nf3e10_latGPS": "-23.550520",
                "nf3e10_longGPS": "-46.633308",
                "nf3e10_CompetFat": "202611",
                "nf3e10_dVencFat": "2026-12-10",
                "nf3e10_dProxLeitura": "2026-12-20",
                "nf3e10_codBarras": "83600000001234567890123456789012345678901234",
                "nf3e10_codDebAuto": "123",
                "nf3e10_gHistFat": [
                    Command.create(
                        {
                            "nf3e10_xGrandFat": "Consumo kWh",
                            "nf3e10_gGrandFat": [
                                Command.create(
                                    {
                                        "nf3e10_CompetFat": f"{202511 + month}"
                                        if month < 2
                                        else f"{202600 + month - 1}",
                                        "nf3e10_vFat": 100,
                                        "nf3e10_uMed": "2",
                                        "nf3e10_qtdDias": "30",
                                    }
                                )
                                for month in range(13)
                            ],
                        }
                    )
                ],
                "fiscal_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.env["product.product"]
                            .create({"name": "Energia TE", "default_code": "TE"})
                            .id,
                            "name": "Consumo TE",
                            "quantity": 100,
                            "price_unit": 0.8,
                            "fiscal_operation_id": operation.id,
                            "fiscal_operation_line_id": operation.line_ids[:1].id,
                            "tax_classification_id": cls.env.ref(
                                "l10n_br_fiscal.tax_classification_000001"
                            ).id,
                            "nf3e10_cClass": "0100101",
                            "nf3e10_uMed": "2",
                            "nf3e10_indOrigemQtd": "2",
                        }
                    )
                ],
            }
        )
        cls.line = cls.document.fiscal_line_ids
        cls.line.cfop_id = cls.env.ref("l10n_br_fiscal.cfop_5258")
        cls.document.action_document_confirm()
        cls.document.document_date = datetime(2026, 11, 20, 15)

    def test_nf3e_xml(self):
        document = self.document
        self.assertFalse(document.xml_error_message)
        key = document.document_key
        self.assertEqual(len(key), 44)
        self.assertEqual(key[20:22], "66")
        self.assertEqual(key[-1], nf3e_check_digit(key[:-1]))
        xml = base64.b64decode(document.authorization_event_id.file_request_id.datas)
        root = etree.fromstring(xml)

        def text(path):
            return root.findtext(path, namespaces=NS)

        self.assertEqual(
            root.find("nf3e:infNF3e", NS).get("Id"), f"NF3e{document.document_key}"
        )
        self.assertEqual(text(".//nf3e:ide/nf3e:mod"), "66")
        self.assertEqual(
            text(".//nf3e:emit/nf3e:CNPJ"), self.company.partner_id.cnpj_cpf_stripped
        )
        self.assertEqual(text(".//nf3e:acessante/nf3e:idAcesso"), "123456789")
        self.assertEqual(len(root.findall(".//nf3e:gGrandFat", NS)), 13)
        self.assertEqual(text(".//nf3e:prod/nf3e:CFOP"), "5258")
        self.assertEqual(text(".//nf3e:ICMS00/nf3e:CST"), "00")
        self.assertEqual(text(".//nf3e:IBSCBS/nf3e:cClassTrib"), "000001")
        self.assertTrue(self.line.ibs_value and self.line.cbs_value)
        self.assertEqual(
            text(".//nf3e:gIBSUF/nf3e:vIBSUF"), f"{self.line.ibs_value:.2f}"
        )
        self.assertEqual(text(".//nf3e:gCBS/nf3e:vCBS"), f"{self.line.cbs_value:.2f}")
        self.assertEqual(
            text(".//nf3e:IBSCBSTot/nf3e:gCBS/nf3e:vCBS"), f"{self.line.cbs_value:.2f}"
        )
        self.assertIn(f"?chNF3e={key}&tpAmb=2", text(".//nf3e:qrCodNF3e"))
        self.assertIsNotNone(root.find("{http://www.w3.org/2000/09/xmldsig#}Signature"))
        with self.assertRaises(UserError):
            document.action_document_send()

    def test_nf3e_vtotdfe(self):
        """NT 2025.001 RTC v1.14a, rule 365: vNF in 2026, plus IBS and CBS from
        2027 on."""
        document = self.document
        self.assertEqual(document.nf3e10_vTotDFe, document.nf3e10_vNF)
        document.document_date = datetime(2027, 1, 5, 15)
        self.assertAlmostEqual(
            document.nf3e10_vTotDFe,
            document.nf3e10_vNF + self.line.ibs_value + self.line.cbs_value,
        )

    def test_nf3e_cancel_event(self):
        self.document.authorization_protocol = "1352600000000012"
        xml = self.document._nf3e_cancel_event_xml("Fatura emitida em duplicidade")
        schemas = resources.files(nfelib).joinpath("nf3e", "schemas", "v1_0")
        self.assertFalse(
            EventoNf3E.schema_validation(
                xml, str(schemas.joinpath("eventoNF3e_v1.00.xsd"))
            )
        )
        root = etree.fromstring(xml.encode())
        cancel = root.find(".//nf3e:evCancNF3e", NS)
        self.assertFalse(
            EventoNf3E.schema_validation(
                etree.tostring(cancel).decode(),
                str(schemas.joinpath("evCancNF3e_v1.00.xsd")),
            )
        )
        self.assertEqual(
            root.find("nf3e:infEvento", NS).get("Id"),
            f"ID110111{self.document.document_key}001",
        )
