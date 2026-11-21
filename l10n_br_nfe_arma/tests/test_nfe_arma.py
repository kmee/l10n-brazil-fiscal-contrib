# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

NFE_NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}


@tagged("post_install", "-at_install")
class TestNFeArma(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.nfe = cls.env.ref("l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11")
        # on 16.0 the company dependent fiscal type is not copied, and
        # without it the item gets no ICMS (copied in the company of the
        # environment, where the document line reads it, as 18.0 does)
        product = cls.env.ref("product.product_product_20")
        cls.product = product.copy(
            {
                "fiscal_type": product.fiscal_type,
                "name": "Pistol",
                "default_code": "PISTOL-1",
                "detailed_type": "product",
                "tracking": "serial",
                "arma_type": "0",
                "arma_description": "PISTOLA CAL 9MM MARCA X 15 TIROS",
            }
        )
        cls.lot = cls._create_lot("SN001", "BC001")
        cls.line = cls.nfe.fiscal_line_ids
        cls.line.product_id = cls.product

    @classmethod
    def _create_lot(cls, name, barrel):
        return cls.env["stock.lot"].create(
            {
                "name": name,
                "product_id": cls.product.id,
                "company_id": cls.nfe.company_id.id,
                "arma_barrel_number": barrel,
            }
        )

    def test_nfe_xml_has_arma(self):
        self.line._nfe40_fill_arma(self.lot)
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
        arma = xml.find(".//nfe:det/nfe:prod/nfe:arma", NFE_NS)
        self.assertEqual(
            [
                arma.findtext(f"nfe:{tag}", namespaces=NFE_NS)
                for tag in ("tpArma", "nSerie", "nCano", "descr")
            ],
            ["0", "SN001", "BC001", "PISTOLA CAL 9MM MARCA X 15 TIROS"],
        )

    def test_one_group_per_serial_number(self):
        self.line._nfe40_fill_arma(self.lot | self._create_lot("SN002", False))
        self.assertEqual(
            sorted(self.line.nfe40_arma.mapped("nfe40_nSerie")), ["SN001", "SN002"]
        )
        with self.assertRaisesRegex(UserError, "SN002"):
            self.nfe._check_nfe40_arma()
        # rule L01-10 (rejection 738)
        self.nfe.document_type_id = self.env.ref("l10n_br_fiscal.document_65")
        with self.assertRaisesRegex(UserError, "NFC-e"):
            self.nfe._check_nfe40_arma()
