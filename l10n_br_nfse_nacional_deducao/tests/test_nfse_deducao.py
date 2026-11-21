# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree
from nfelib.nfse.bindings.v1_0.dps_v1_01 import Dps

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_br_fiscal.constants.fiscal import PROCESSADOR_OCA
from odoo.addons.l10n_br_nfse_nacional.constants.nfse_nacional import (
    PROVEDOR_NFSE_NACIONAL,
)

NS = {"nfse": "http://www.sped.fazenda.gov.br/nfse"}
SUPPLIER_NFSE_KEY = "42024042123456780001950000000000000126010000000001"


# the export builds the remaining spec models, which an at_install
# transaction would roll back
@tagged("post_install", "-at_install")
class TestNfseDeducao(TransactionCase):
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
        cls.supplier_nfse = cls.env.ref("l10n_br_nfse_nacional.demo_nfse_sn")
        cls.supplier_nfse.nfse_key = SUPPLIER_NFSE_KEY
        cls.supplier = cls.env.ref("l10n_br_nfse_nacional.partner_toma_lc")
        cls.Adjustment = cls.env["l10n_br_nfse_nacional.bc.adjustment"]

    def _adjustment(self, **values):
        return self.Adjustment.create(
            dict(
                {
                    "document_id": self.nfse.id,
                    "adjustment_type": "2",
                    "source_document_id": self.supplier_nfse.id,
                    "supplier_id": self.supplier.id,
                    "document_amount": 30.0,
                    "applied_amount": 5.0,
                },
                **values,
            )
        )

    def _vajustebc(self):
        xml = self.nfse._serialize([])[0].to_xml()
        self.assertEqual(Dps.schema_validation(xml), [])
        root = etree.fromstring(xml.encode())
        return root.find("./nfse:infDPS/nfse:valores/nfse:vAjusteBC", NS)

    def test_adjustment_document_from_fiscal_document(self):
        adjustment = self._adjustment()
        self.assertEqual(adjustment.dfe_type, "1")
        self.assertEqual(adjustment.dfe_key, self.supplier_nfse.nfse_key)
        doc = self._vajustebc().find("nfse:documentos/nfse:docAjusteBC", NS)
        self.assertEqual(doc.findtext("nfse:tpAjusteBC", namespaces=NS), "2")
        self.assertEqual(doc.findtext("nfse:vAjusteAplic", namespaces=NS), "5.00")
        self.assertEqual(
            doc.findtext("nfse:dFeNacional/nfse:chaveDFe", namespaces=NS),
            self.supplier_nfse.nfse_key,
        )
        self.assertEqual(
            doc.findtext("nfse:fornec/nfse:CNPJ", namespaces=NS), "12345678000195"
        )

    def test_issqn_deduction_of_the_line(self):
        self.line.issqn_deduction_amount = 4.0
        self.assertEqual(
            self._vajustebc().findtext("nfse:vAjusteBCISSQN", namespaces=NS), "4.00"
        )
        self._adjustment()
        with self.assertRaisesRegex(UserError, "E0462"):
            self.nfse._serialize([])

    def test_adjustment_rules(self):
        with self.assertRaisesRegex(ValidationError, "E0465"):
            self._adjustment(adjustment_type="99")
        with self.assertRaisesRegex(ValidationError, "E0460"):
            self._adjustment(dfe_key="123")
