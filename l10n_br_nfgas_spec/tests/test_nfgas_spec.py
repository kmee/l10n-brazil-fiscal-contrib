# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from importlib import import_module

from odoo import fields
from odoo.tests import TransactionCase, tagged

from ..bindings.v1_0.ev_canc_nfgas_v1_00 import EvCancNfgas, EvCancNfgasDescEvento
from ..models.v1_0 import dfe_tipos_basicos_v1_00, nfgas_tipos_basico_v1_00
from ..tools import schema_path

# xs:gYearMonth has no Odoo field type (xsdata-odoo skips it)
SKIPPED_TAGS = {
    ("nfgas.10.tajustecompet", "competApur"),
    ("nfgas.10.tcredpresibszfm", "competApur"),
}


@tagged("post_install", "-at_install")
class TestNfgasSpec(TransactionCase):
    def test_spec_models_cover_bindings(self):
        """Every tag of the bindings has its nfgas10_ field."""
        checked = 0
        for spec_module in (nfgas_tipos_basico_v1_00, dfe_tipos_basicos_v1_00):
            binding_module = import_module(
                spec_module.__name__.replace(".models.", ".bindings.")
            )
            for spec_class in vars(spec_module).values():
                binding_type = getattr(spec_class, "_binding_type", None)
                if not isinstance(spec_class, type) or not binding_type:
                    continue
                binding_class = binding_module
                for attr in binding_type.split("."):
                    binding_class = getattr(binding_class, attr)
                odoo_fields = {
                    name
                    for name, value in vars(spec_class).items()
                    if isinstance(value, fields.Field)
                }
                for fname, fspec in binding_class.__dataclass_fields__.items():
                    tag = fspec.metadata.get("name", fname)
                    if fname == "signature" or (spec_class._name, tag) in SKIPPED_TAGS:
                        continue
                    self.assertIn(
                        f"nfgas10_{tag}",
                        odoo_fields,
                        f"{spec_class._name} misses the {tag} tag",
                    )
                self.assertIn(spec_class._name, self.env)
                checked += 1
        self.assertGreater(checked, 100)

    def test_ibscbs_groups(self):
        """IBSCBS is mandatory in the NFGas item (MOC NFGas 1.00g, Anexo I)."""
        ibscbs = self.env["nfgas.10.timp"]._fields["nfgas10_IBSCBS"]
        self.assertEqual(ibscbs.comodel_name, "nfgas.10.ttribnfgas")
        self.assertTrue(ibscbs.xsd_required)
        self.assertEqual(
            self.env["nfgas.10.total"]._fields["nfgas10_IBSCBSTot"].comodel_name,
            "nfgas.10.tibscbstot",
        )
        # NT 2026.004 v1.01: net values of the item
        self.assertIn("nfgas10_vProdLiq", self.env["nfgas.10.prod"]._fields)

    def test_bindings_against_schema(self):
        event = EvCancNfgas(
            descEvento=EvCancNfgasDescEvento.CANCELAMENTO,
            nProt="3352600000000001",
            xJust="Fatura emitida em duplicidade",
        )
        xml = event.to_xml()
        self.assertFalse(
            EvCancNfgas.schema_validation(xml, schema_path("evCancNFGas_v1.00.xsd"))
        )
        event.xJust = "curta"
        self.assertTrue(
            EvCancNfgas.schema_validation(
                event.to_xml(), schema_path("evCancNFGas_v1.00.xsd")
            )
        )
