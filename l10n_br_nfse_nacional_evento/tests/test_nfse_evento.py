# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

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
class TestNfseEvento(TransactionCase):
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
        cls.line.national_taxation_code_id = cls.env[
            "l10n_br_fiscal.national.taxation.code"
        ].create({"name": "Shows and concerts", "code": "12.07.01"})
        cls.venue = cls.env["res.partner"].create(
            {
                "name": "Event Venue",
                "street_name": "Rua dos Eventos",
                "street_number": "10",
                "district": "Centro",
                "zip": "89010-000",
                "city_id": cls.env.ref("l10n_br_base.city_4202404").id,
                "country_id": cls.env.ref("base.br").id,
            }
        )
        cls.nfse.write(
            {
                "nfse_event_name": "Summer Festival",
                "nfse_event_date_start": date(2026, 1, 10),
                "nfse_event_date_end": date(2026, 1, 12),
                "partner_shipping_id": cls.venue.id,
            }
        )

    def _event(self):
        xml = self.nfse._serialize([])[0].to_xml()
        self.assertEqual(Dps.schema_validation(xml), [])
        root = etree.fromstring(xml.encode())
        return root.find("./nfse:infDPS/nfse:serv/nfse:atvEvento", NS)

    def test_event_with_venue(self):
        event = self._event()
        self.assertEqual(event.findtext("nfse:xNome", namespaces=NS), "Summer Festival")
        self.assertEqual(event.findtext("nfse:dtIni", namespaces=NS), "2026-01-10")
        self.assertEqual(event.findtext("nfse:dtFim", namespaces=NS), "2026-01-12")
        self.assertEqual(
            event.findtext("nfse:end/nfse:xLgr", namespaces=NS), "Rua dos Eventos"
        )

    def test_event_with_municipal_code(self):
        self.nfse.nfse_event_code = "EVT-2026-01"
        event = self._event()
        self.assertEqual(event.findtext("nfse:idAtvEvt", namespaces=NS), "EVT-2026-01")
        self.assertIsNone(event.find("nfse:end", NS))

    def test_event_group_required(self):
        """Rule E0390."""
        self.nfse.nfse_event_name = False
        with self.assertRaisesRegex(UserError, "E0390"):
            self.nfse._serialize([])
