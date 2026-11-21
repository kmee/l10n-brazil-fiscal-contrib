# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

NFE_NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}


@tagged("post_install", "-at_install")
class TestNFeObsItem(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.document = cls.env.ref("l10n_br_nfe.demo_nfe_natural_icms_7_resale")
        cls.obs_item = cls.env["nfe.40.obsitem"].create(
            {
                "nfe40_obsCont": cls.env["nfe.40.det_obscont"]
                .create({"nfe40_xCampo": "Pedido", "nfe40_xTexto": "PO-123"})
                .id,
                "nfe40_obsFisco": cls.env["nfe.40.det_obsfisco"]
                .create({"nfe40_xCampo": "Lote", "nfe40_xTexto": "L-9"})
                .id,
            }
        )
        cls.product = cls.env.ref("product.product_product_9")
        cls.product.nfe40_obsItem = cls.obs_item
        cls.line = cls.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": cls.document.id,
                "name": "Observed item",
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

    def test_nfe_xml_has_obs_item(self):
        self.assertEqual(self.line.nfe40_obsItem, self.obs_item)
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
        nodes = etree.fromstring(xml).findall(".//nfe:det/nfe:obsItem", NFE_NS)
        self.assertEqual(len(nodes), 1)
        obs_cont = nodes[0].find("nfe:obsCont", NFE_NS)
        obs_fisco = nodes[0].find("nfe:obsFisco", NFE_NS)
        self.assertEqual(
            (
                obs_cont.get("xCampo"),
                obs_cont.findtext("nfe:xTexto", namespaces=NFE_NS),
                obs_fisco.get("xCampo"),
                obs_fisco.findtext("nfe:xTexto", namespaces=NFE_NS),
            ),
            ("Pedido", "PO-123", "Lote", "L-9"),
        )

    def test_obs_length(self):
        for vals in (
            {"nfe40_xCampo": "x" * 21, "nfe40_xTexto": "ok"},
            {"nfe40_xCampo": "ok", "nfe40_xTexto": "x" * 61},
            {"nfe40_xCampo": " ", "nfe40_xTexto": "ok"},
        ):
            with self.assertRaises(ValidationError):
                self.env["nfe.40.det_obscont"].create(vals)
