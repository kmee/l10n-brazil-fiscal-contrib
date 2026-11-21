# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

NFE_NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}


@tagged("post_install", "-at_install")
class TestNFeRetirada(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.nfe = cls.env.ref("l10n_br_nfe.demo_nfe_same_state")
        cls.company = cls.nfe.company_id
        cls.warehouse_partner = cls.env["res.partner"].create(
            {
                "name": "General Warehouse",
                "is_company": True,
                "vat": "47.018.352/0001-38",
                "street_name": "Estrada do Caminho Velho",
                "street_number": "100",
                "district": "Jardim Nova Cidade",
                "zip": "07252-312",
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.env.ref("base.state_br_sp").id,
                "city_id": cls.env.ref("l10n_br_base.city_3518800").id,
            }
        )

    def _picking_from(self, partner):
        warehouse = self.env["stock.warehouse"].create(
            {
                "name": f"WH {partner.name}",
                "code": f"W{partner.id % 10000}",
                "company_id": self.company.id,
                "partner_id": partner.id,
            }
        )
        return self.env["stock.picking"].create(
            {
                "picking_type_id": warehouse.out_type_id.id,
                "location_id": warehouse.lot_stock_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "company_id": self.company.id,
            }
        )

    def test_pickup_address_from_warehouse(self):
        picking = self._picking_from(self.warehouse_partner)
        self.assertEqual(
            self.nfe._nfe40_retirada_from_pickings(picking), self.warehouse_partner
        )
        company_picking = self._picking_from(self.company.partner_id)
        self.assertFalse(self.nfe._nfe40_retirada_from_pickings(company_picking))
        self.assertFalse(
            self.nfe._nfe40_retirada_from_pickings(picking | company_picking)
        )

    def test_nfe_xml_has_retirada(self):
        self.nfe.nfe40_retirada = self.warehouse_partner
        self.nfe.action_document_confirm()
        self.assertEqual(self.nfe.state_edoc, "a_enviar")
        self.assertFalse(self.nfe.xml_error_message)
        xml = base64.b64decode(self.nfe.authorization_event_id.file_request_id.datas)
        retirada = etree.fromstring(xml).find(".//nfe:infNFe/nfe:retirada", NFE_NS)
        self.assertEqual(
            [
                retirada.findtext(f"nfe:{tag}", namespaces=NFE_NS)
                for tag in ("CNPJ", "xLgr", "nro", "cMun", "UF")
            ],
            ["47018352000138", "Estrada do Caminho Velho", "100", "3518800", "SP"],
        )

    def test_incomplete_pickup_address_blocks_confirmation(self):
        self.warehouse_partner.write({"vat": False, "street_number": False})
        self.nfe.nfe40_retirada = self.warehouse_partner
        with self.assertRaisesRegex(UserError, "CNPJ or CPF, number"):
            self.nfe.action_document_confirm()
