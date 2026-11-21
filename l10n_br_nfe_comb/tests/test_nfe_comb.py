# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged

NFE_NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}
TAGS = ("cProdANP", "descANP", "UFCons", "origComb/nfe:pOrig")


@tagged("post_install", "-at_install")
class TestNFeComb(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.nfe = cls.env.ref("l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11")
        cls.comb = cls.env["nfe.40.comb"].create(
            {
                "nfe40_cProdANP": "320102001",
                "nfe40_descANP": "GASOLINA C COMUM",
                "nfe40_origComb": [
                    Command.create(
                        {
                            "nfe40_indImport": "0",
                            "nfe40_cUFOrig": "35",
                            "nfe40_pOrig": 100,
                        }
                    )
                ],
            }
        )
        # on 16.0 the company dependent fiscal type is not copied, and
        # without it the item gets no ICMS (copied in the company of the
        # environment, where the document line reads it, as 18.0 does)
        product = cls.env.ref("product.product_product_20")
        cls.product = product.copy(
            {
                "name": "Gasoline",
                "default_code": "GAS-C",
                "fiscal_type": product.fiscal_type,
            }
        )
        cls.product.nfe40_comb = cls.comb
        cls.line = cls.nfe.fiscal_line_ids
        cls.line.product_id = cls.product

    def _xml_comb(self):
        xml = base64.b64decode(self.nfe.send_file_id.datas)
        return etree.fromstring(xml).find(".//nfe:det/nfe:prod/nfe:comb", NFE_NS)

    def _confirm(self):
        self.nfe.nfe40_detPag = [
            Command.clear(),
            Command.create(
                {
                    "nfe40_indPag": "0",
                    "nfe40_tPag": "01",
                    "nfe40_vPag": self.nfe.amount_financial_total,
                }
            ),
        ]
        self.nfe.action_document_confirm()

    def test_nfe_xml_has_comb(self):
        self.assertEqual(self.line.nfe40_comb, self.comb)
        self._confirm()
        self.assertFalse(self.nfe.xml_error_message)
        comb = self._xml_comb()
        self.assertEqual(
            [comb.findtext(f"nfe:{tag}", namespaces=NFE_NS) for tag in TAGS],
            ["320102001", "GASOLINA C COMUM", "SP", "100"],
        )

    def test_glp_rules(self):
        """Rules LA03c-10 (rejection 461) and LA03c-20 (rejection 855)."""
        self.comb.write(
            {"nfe40_cProdANP": "210203001", "nfe40_pGLP": 60, "nfe40_pGNn": 30}
        )
        with self.assertRaisesRegex(UserError, "855"):
            self._confirm()
        self.comb.nfe40_pGNi = 10
        self._confirm()
        self.assertFalse(self.nfe.xml_error_message)
        self.assertEqual(
            self._xml_comb().findtext("nfe:pGLP", namespaces=NFE_NS), "60.00"
        )
        self.comb.nfe40_cProdANP = "320102001"
        self.assertIn("461", "".join(self.line._nfe40_comb_errors()))

    def _errors(self):
        return "".join(self.line._nfe40_comb_errors())

    def test_meter_and_origin_rules(self):
        """Rules LA11-20, LA16-10 (rejections 379 and 380) and LA21-10
        (rejection 958)."""
        self.comb.nfe40_encerrante = self.env["nfe.40.encerrante"].create(
            {
                "nfe40_nBico": "1",
                "nfe40_nTanque": "1",
                "nfe40_vEncIni": 10,
                "nfe40_vEncFin": 10,
            }
        )
        self.comb.nfe40_origComb.nfe40_pOrig = 90
        errors = self._errors()
        for rejection in ("379", "380", "958"):
            self.assertIn(rejection, errors)

    def test_anp_code_pattern(self):
        with self.assertRaises(ValidationError):
            self.comb.nfe40_cProdANP = "3201020"
