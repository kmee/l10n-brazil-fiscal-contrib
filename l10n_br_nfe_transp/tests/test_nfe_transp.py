# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

NFE_NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}


@tagged("post_install", "-at_install")
class TestNFeTransp(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.nfe = cls.env.ref("l10n_br_nfe.demo_nfe_same_state")
        cls.carrier = cls.env.ref("l10n_br_delivery.test_br_delivery_carrier").copy()
        cls.vehicle = cls._create_vehicle("Truck", "abc-1d23", "123456789")
        cls.trailer = cls._create_vehicle("Trailer", "DEF4567", False)
        cls.trailer.carrier_id = False

    @classmethod
    def _create_vehicle(cls, name, plate, rntc):
        return cls.env["l10n_br_delivery.carrier.vehicle"].create(
            {
                "name": name,
                "plate": plate,
                "rntc_code": rntc,
                "state_id": cls.env.ref("base.state_br_sp").id,
                "carrier_id": cls.carrier.id,
                "active": True,
            }
        )

    def _text(self, node, path):
        return node.findtext(path, namespaces=NFE_NS)

    def test_vehicle_from_carrier(self):
        self.nfe.carrier_id = self.carrier
        self.assertEqual(self.nfe.transport_vehicle_id, self.vehicle)

    def test_nfe_xml_has_vehicle_trailer_and_retention(self):
        self.nfe.write(
            {
                "transport_vehicle_id": self.vehicle.id,
                "transport_trailer_ids": [(6, 0, self.trailer.ids)],
                "ret_transp_service_value": 200.0,
                "ret_transp_percent": 12.0,
                "ret_transp_cfop_id": self.env["l10n_br_fiscal.cfop"]
                .search([("code", "=", "5352")], limit=1)
                .id,
            }
        )
        self.assertEqual(self.nfe.ret_transp_value, 24.0)
        self.nfe.action_document_confirm()
        self.assertEqual(self.nfe.state_edoc, "a_enviar")
        self.assertFalse(self.nfe.xml_error_message)
        xml = base64.b64decode(self.nfe.authorization_event_id.file_request_id.datas)
        transp = etree.fromstring(xml).find(".//nfe:infNFe/nfe:transp", NFE_NS)
        self.assertEqual(
            [
                self._text(transp, path)
                for path in (
                    "nfe:veicTransp/nfe:placa",
                    "nfe:veicTransp/nfe:UF",
                    "nfe:veicTransp/nfe:RNTC",
                    "nfe:reboque/nfe:placa",
                    "nfe:retTransp/nfe:vServ",
                    "nfe:retTransp/nfe:vBCRet",
                    "nfe:retTransp/nfe:pICMSRet",
                    "nfe:retTransp/nfe:vICMSRet",
                    "nfe:retTransp/nfe:CFOP",
                    "nfe:retTransp/nfe:cMunFG",
                )
            ],
            [
                "ABC1D23",
                "SP",
                "123456789",
                "DEF4567",
                "200.00",
                "200.00",
                "12.00",
                "24.00",
                "5352",
                self.nfe.company_id.partner_id.city_id.ibge_code,
            ],
        )

    def test_interstate_operation_omits_vehicle(self):
        """Rule X02-20 (rejection 868)."""
        self.nfe.write(
            {
                "partner_id": self.env.ref("l10n_br_base.res_partner_cliente5_pe").id,
                "transport_vehicle_id": self.vehicle.id,
                "transport_trailer_ids": [(6, 0, self.trailer.ids)],
            }
        )
        self.assertEqual(self.nfe.nfe40_idDest, "2")
        xsd_fields = ["nfe40_modFrete", "nfe40_veicTransp", "nfe40_reboque"]
        export_dict = {}
        self.nfe._export_fields_nfe_40_transp(xsd_fields, None, export_dict)
        self.assertEqual((xsd_fields, export_dict), (["nfe40_modFrete"], {}))

    def test_invalid_plate_blocks_confirmation(self):
        self.vehicle.plate = "AB-12"
        self.nfe.transport_vehicle_id = self.vehicle
        with self.assertRaisesRegex(UserError, "plate must have 7"):
            self.nfe.action_document_confirm()
