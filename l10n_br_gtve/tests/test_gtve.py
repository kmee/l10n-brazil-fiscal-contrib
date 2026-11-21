# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import contextlib
import gzip
import importlib.resources
from types import SimpleNamespace
from unittest import mock

import nfelib
from erpbrasil.edoc.cte import TransmissaoCTE
from lxml import etree
from nfelib.nfe.ws.edoc_legacy import CTeAdapter

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_REJEITADA,
)

NS = {"cte": "http://www.portalfiscal.inf.br/cte"}

RET_GTVE = """<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
<soap:Body><cteRecepcaoGTVeResult
 xmlns="http://www.portalfiscal.inf.br/cte/wsdl/CTeRecepcaoGTVeV4">
<retGTVe versao="4.00" xmlns="http://www.portalfiscal.inf.br/cte">
<tpAmb>2</tpAmb><cUF>35</cUF><verAplic>SP-CTe-01</verAplic>
<cStat>{status}</cStat><xMotivo>{motive}</xMotivo>{protocol}
</retGTVe></cteRecepcaoGTVeResult></soap:Body></soap:Envelope>"""

PROT_GTVE = """<protCTe versao="4.00"><infProt><tpAmb>2</tpAmb>
<verAplic>SP-CTe-01</verAplic><chCTe>{key}</chCTe>
<dhRecbto>2026-11-20T10:05:00-03:00</dhRecbto><nProt>135260000000001</nProt>
<cStat>100</cStat><xMotivo>Autorizado o uso do CT-e</xMotivo></infProt>
</protCTe>"""


def _schema(name):
    path = importlib.resources.files(nfelib.__name__).joinpath(
        "cte", "schemas", "v4_0", name
    )
    with importlib.resources.as_file(path) as schema_path:
        return etree.XMLSchema(etree.parse(str(schema_path)))


@contextlib.contextmanager
def _fake_client(self, url, *args, **kwargs):
    yield None


