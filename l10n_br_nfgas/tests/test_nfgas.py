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

from odoo.addons.l10n_br_nfgas_spec.bindings.v1_0.nfgas_v1_00 import Nfgas
from odoo.addons.l10n_br_nfgas_spec.tools import schema_path

from ..models.document import nfgas_check_digit
from ..nfgas_client.client import NfgasClient

NS = {"nfgas": "http://www.portalfiscal.inf.br/nfgas"}

SOAP_RESPONSE = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">'
    "<soap:Body>"
    '<nfgasResultMsg xmlns="http://www.portalfiscal.inf.br/NFGas/wsdl/%(service)s">'
    "%(content)s</nfgasResultMsg></soap:Body></soap:Envelope>"
)

RET_NFGAS = (
    '<retNFGas xmlns="http://www.portalfiscal.inf.br/nfgas" versao="1.00">'
    "<tpAmb>2</tpAmb><cUF>35</cUF><verAplic>RS20261101</verAplic>"
    "<cStat>100</cStat><xMotivo>Autorizado o Uso da NFGas</xMotivo>"
    '<protNFGas versao="1.00"><infProt>'
    "<tpAmb>2</tpAmb><verAplic>RS20261101</verAplic><chNFGas>%(key)s</chNFGas>"
    "<dhRecbto>2026-11-21T10:00:01-03:00</dhRecbto>"
    "<nProt>3352600000000001</nProt>"
    "<digVal>bm90LWNoZWNrZWQtaW4tdGVzdHM=</digVal>"
    "<cStat>100</cStat><xMotivo>Autorizado o Uso da NFGas</xMotivo>"
    "</infProt></protNFGas></retNFGas>"
)

RET_EVENTO = (
    '<retEventoNFGas xmlns="http://www.portalfiscal.inf.br/nfgas" versao="1.00">'
    "<infEvento><tpAmb>2</tpAmb><verAplic>RS20261101</verAplic><cOrgao>35</cOrgao>"
    "<cStat>%(status)s</cStat><xMotivo>%(reason)s</xMotivo>"
    "<chNFGas>%(key)s</chNFGas><tpEvento>110111</tpEvento>"
    "<xEvento>Cancelamento</xEvento><nSeqEvento>1</nSeqEvento>"
    "<dhRegEvento>2026-11-21T10:05:00-03:00</dhRegEvento>"
    "<nProt>3352600000000002</nProt></infEvento></retEventoNFGas>"
)


