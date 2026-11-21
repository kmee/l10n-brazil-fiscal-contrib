# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree
from nfelib.nfse.bindings.v1_0.dps_v1_01 import Dps

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_br_fiscal.constants.fiscal import PROCESSADOR_OCA
from odoo.addons.l10n_br_nfse_nacional.constants.nfse_nacional import (
    PROVEDOR_NFSE_NACIONAL,
)

NS = {"nfse": "http://www.sped.fazenda.gov.br/nfse"}


# the export builds the remaining spec models, which an at_install
# transaction would roll back
@tagged("post_install", "-at_install")
class TestNfseObra(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.nfse = cls.env.ref("l10n_br_nfse_nacional.demo_nfse_lc")
        cls.nfse.company_id.write(
            {
                "processador_edoc": PROCESSADOR_OCA,
                "provedor_nfse": PROVEDOR_NFSE_NACIONAL,
            }
        )
        cls.line = cls.nfse.fiscal_line_ids[0]
        cls.obra_code = cls.env["l10n_br_fiscal.national.taxation.code"].create(
            {"name": "Construction by contract", "code": "07.02.01"}
        )
        cls.site = cls.env["res.partner"].create(
            {
                "name": "Construction Site",
                "street_name": "Rua das Obras",
                "street_number": "100",
                "district": "Centro",
                "zip": "89010-000",
                "city_id": cls.env.ref("l10n_br_base.city_4202404").id,
                "country_id": cls.env.ref("base.br").id,
            }
        )

    def _obra(self):
        xml = self.nfse._serialize([])[0].to_xml()
        self.assertEqual(Dps.schema_validation(xml), [])
        root = etree.fromstring(xml.encode())
        return root.find("./nfse:infDPS/nfse:serv/nfse:obra", NS)

    def test_obra_codes_from_construction_site(self):
        self.site.write({"nfse_cno": "900012345678", "nfse_insc_imob_fisc": "IM-77"})
        self.line.national_taxation_code_id = self.obra_code
        self.nfse.partner_shipping_id = self.site
        self.assertEqual(self.nfse.civil_construction_code, "900012345678")
        obra = self._obra()
        self.assertEqual(obra.findtext("nfse:cObra", namespaces=NS), "900012345678")
        self.assertEqual(obra.findtext("nfse:inscImobFisc", namespaces=NS), "IM-77")
        self.assertIsNone(obra.find("nfse:end", NS))

    def test_obra_address_without_codes(self):
        self.nfse.partner_shipping_id = self.site
        self.assertIsNone(self._obra(), "only obra services report an address")
        self.line.national_taxation_code_id = self.obra_code
        obra = self._obra()
        self.assertEqual(obra.findtext("nfse:end/nfse:CEP", namespaces=NS), "89010000")
        self.assertEqual(obra.findtext("nfse:end/nfse:nro", namespaces=NS), "100")

    def test_obra_group_required(self):
        """Rule E0370."""
        self.line.national_taxation_code_id = self.obra_code
        with self.assertRaisesRegex(UserError, "E0370"):
            self.nfse._serialize([])
