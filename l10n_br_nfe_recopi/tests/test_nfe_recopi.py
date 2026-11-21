# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import date

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged

from ..models.document import is_valid_recopi_number

NFE_NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}
# example of the MOC 7.0, Visao Geral, section 8.5.3
RECOPI = "20131106114609734393"


@tagged("post_install", "-at_install")
class TestNFeRecopi(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.nfe = cls.env.ref("l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11")
        cls.line = cls.nfe.fiscal_line_ids
        cls.line.product_id.recopi_paper = True
        cls.nfe.recopi_number = RECOPI

    def test_nfe_xml_has_recopi(self):
        self.assertEqual(self.line.nfe40_nRECOPI, RECOPI)
        self.nfe.nfe40_detPag = [
            Command.create(
                {
                    "nfe40_indPag": "0",
                    "nfe40_tPag": "01",
                    "nfe40_vPag": self.nfe.amount_financial_total,
                }
            ),
        ]
        self.nfe.action_document_confirm()
        self.assertFalse(self.nfe.xml_error_message)
        xml = etree.fromstring(base64.b64decode(self.nfe.send_file_id.datas))
        self.assertEqual(
            xml.findtext(".//nfe:det/nfe:prod/nfe:nRECOPI", namespaces=NFE_NS), RECOPI
        )

    def test_recopi_number_validation(self):
        """Rule LB01-30 (rejection 350)."""
        today = date(2026, 1, 1)
        self.assertTrue(is_valid_recopi_number(RECOPI, today))
        for number in (
            "20131106114609734394",  # check digit
            "20121106114609734393",  # before 2013
            "20131306114609734393",  # month
            "2013110611460973439",  # length
        ):
            self.assertFalse(is_valid_recopi_number(number, today), number)
        self.assertFalse(is_valid_recopi_number(RECOPI, date(2013, 11, 5)))
        with self.assertRaises(ValidationError):
            self.nfe.recopi_number = "20131106114609734394"

    def test_nfce_refuses_recopi(self):
        """Rule LB01-10 (rejection 348)."""
        self.nfe.document_type_id = self.env.ref("l10n_br_fiscal.document_65")
        with self.assertRaisesRegex(UserError, "NFC-e"):
            self.nfe._check_nfe40_nRECOPI()
