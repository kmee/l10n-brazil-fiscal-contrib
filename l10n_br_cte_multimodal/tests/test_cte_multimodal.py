# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import importlib.resources

import nfelib
from lxml import etree
from xsdata.formats.dataclass.serializers import XmlSerializer

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

CTE_NS = {"cte": "http://www.portalfiscal.inf.br/cte"}
SCHEMA = ("cte", "schemas", "v4_0", "cteMultiModal_v4.00.xsd")


class TestCTeMultimodal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        schema = importlib.resources.files(nfelib.__name__).joinpath(*SCHEMA)
        with importlib.resources.as_file(schema) as path:
            cls.schema = etree.XMLSchema(etree.parse(str(path)))
        cls.cte = cls.env.ref("l10n_br_cte.demo_cte_lc_modal_dutoviario")
        cls.cte.write(
            {
                "transport_modal": "06",
                "cte40_COTM": "OTM-0001",
                "cte40_indNegociavel": "1",
            }
        )

    def _modal_xml(self):
        export_dict = {}
        self.cte._export_fields_cte_40_tcte_infmodal([], None, export_dict)
        xml = XmlSerializer().render(
            export_dict["any_element"], ns_map={None: CTE_NS["cte"]}
        )
        root = etree.fromstring(xml.encode())
        self.assertTrue(self.schema.validate(root), self.schema.error_log)
        return root

    def test_multimodal_with_insurance(self):
        self.cte.write(
            {
                "cte40_multimodal_xSeg": "Seguradora Teste",
                "cte40_multimodal_CNPJ": "12.345.678/0001-95",
                "cte40_multimodal_nApol": "AP-123",
                "cte40_multimodal_nAver": "AV-456",
            }
        )
        root = self._modal_xml()
        self.assertEqual(root.tag, f"{{{CTE_NS['cte']}}}multimodal")
        self.assertEqual(root.findtext("cte:COTM", namespaces=CTE_NS), "OTM-0001")
        self.assertEqual(root.findtext("cte:indNegociavel", namespaces=CTE_NS), "1")
        self.assertEqual(
            root.findtext("cte:seg/cte:infSeg/cte:CNPJ", namespaces=CTE_NS),
            "12345678000195",
        )
        self.assertEqual(
            root.findtext("cte:seg/cte:nAver", namespaces=CTE_NS), "AV-456"
        )

    def test_multimodal_without_insurance(self):
        root = self._modal_xml()
        self.assertIsNone(root.find("cte:seg", namespaces=CTE_NS))

    def test_insurance_without_cnpj(self):
        self.cte.write(
            {
                "cte40_multimodal_xSeg": "Seguradora Teste",
                "cte40_multimodal_nApol": "AP-123",
                "cte40_multimodal_nAver": "AV-456",
            }
        )
        root = self._modal_xml()
        self.assertEqual(
            root.findtext("cte:seg/cte:infSeg/cte:CNPJ", namespaces=CTE_NS), ""
        )

    def test_missing_required_elements(self):
        self.cte.cte40_COTM = False
        with self.assertRaisesRegex(UserError, "COTM"):
            self.cte._export_cte_modal_multimodal()
        self.cte.write({"cte40_COTM": "OTM-0001", "cte40_multimodal_nApol": "AP-1"})
        with self.assertRaisesRegex(UserError, "Insurance Company, Insurance End"):
            self.cte._export_cte_modal_multimodal()
