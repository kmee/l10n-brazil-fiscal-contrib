# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import gzip
import re
from datetime import date, datetime
from unittest import mock

from erpbrasil.assinatura import misc
from lxml import etree

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger

from odoo.addons.l10n_br_nfag_spec.bindings.v1_0 import EventoNfag

from ..constants.nfag import nfag_schema
from ..models.document import nfag_check_digit
from ..nfag_client.client import NfagClient

NS = {"nfag": "http://www.portalfiscal.inf.br/nfag"}

SOAP_RESPONSE = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">'
    "<soap:Body>"
    '<nfagResultMsg xmlns="http://www.portalfiscal.inf.br/NFAg/wsdl/%(service)s">'
    "%(content)s</nfagResultMsg></soap:Body></soap:Envelope>"
)

RET_NFAG = (
    '<retNFAg xmlns="http://www.portalfiscal.inf.br/nfag" versao="1.00">'
    "<tpAmb>2</tpAmb><cUF>35</cUF><verAplic>SVRS-TESTE</verAplic>"
    "<cStat>100</cStat><xMotivo>Autorizado o uso da NFAg</xMotivo>"
    '<protNFAg versao="1.00"><infProt>'
    "<tpAmb>2</tpAmb><verAplic>SVRS-TESTE</verAplic><chNFAg>%(key)s</chNFAg>"
    "<dhRecbto>2026-11-20T15:00:01-03:00</dhRecbto>"
    "<nProt>3752600000000001</nProt>"
    "<digVal>bm90LWNoZWNrZWQtaW4tdGVzdHM=</digVal>"
    "<cStat>100</cStat><xMotivo>Autorizado o uso da NFAg</xMotivo>"
    "</infProt></protNFAg></retNFAg>"
)

RET_EVENTO = (
    '<retEventoNFAg xmlns="http://www.portalfiscal.inf.br/nfag" versao="1.00">'
    "<infEvento><tpAmb>2</tpAmb><verAplic>SVRS-TESTE</verAplic>"
    "<cOrgao>35</cOrgao><cStat>%(status)s</cStat><xMotivo>%(reason)s</xMotivo>"
    "<chNFAg>%(key)s</chNFAg><tpEvento>110111</tpEvento>"
    "<xEvento>Cancelamento</xEvento><nSeqEvento>1</nSeqEvento>"
    "<dhRegEvento>2026-11-20T15:05:00-03:00</dhRegEvento>"
    "<nProt>3752600000000002</nProt></infEvento></retEventoNFAg>"
)


