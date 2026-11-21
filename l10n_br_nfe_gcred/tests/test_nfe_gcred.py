# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged

NFE_NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}


@tagged("post_install", "-at_install")
class TestNFeGCred(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.document = cls.env.ref("l10n_br_nfe.demo_nfe_natural_icms_7_resale")
        cls.product = cls.env.ref("product.product_product_9").with_company(
            cls.document.company_id
        )
        cls.product.write(
            {"nfe_cred_presumido_code": "SP000123", "nfe_cred_presumido_percent": 3.5}
        )
        cls.line = cls.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": cls.document.id,
                "name": "Presumed credit",
                "product_id": cls.product.id,
                "uom_id": cls.env.ref("uom.product_uom_kgm").id,
                "quantity": 2,
                "fiscal_operation_type": "out",
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_venda").id,
                "fiscal_operation_line_id": cls.env.ref(
                    "l10n_br_fiscal.fo_venda_revenda"
                ).id,
            }
        )

    def test_line_gets_credit_from_product(self):
        self.assertTrue(self.line.icms_base)
        self.assertEqual(
            [
                (g.nfe40_cCredPresumido, g.nfe40_pCredPresumido, g.nfe40_vCredPresumido)
                for g in self.line.nfe40_gCred
            ],
            [("SP000123", 3.5, round(self.line.icms_base * 0.035, 2))],
        )

    def test_nfe_xml_has_gcred(self):
        document = self.document
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
        groups = etree.fromstring(xml).findall(".//nfe:det/nfe:prod/nfe:gCred", NFE_NS)
        self.assertEqual(len(groups), 1)
        self.assertEqual(
            [
                groups[0].findtext(f"nfe:{tag}", namespaces=NFE_NS)
                for tag in ("cCredPresumido", "pCredPresumido", "vCredPresumido")
            ],
            [
                "SP000123",
                "3.5000",
                f"{self.line.nfe40_gCred.nfe40_vCredPresumido:.2f}",
            ],
        )

    def test_check_gcred(self):
        self.line.nfe40_gCred = [
            Command.create(
                {
                    "nfe40_cCredPresumido": f"SP00000{i}",
                    "nfe40_pCredPresumido": 1,
                    "nfe40_vCredPresumido": 1,
                }
            )
            for i in range(4)
        ]
        with self.assertRaisesRegex(UserError, "at most 4"):
            self.document._check_nfe40_gCred()
        self.line.nfe40_gCred[1:].unlink()
        self.line.nfe40_gCred.nfe40_cCredPresumido = "SP 1234"
        with self.assertRaisesRegex(UserError, "8 or 10 characters"):
            self.document._check_nfe40_gCred()

    def test_product_code_pattern(self):
        with self.assertRaises(ValidationError):
            self.product.nfe_cred_presumido_code = "SP123"
