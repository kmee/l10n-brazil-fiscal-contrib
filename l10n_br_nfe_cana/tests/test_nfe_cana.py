# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged

NFE_NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}


@tagged("post_install", "-at_install")
class TestNFeCana(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.cana = cls.env["nfe.40.cana"].create(
            {
                "nfe40_safra": "2025/2026",
                "nfe40_ref": "10/2025",
                "nfe40_forDia": [
                    Command.create({"nfe40_dia": "1", "nfe40_qtde": 1000.5}),
                    Command.create({"nfe40_dia": "2", "nfe40_qtde": 2000}),
                ],
                "nfe40_qTotAnt": 500,
                "nfe40_deduc": [
                    Command.create({"nfe40_xDed": "CONSECANA", "nfe40_vDed": 10}),
                ],
                "nfe40_vFor": 300,
            }
        )

    def test_totals(self):
        cana = self.cana
        self.assertEqual(
            (
                cana.nfe40_qTotMes,
                cana.nfe40_qTotGer,
                cana.nfe40_vTotDed,
                cana.nfe40_vLiqFor,
            ),
            (3000.5, 3500.5, 10, 290),
        )

    def test_nfe_xml_has_cana(self):
        document = self.env.ref("l10n_br_nfe.demo_nfe_natural_icms_7_resale")
        document.nfe40_cana = self.cana
        document.nfe40_detPag = [
            Command.clear(),
            Command.create(
                {
                    "nfe40_indPag": "0",
                    "nfe40_tPag": "01",
                    "nfe40_vPag": document.amount_financial_total,
                }
            ),
        ]
        document.action_document_confirm()
        self.assertFalse(document.xml_error_message)
        xml = base64.b64decode(document.authorization_event_id.file_request_id.datas)
        cana = etree.fromstring(xml).find(".//nfe:infNFe/nfe:cana", NFE_NS)
        self.assertEqual(cana.findtext("nfe:ref", namespaces=NFE_NS), "10/2025")
        self.assertEqual(
            [d.get("dia") for d in cana.findall("nfe:forDia", NFE_NS)], ["1", "2"]
        )
        self.assertEqual(float(cana.findtext("nfe:qTotGer", namespaces=NFE_NS)), 3500.5)
        self.assertEqual(cana.findtext("nfe:vLiqFor", namespaces=NFE_NS), "290.00")

    def test_nfce_refuses_cana(self):
        """Rule ZC01-10."""
        document = self.env.ref("l10n_br_nfe.demo_nfce_same_state")
        document.nfe40_cana = self.cana
        with self.assertRaisesRegex(UserError, "NFC-e"):
            document._check_nfe40_cana()

    def test_layout_constraints(self):
        with self.assertRaises(ValidationError):
            self.cana.nfe40_ref = "13/2025"
        with self.assertRaises(ValidationError):
            self.cana.nfe40_forDia = [Command.create({"nfe40_dia": "1"})]
        with self.assertRaises(ValidationError):
            self.cana.nfe40_forDia.nfe40_dia = "32"
