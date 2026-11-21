# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged

NFE_NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}
VEHICLE_MODEL = {
    "nfe40_tpOp": "1",
    "nfe40_cCor": "1",
    "nfe40_xCor": "BRANCA",
    "nfe40_pot": "110",
    "nfe40_cilin": "1600",
    "nfe40_pesoL": "1100",
    "nfe40_pesoB": "1500",
    "nfe40_tpComb": "16",
    "nfe40_CMT": "1.5000",
    "nfe40_dist": "2500",
    "nfe40_anoMod": "2026",
    "nfe40_anoFab": "2026",
    "nfe40_tpPint": "S",
    "nfe40_tpVeic": "6",
    "nfe40_espVeic": "1",
    "nfe40_VIN": "N",
    "nfe40_condVeic": "1",
    "nfe40_cMod": "123456",
    "nfe40_cCorDENATRAN": "04",
    "nfe40_lota": "5",
    "nfe40_tpRest": "0",
}


@tagged("post_install", "-at_install")
class TestNFeVeic(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.nfe = cls.env.ref("l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11")
        cls.product = cls.env.ref("product.product_product_20").copy(
            {
                "name": "Car",
                "default_code": "CAR-1",
                "is_storable": True,
                "tracking": "serial",
                "nfe40_veicProd": cls.env["nfe.40.veicprod"].create(VEHICLE_MODEL).id,
            }
        )
        cls.lot = cls._create_lot("9BWZZZ377VT004251")
        cls.line = cls.nfe.fiscal_line_ids
        cls.line.product_id = cls.product

    @classmethod
    def _create_lot(cls, name):
        return cls.env["stock.lot"].create(
            {
                "name": name,
                "product_id": cls.product.id,
                "company_id": cls.nfe.company_id.id,
                "vehicle_serial": "4251",
                "vehicle_engine_number": "ENG4251",
            }
        )

    def test_nfe_xml_has_veicprod(self):
        self.line._nfe40_fill_veicprod(self.lot)
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
        veic = xml.find(".//nfe:det/nfe:prod/nfe:veicProd", NFE_NS)
        self.assertEqual(
            [
                veic.findtext(f"nfe:{tag}", namespaces=NFE_NS)
                for tag in ("chassi", "nSerie", "nMotor", "xCor")
            ],
            ["9BWZZZ377VT004251", "4251", "ENG4251", "BRANCA"],
        )

    def test_one_vehicle_per_item(self):
        lots = self.lot | self._create_lot("9BWZZZ377VT004252")
        self.line._nfe40_fill_veicprod(lots)
        self.assertFalse(self.line.nfe40_veicProd)

    def test_rules(self):
        self.lot.vehicle_engine_number = False
        self.line._nfe40_fill_veicprod(self.lot)
        with self.assertRaisesRegex(UserError, "required"):
            self.nfe._check_nfe40_veicprod()
        # rule J01-10 (rejection 736)
        self.nfe.document_type_id = self.env.ref("l10n_br_fiscal.document_65")
        with self.assertRaisesRegex(UserError, "NFC-e"):
            self.nfe._check_nfe40_veicprod()
        with self.assertRaises(ValidationError):
            self.line.nfe40_veicProd.nfe40_chassi = "9BWZZZ377VT00425"