@tagged("post_install", "-at_install")
class TestNFAg(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=True, tz="America/Sao_Paulo")
        )
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.company.processador_edoc = "oca"
        cls.company.nfag_environment = "2"
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
        document_type = cls.env.ref("l10n_br_fiscal.document_75")
        serie = cls.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "1",
                "name": "NFAg",
                "document_type_id": document_type.id,
                "company_id": cls.company.id,
            }
        )
        partner = cls.env["res.partner"].create(
            {
                "name": "Consumidor NFAg",
                "is_company": True,
                "vat": "47.621.853/0001-04",
                "street_name": "Rua das Fontes",
                "street_number": "75",
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
                "document_date": datetime(2026, 11, 20, 15),
                "fiscal_operation_type": "out",
                "fiscal_operation_id": operation.id,
                "nfag_environment": "2",
                "nfag10_idLigacao": "000123456",
                "nfag10_tpLigacao": "1",
                "nfag10_latGPS": "-23.550520",
                "nfag10_longGPS": "-46.633308",
                "nfag10_CompetFat": "202611",
                "nfag10_dVencFat": date(2026, 12, 10),
                "nfag10_dProxLeitura": date(2026, 12, 18),
                "nfag10_codBarras": "82650000001234567890123456789012345678901234",
                "nfag10_codDebAuto": "123",
                "nfag10_nAgenciaAtend": "Agencia Centro",
                "nfag10_enderAgenciaAtend": "Rua das Fontes, 1, Centro, Sao Paulo",
                "nfag10_gMed": [
                    Command.create(
                        {
                            "nfag10_nMed": "01",
                            "nfag10_idMedidor": "HID-0001",
                            "nfag10_dMedAnt": date(2026, 10, 18),
                            "nfag10_dMedAtu": date(2026, 11, 18),
                        }
                    )
                ],
                "nfag10_gHistCons": [
                    Command.create(
                        {
                            "nfag10_xHistorico": "Consumo de agua m3",
                            "nfag10_medMensal": 10,
                            "nfag10_gCons": [
                                Command.create(
                                    {
                                        "nfag10_CompetFat": competence,
                                        "nfag10_uMed": "1",
                                        "nfag10_qtdDias": "00030",
                                        "nfag10_volFat": 10,
                                    }
                                )
                                for competence in ("202608", "202609", "202610")
                            ],
                        }
                    )
                ],
                "fiscal_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.env["product.product"]
                            .create({"name": "Agua tratada", "default_code": "AGUA"})
                            .id,
                            "name": "Fornecimento de agua",
                            "quantity": 10,
                            "price_unit": 8.5,
                            "fiscal_operation_id": operation.id,
                            "fiscal_operation_line_id": operation.line_ids[:1].id,
                            "tax_classification_id": cls.env.ref(
                                "l10n_br_fiscal.tax_classification_000001"
                            ).id,
                            # any 7 digit code: the cClass table of the NFAg
                            # portal is not bundled (see the roadmap)
                            "nfag10_cClass": "0100101",
                            "nfag10_uMed": "1",
                            "nfag10_indOrigemQtd": "2",
                        }
                    )
                ],
            }
        )
        cls.line = cls.document.fiscal_line_ids
        # the NFAg has no ICMS group
        cls.line.icms_tax_id = False

    def _signed_xml(self):
        attachment = self.document.authorization_event_id.file_request_id
        return base64.b64decode(attachment.datas).decode("utf-8")

    def _soap(self, service, content):
        return (SOAP_RESPONSE % {"service": service, "content": content}).encode()

    def test_check_digit(self):
        """Example of the MOC NFAg 1.00l (Visão Geral, cálculo do DV)."""
        self.assertEqual(
            nfag_check_digit("5206043300991100250655012000000780026730161"), "5"
        )

    def test_nfag_xml(self):
        """The NFAg is signed, valid against the XSD and has the main groups."""
        document = self.document
        document.action_document_confirm()
        self.assertFalse(document.xml_error_message)
        key = document.document_key
        self.assertEqual(len(key), 44)
        self.assertEqual(key[20:22], "75")
        self.assertEqual(key[-1], nfag_check_digit(key[:-1]))
        xml = self._signed_xml()
        root = etree.fromstring(xml.encode())

        def text(path):
            return root.findtext(path, namespaces=NS)

        self.assertEqual(root.find("nfag:infNFAg", NS).get("Id"), f"NFAG{key}")
        self.assertEqual(text(".//nfag:ide/nfag:mod"), "75")
        self.assertEqual(text(".//nfag:ide/nfag:finNFAg"), "0")
        self.assertEqual(text(".//nfag:ide/nfag:tpFat"), "1")
        self.assertEqual(
            text(".//nfag:emit/nfag:CNPJ"), self.company.partner_id.cnpj_cpf_stripped
        )
        self.assertEqual(text(".//nfag:dest/nfag:CNPJ"), "47621853000104")
        self.assertEqual(text(".//nfag:ligacao/nfag:idLigacao"), "000123456")
        self.assertEqual(root.find(".//nfag:gMed", NS).get("nMed"), "01")
        self.assertEqual(text(".//nfag:det/nfag:prod/nfag:cClass"), "0100101")
        self.assertEqual(float(text(".//nfag:det/nfag:prod/nfag:vProd")), 85.0)
        self.assertEqual(text(".//nfag:gFat/nfag:codDebAuto"), "123")
        self.assertEqual(len(root.findall(".//nfag:gHistCons/nfag:gCons", NS)), 3)
        self.assertEqual(text(".//nfag:IBSCBS/nfag:cClassTrib"), "000001")
        self.assertTrue(self.line.ibs_value and self.line.cbs_value)
        self.assertEqual(
            text(".//nfag:gIBSUF/nfag:vIBSUF"), f"{self.line.ibs_value:.2f}"
        )
        self.assertEqual(text(".//nfag:gCBS/nfag:vCBS"), f"{self.line.cbs_value:.2f}")
        self.assertEqual(
            text(".//nfag:IBSCBSTot/nfag:gCBS/nfag:vCBS"), f"{self.line.cbs_value:.2f}"
        )
        # NT 2026.004 v1.01, rule 365: vTotDFe repeats vNF in 2026
        self.assertEqual(text(".//nfag:total/nfag:vNF"), "85.00")
        self.assertEqual(text(".//nfag:total/nfag:vTotDFe"), "85.00")
        self.assertEqual(
            text(".//nfag:qrCodNFAg"),
            f"https://dfe-portal.svrs.rs.gov.br/nfag/qrCode?chNFAg={key}&tpAmb=2",
        )
        self.assertIsNotNone(root.find("{http://www.w3.org/2000/09/xmldsig#}Signature"))

    def test_vtotdfe_from_2027(self):
        """NT 2026.004 v1.01, rule 365: vNF plus IBS and CBS from 2027 on."""
        document = self.document
        self.assertEqual(document.nfag10_vTotDFe, document.nfag10_vNF)
        document.document_date = datetime(2027, 1, 5, 15)
        self.assertAlmostEqual(
            document.nfag10_vTotDFe,
            document.nfag10_vNF + self.line.ibs_value + self.line.cbs_value,
        )

    def test_deduction_item(self):
        """An item whose cClass starts with 5 is deducted from the totals."""
        self.line.nfag10_cClass = "5000101"
        self.assertEqual(self.document.nfag10_vProd, -self.line.nfag10_vProd)

    def test_required_fields(self):
        self.document.nfag10_idLigacao = False
        with self.assertRaisesRegex(UserError, "Ligação"):
            self.document.action_document_confirm()

    @mute_logger("brazil_fiscal_client.fiscal_client")
    def test_send_and_cancel(self):
        """Authorization and cancellation against a simulated authorizer."""
        document = self.document
        document.action_document_confirm()
        key = document.document_key
        with mock.patch.object(
            NfagClient,
            "_post",
            return_value=self._soap("NFAgRecepcao", RET_NFAG % {"key": key}),
        ) as post:
            document.action_document_send()
        location = post.call_args.args[0]
        self.assertEqual(
            location,
            "https://nfag-homologacao.svrs.rs.gov.br/WS/NFAgRecepcao/NFAgRecepcao.asmx",
        )
        self.assertIn(
            "NFAg/wsdl/NFAgRecepcao/NFAgRecepcao",
            post.call_args.kwargs["headers"]["content-type"],
        )
        sent = re.search(r"nfagDadosMsg[^>]*>([^<]+)<", post.call_args.kwargs["data"])
        sent_xml = gzip.decompress(base64.b64decode(sent.group(1))).decode()
        self.assertIn(f'Id="NFAG{key}"', sent_xml)
        self.assertEqual(document.state_edoc, "autorizada")
        self.assertEqual(document.authorization_protocol, "3752600000000001")

        cancel_xml = document._nfag_cancel_event_xml("Fatura emitida em duplicidade")
        cancel = etree.fromstring(cancel_xml.encode()).find(".//nfag:evCancNFAg", NS)
        self.assertFalse(
            EventoNfag.schema_validation(
                etree.tostring(cancel).decode(), nfag_schema("evCancNFAg")
            )
        )

        def event_response(status, reason):
            return self._soap(
                "NFAgRecepcaoEvento",
                RET_EVENTO % {"status": status, "reason": reason, "key": key},
            )

        # a refusal keeps the document authorized and the event recorded
        with mock.patch.object(
            NfagClient, "_post", return_value=event_response("220", "Rejeicao: prazo")
        ):
            document._document_cancel("Cancelamento de teste da NFAg")
        self.assertEqual(document.state_edoc, "autorizada")
        self.assertEqual(document.cancel_event_id.status_code, "220")

        with mock.patch.object(
            NfagClient,
            "_post",
            return_value=event_response("135", "Evento registrado e vinculado"),
        ) as post:
            document._document_cancel("Cancelamento de teste da NFAg")
        self.assertIn(f"ID110111{key}001", post.call_args.kwargs["data"])
        self.assertEqual(document.state_edoc, "cancelada")
        self.assertEqual(document.cancel_event_id.state, "done")