@tagged("post_install", "-at_install")
class TestGTVe(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        document_type = cls.env.ref("l10n_br_gtve.document_64")
        serie = cls.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "1",
                "name": "GTV-e 1",
                "document_type_id": document_type.id,
                "company_id": company.id,
            }
        )
        cls.gtve = cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": company.id,
                "document_type_id": document_type.id,
                "document_serie_id": serie.id,
                "document_number": "1",
                "document_date": "2026-11-20 13:00:00",
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_venda").id,
                "fiscal_operation_type": "out",
                "processador_edoc": "oca",
                "cte_environment": "2",
                "partner_id": cls.env.ref("l10n_br_base.res_partner_cliente1_sp").id,
                "partner_sendering_id": cls.env.ref(
                    "l10n_br_base.res_partner_cliente2_sp"
                ).id,
                "partner_shipping_id": cls.env.ref(
                    "l10n_br_base.res_partner_cliente3_am"
                ).id,
                "transport_modal": "01",
                "gtve_cfop_id": cls.env.ref("l10n_br_fiscal.cfop_5359").id,
                "gtve_departure_date": "2026-11-20 13:10:00",
                "gtve_arrival_date": "2026-11-20 15:30:00",
                "gtve_load_quantity": 2,
                "gtve_species_ids": [
                    Command.create({"cte40_tpEspecie": "1", "cte40_vEspecie": 1500}),
                    Command.create(
                        {
                            "cte40_tpEspecie": "3",
                            "cte40_vEspecie": 10,
                            "cte40_tpNumerario": "2",
                            "cte40_xMoedaEstr": "DOLAR",
                        }
                    ),
                ],
                "gtve_vehicle_ids": [
                    Command.create({"cte40_placa": "ABC1D23", "cte40_UF": "SP"})
                ],
            }
        )
        cls.gtve.action_document_confirm()

    def _sent_xml(self):
        return base64.b64decode(self.gtve.send_file_id.datas)

    def _send(self, status, motive, protocol=""):
        response = RET_GTVE.format(status=status, motive=motive, protocol=protocol)
        fake = SimpleNamespace(
            text=response,
            content=response.encode(),
            raise_for_status=lambda: None,
        )
        with (
            mock.patch.object(TransmissaoCTE, "cliente", _fake_client),
            mock.patch.object(TransmissaoCTE, "enviar", return_value=fake) as send,
        ):
            self.gtve.action_document_send()
        return send

    def test_export_signed_and_valid(self):
        self.assertEqual(self.gtve.state_edoc, SITUACAO_EDOC_A_ENVIAR)
        self.assertFalse(self.gtve.xml_error_message)
        root = etree.fromstring(self._sent_xml())
        schema = _schema("GTVe_v4.00.xsd")
        self.assertTrue(schema.validate(root), schema.error_log)
        key = self.gtve.document_key
        self.assertEqual(key[20:22], "64")
        inf = root.find("cte:infCte", NS)
        self.assertEqual(inf.get("Id"), f"CTe{key}")
        self.assertEqual(inf.findtext("cte:ide/cte:mod", namespaces=NS), "64")
        self.assertEqual(inf.findtext("cte:ide/cte:tpCTe", namespaces=NS), "4")
        self.assertEqual(inf.findtext("cte:ide/cte:tpServ", namespaces=NS), "9")
        self.assertEqual(inf.findtext("cte:ide/cte:toma/cte:toma", namespaces=NS), "0")
        self.assertEqual(
            inf.findtext("cte:rem/cte:xNome", namespaces=NS),
            "CTE EMITIDO EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL",
        )
        species = inf.findall("cte:detGTV/cte:infEspecie", NS)
        self.assertEqual(
            [s.findtext("cte:tpEspecie", namespaces=NS) for s in species], ["1", "3"]
        )
        self.assertIsNone(species[0].find("cte:xMoedaEstr", NS))
        self.assertEqual(species[1].findtext("cte:xMoedaEstr", namespaces=NS), "DOLAR")
        self.assertIn(
            f"chCTe={key}",
            root.findtext("cte:infCTeSupl/cte:qrCodCTe", namespaces=NS),
        )

    def test_send_authorized(self):
        send = self._send(
            "100",
            "Autorizado o uso do CT-e",
            PROT_GTVE.format(key=self.gtve.document_key),
        )
        operation, message = send.call_args.args
        self.assertEqual(operation, "cteRecepcaoGTVe")
        self.assertEqual(gzip.decompress(base64.b64decode(message)), self._sent_xml())
        self.assertEqual(self.gtve.state_edoc, SITUACAO_EDOC_AUTORIZADA)
        self.assertEqual(self.gtve.authorization_protocol, "135260000000001")
        proc = etree.fromstring(base64.b64decode(self.gtve.authorization_file_id.datas))
        schema = _schema("procGTVe_v4.00.xsd")
        self.assertTrue(schema.validate(proc), schema.error_log)

    def test_send_rejected(self):
        self._send("999", "Rejeicao: erro nao catalogado")
        self.assertEqual(self.gtve.state_edoc, SITUACAO_EDOC_REJEITADA)
        self.assertEqual(self.gtve.status_code, "999")

    def test_cancel(self):
        self._send(
            "100",
            "Autorizado o uso do CT-e",
            PROT_GTVE.format(key=self.gtve.document_key),
        )
        event = SimpleNamespace(
            envio_xml="<eventoCTe/>",
            resposta=SimpleNamespace(
                infEvento=SimpleNamespace(
                    cStat="135",
                    xMotivo="Evento registrado e vinculado a CT-e",
                    chCTe=self.gtve.document_key,
                    dhRegEvento="2026-11-20T11:00:00-03:00",
                    nProt="135260000000002",
                )
            ),
            retorno=SimpleNamespace(content=b"<retEventoCTe/>"),
        )
        with (
            mock.patch.object(
                CTeAdapter, "cancela_documento", return_value=mock.sentinel.evento
            ) as cancel,
            mock.patch.object(CTeAdapter, "enviar_lote_evento", return_value=event),
        ):
            self.gtve._document_cancel("Cancelamento de teste da GTV-e")
        self.assertEqual(cancel.call_args.kwargs["chave"], self.gtve.document_key)
        self.assertEqual(self.gtve.state_edoc, SITUACAO_EDOC_CANCELADA)

    def test_rules(self):
        self.gtve.gtve_service_taker = "4"
        ide = self.gtve.gtve_id._build_binding("cte", "40").ide
        self.assertIsNone(ide.toma)
        self.assertEqual(ide.tomaTerceiro.toma, "4")
        self.assertEqual(ide.tomaTerceiro.xNome, self.gtve.partner_id.legal_name)
        with self.assertRaisesRegex(UserError, "correction letter"):
            self.gtve._document_correction("Correcao")
        self.gtve.gtve_species_ids = False
        with self.assertRaisesRegex(UserError, "Transported Species"):
            self.gtve._check_gtve()