@tagged("post_install", "-at_install")
class TestNFGas(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=True, tz="America/Sao_Paulo")
        )
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.company.processador_edoc = "oca"
        cls.company.nfgas_environment = "2"
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
        document_type = cls.env.ref("l10n_br_nfgas.document_76")
        serie = cls.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "1",
                "name": "NFGas",
                "document_type_id": document_type.id,
                "company_id": cls.company.id,
            }
        )
        partner = cls.env["res.partner"].create(
            {
                "name": "Consumidor NFGas",
                "is_company": True,
                "vat": "76.240.138/0001-20",
                "street_name": "Rua do Gasoduto",
                "street_number": "76",
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
                "document_date": datetime(2026, 11, 21, 13, 0, 0),
                "nfgas10_idInstalacao": "INST000123",
                "nfgas10_tpInstalacao": "1",
                "nfgas10_tpClasse": "02",
                "nfgas10_CompetFat": "202611",
                "nfgas10_dVencFat": date(2026, 12, 10),
                "nfgas10_dProxLeitura": date(2026, 12, 20),
                "nfgas10_codBarras": "83600000001234567890123456789012345678901234",
                "nfgas10_codDebAuto": "123",
                "nfgas10_gMed": [
                    Command.create(
                        {
                            "nfgas10_idEqp": "MED001",
                            "nfgas10_tpEqp": "1",
                            "nfgas10_tpMedidor": "2",
                            "nfgas10_dMedAnt": date(2026, 10, 20),
                            "nfgas10_vMedAnt": 1000.0,
                            "nfgas10_dMedAtu": date(2026, 11, 20),
                            "nfgas10_vMedAtu": 1250.0,
                        }
                    )
                ],
                "nfgas10_gHistCons": [
                    Command.create(
                        {
                            "nfgas10_xHistorico": "Consumo meses anteriores",
                            "nfgas10_medMensal": 240.0,
                            "nfgas10_gCons": [
                                Command.create(
                                    {
                                        "nfgas10_CompetFat": "202610",
                                        "nfgas10_qtdDias": "30",
                                        "nfgas10_vFat": 960.0,
                                    }
                                )
                            ],
                        }
                    )
                ],
                "manual_customer_additional_data": "Fatura de teste",
            }
        )
        cls.line = cls.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": cls.document.id,
                "product_id": cls.env["product.product"]
                .create({"name": "Gas natural", "default_code": "GN"})
                .id,
                "name": "Gas natural canalizado",
                "quantity": 250.0,
                "price_unit": 4.0,
                "fiscal_operation_type": "out",
                "fiscal_operation_id": operation.id,
                "fiscal_operation_line_id": operation.line_ids[:1].id,
                "tax_classification_id": cls.env.ref(
                    "l10n_br_fiscal.tax_classification_000001"
                ).id,
                "nfgas10_cClass": "0100101",
                "nfgas10_indOrigemQtd": "2",
                "nfgas_meter_id": cls.document.nfgas10_gMed.id,
            }
        )
        cls.line.cfop_id = cls.env.ref("l10n_br_fiscal.cfop_5656")

    def _signed_xml(self):
        attachment = self.document.authorization_event_id.file_request_id
        return base64.b64decode(attachment.datas).decode("utf-8")

    def _soap(self, service, content):
        return (SOAP_RESPONSE % {"service": service, "content": content}).encode()

    def test_nfgas_xml(self):
        """The NFGas is signed, valid against the XSD and has the main groups."""
        document = self.document
        document.action_document_confirm()
        self.assertFalse(document.xml_error_message)
        xml = self._signed_xml()
        self.assertEqual(Nfgas.schema_validation(xml, schema_path()), [])
        key = document.document_key
        self.assertEqual(len(key), 44)
        self.assertEqual(key[20:22], "76")
        self.assertEqual(key[-1], nfgas_check_digit(key[:-1]))
        root = etree.fromstring(xml.encode())

        def text(path):
            return root.findtext(path, namespaces=NS)

        self.assertEqual(root.find("nfgas:infNFGas", NS).get("Id"), f"NFGas{key}")
        self.assertIsNotNone(root.find("{http://www.w3.org/2000/09/xmldsig#}Signature"))
        self.assertEqual(text(".//nfgas:ide/nfgas:mod"), "76")
        self.assertEqual(text(".//nfgas:ide/nfgas:tpFat"), "1")
        self.assertEqual(
            text(".//nfgas:emit/nfgas:CNPJ"), self.company.partner_id.cnpj_cpf_stripped
        )
        self.assertEqual(text(".//nfgas:dest/nfgas:CNPJ"), "76240138000120")
        self.assertEqual(text(".//nfgas:instalacao/nfgas:idInstalacao"), "INST000123")
        self.assertEqual(text(".//nfgas:gMed/nfgas:vMedAtu"), "1250.0000")
        self.assertEqual(text(".//nfgas:prod/nfgas:cClass"), "0100101")
        self.assertEqual(text(".//nfgas:prod/nfgas:CFOP"), "5656")
        self.assertEqual(float(text(".//nfgas:prod/nfgas:vProd")), 1000.0)
        self.assertEqual(root.find(".//nfgas:gMed", NS).get("nMed"), "01")
        self.assertEqual(text(".//nfgas:gMedicao/nfgas:nMed"), "01")
        self.assertEqual(text(".//nfgas:gMedida/nfgas:vMed"), "250.0000")
        self.assertEqual(text(".//nfgas:imposto/nfgas:ICMS00/nfgas:CST"), "00")
        # IBS/CBS: the IBSCBS group is mandatory in the NFGas item
        line = self.line
        self.assertTrue(line.ibs_value and line.cbs_value)
        self.assertEqual(text(".//nfgas:IBSCBS/nfgas:cClassTrib"), "000001")
        self.assertEqual(text(".//nfgas:gIBSUF/nfgas:vIBSUF"), f"{line.ibs_value:.2f}")
        self.assertEqual(text(".//nfgas:gCBS/nfgas:vCBS"), f"{line.cbs_value:.2f}")
        self.assertEqual(
            text(".//nfgas:IBSCBSTot/nfgas:gCBS/nfgas:vCBS"), f"{line.cbs_value:.2f}"
        )
        # NT 2026.004 v1.01: vTotDFe repeats vNF in 2026
        self.assertEqual(text(".//nfgas:total/nfgas:vNF"), "1000.00")
        self.assertEqual(text(".//nfgas:total/nfgas:vTotDFe"), "1000.00")
        self.assertEqual(text(".//nfgas:gFat/nfgas:codDebAuto"), "123")
        self.assertEqual(text(".//nfgas:gHistCons/nfgas:gCons/nfgas:vFat"), "960.0000")
        self.assertEqual(text(".//nfgas:infAdic/nfgas:infCpl"), "Fatura de teste")
        self.assertEqual(
            text(".//nfgas:qrCodNFGas"),
            f"https://dfe-portal.svrs.rs.gov.br/nfgas/qrCode?chNFGas={key}&tpAmb=2",
        )

    def test_nfgas_vtotdfe_from_2027(self):
        """NT 2026.004 v1.01, rule 365: vTotDFe adds IBS and CBS from 2027 on."""
        document = self.document
        self.assertEqual(document.nfgas10_vTotDFe, document.nfgas10_vNF)
        document.document_date = datetime(2027, 1, 5, 15, 0, 0)
        self.assertAlmostEqual(
            document.nfgas10_vTotDFe,
            document.nfgas10_vNF + self.line.ibs_value + self.line.cbs_value,
        )

    def test_nfgas_required_fields(self):
        self.document.nfgas10_idInstalacao = False
        self.line.cfop_id = self.env.ref("l10n_br_fiscal.cfop_5102")
        with self.assertRaisesRegex(UserError, "CFOP allowed in the NFGas"):
            self.document.action_document_confirm()

    @mute_logger("brazil_fiscal_client.fiscal_client")
    def test_nfgas_send_and_cancel(self):
        """Authorization and cancellation against a simulated authorizer."""
        document = self.document
        document.action_document_confirm()
        key = document.document_key
        with mock.patch.object(
            NfgasClient,
            "_post",
            return_value=self._soap("NFGasRecepcao", RET_NFGAS % {"key": key}),
        ) as post:
            document.action_document_send()
        self.assertIn("nfgas-homologacao.svrs.rs.gov.br", post.call_args.args[0])
        self.assertIn(
            "NFGas/wsdl/NFGasRecepcao/NFGasRecepcao",
            post.call_args.kwargs["headers"]["content-type"],
        )
        sent = re.search(r"nfgasDadosMsg[^>]*>([^<]+)<", post.call_args.kwargs["data"])
        sent_xml = gzip.decompress(base64.b64decode(sent.group(1))).decode()
        self.assertIn(f'Id="NFGas{key}"', sent_xml)
        self.assertEqual(document.state_edoc, "autorizada")
        self.assertEqual(document.authorization_protocol, "3352600000000001")

        def event_response(status, reason):
            return self._soap(
                "NFGasRecepcaoEvento",
                RET_EVENTO % {"status": status, "reason": reason, "key": key},
            )

        # a refusal keeps the document authorized and the event recorded
        with mock.patch.object(
            NfgasClient, "_post", return_value=event_response("220", "Rejeicao: prazo")
        ):
            document._document_cancel("Fatura emitida em duplicidade")
        self.assertEqual(document.state_edoc, "autorizada")
        self.assertEqual(document.cancel_event_id.status_code, "220")

        with mock.patch.object(
            NfgasClient,
            "_post",
            return_value=event_response("135", "Evento registrado e vinculado"),
        ) as post:
            document._document_cancel("Fatura emitida em duplicidade")
        data = post.call_args.kwargs["data"]
        self.assertIn(f'Id="ID110111{key}001"', data)
        self.assertIn("<descEvento>Cancelamento</descEvento>", data)
        self.assertEqual(document.state_edoc, "cancelada")
        self.assertEqual(document.cancel_event_id.state, "done")
