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


# the export builds the remaining spec models, which an at_install
# transaction would roll back
@tagged("post_install", "-at_install")
class TestNfseImovel(TransactionCase):
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
        cls.line.write(
            {
                "national_taxation_code_id": cls.env[
                    "l10n_br_fiscal.national.taxation.code"
                ]
                .create({"name": "Real estate lease", "code": "99.03.01"})
                .id,
                "tax_classification_id": cls.env.ref(
                    "l10n_br_fiscal.tax_classification_000001"
                ).id,
                "ibs_cst_id": cls.env.ref("l10n_br_fiscal.cst_ibs_000").id,
                "operation_indicator_id": cls.env.ref(
                    "l10n_br_fiscal.operation_indicator_020101"
                ).id,
            }
        )

    def _add_unit(self, **values):
        return self.env["l10n_br_nfse_nacional.real.estate.unit"].create(
            dict({"document_id": self.nfse.id, "cib": "1234567X"}, **values)
        )

    def _imovel(self):
        xml = self.nfse._serialize([])[0].to_xml()
        self.assertEqual(Dps.schema_validation(xml), [])
        root = etree.fromstring(xml.encode())
        return root.find("./nfse:infDPS/nfse:IBSCBS/nfse:imovel", NS)

    def test_lease_of_real_estate(self):
        self._add_unit(
            insc_imob_fisc="IPTU-55",
            adjustment_ids=[(0, 0, {"adjustment_type": "03", "amount": 2.0})],
        )
        imovel = self._imovel()
        self.assertEqual(imovel.findtext("nfse:cMun", namespaces=NS), "4202404")
        self.assertEqual(
            imovel.findtext("nfse:gLocacao/nfse:pCopropriedade", namespaces=NS),
            "100.00",
        )
        self.assertEqual(
            imovel.findtext("nfse:gLocacao/nfse:vTotOper", namespaces=NS), "20.00"
        )
        unit = imovel.find("nfse:gUnidImob", NS)
        self.assertEqual(unit.findtext("nfse:cCIB", namespaces=NS), "1234567X")
        self.assertEqual(
            unit.findtext(
                "nfse:gAjusteBCLocImoveis/nfse:tpAjusteBCLocImoveis", namespaces=NS
            ),
            "03",
        )

    def test_units_required_for_the_indicator(self):
        """Rule E0938."""
        with self.assertRaisesRegex(UserError, "E0938"):
            self.nfse._serialize([])

    def test_group_only_for_real_estate_indicators(self):
        """Rule E0928."""
        self.line.operation_indicator_id = self.env.ref(
            "l10n_br_fiscal.operation_indicator_030101"
        )
        self.assertIsNone(self._imovel())
        self._add_unit()
        with self.assertRaisesRegex(UserError, "E0928"):
            self.nfse._serialize([])

    def test_adjustment_description_rule(self):
        """Rule E0949."""
        with self.assertRaisesRegex(ValidationError, "E0949"):
            self._add_unit(
                adjustment_ids=[(0, 0, {"adjustment_type": "99", "amount": 1.0})]
            )
