# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

NFE_NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}
NFE_TAGS = ("xNEmp", "xPed", "xCont")


@tagged("post_install", "-at_install")
class TestNFeCompra(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.nfe = cls.env.ref("l10n_br_nfe.demo_nfe_same_state")
        # l10n_br_nfe 16.0 does not fill the payment of the demo NF-e
        cls.nfe.nfe40_detPag = [
            Command.clear(),
            Command.create(
                {
                    "nfe40_indPag": "0",
                    "nfe40_tPag": "01",
                    "nfe40_vPag": cls.nfe.amount_financial_total,
                }
            ),
        ]

    def _confirm(self):
        self.nfe.action_document_confirm()
        self.assertEqual(self.nfe.state_edoc, "a_enviar")
        self.assertFalse(self.nfe.xml_error_message)
        xml = base64.b64decode(self.nfe.authorization_event_id.file_request_id.datas)
        return etree.fromstring(xml)

    def test_purchase_order_from_lines(self):
        lines = self.nfe.fiscal_line_ids
        lines.partner_order = "PO-1"
        self.assertEqual(self.nfe.purchase_order_ref, "PO-1")
        lines[0].partner_order = "PO-2"
        self.assertFalse(self.nfe.purchase_order_ref)

    def test_nfe_xml_has_compra(self):
        self.nfe.fiscal_line_ids.partner_order = "PO-1"
        self.nfe.purchase_commitment_note = "2026NE000123"
        self.nfe.purchase_contract_ref = "CT 45/2026"
        root = self._confirm()
        compra = root.find(".//nfe:infNFe/nfe:compra", NFE_NS)
        self.assertEqual(
            [compra.findtext(f"nfe:{tag}", namespaces=NFE_NS) for tag in NFE_TAGS],
            ["2026NE000123", "PO-1", "CT 45/2026"],
        )

    def test_no_compra_in_nfce(self):
        nfce = self.env.ref("l10n_br_nfe.demo_nfce_same_state")
        nfce.purchase_commitment_note = "2026NE000123"
        export_dict = {}
        nfce._export_tag_nfe_40_compra([], None, export_dict)
        self.assertFalse(export_dict)

    def test_public_body_relief_requires_commitment_note(self):
        """Rule ZB02-10 (rejection 359)."""
        self.nfe.fiscal_line_ids[0].icms_relief_id = self.env.ref(
            "l10n_br_fiscal.icms_relief_8"
        )
        with self.assertRaisesRegex(UserError, "commitment note"):
            self.nfe.action_document_confirm()
