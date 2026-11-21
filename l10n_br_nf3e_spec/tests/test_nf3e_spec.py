# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from importlib import import_module

from odoo import fields
from odoo.tests import TransactionCase, tagged

from ..models.v1_0 import dfe_tipos_basicos_v1_00, nf3e_tipos_basico_v1_00

# xs:gYearMonth has no Odoo field type (xsdata-odoo skips it) and the lists of
# simple values of gConsumidor are skipped at generation (XSDATA_SKIP)
SKIPPED_TAGS = {
    ("nf3e.10.tajustecompet", "competApur"),
    ("nf3e.10.tcredpresibszfm", "competApur"),
    ("nf3e.10.gconsumidor", "tpPosTar"),
    ("nf3e.10.gconsumidor", "tpPosTarInjet"),
}


@tagged("post_install", "-at_install")
class TestNf3eSpec(TransactionCase):
    def test_spec_models_cover_bindings(self):
        """Every tag of the nfelib bindings has its nf3e10_ field."""
        checked = 0
        for spec_module in (nf3e_tipos_basico_v1_00, dfe_tipos_basicos_v1_00):
            binding_module = import_module(
                spec_module.__name__.replace(
                    "odoo.addons.l10n_br_nf3e_spec.models", "nfelib.nf3e.bindings"
                )
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
                        f"nf3e10_{tag}",
                        odoo_fields,
                        f"{spec_class._name} misses the {tag} tag",
                    )
                self.assertIn(spec_class._name, self.env)
                checked += 1
        self.assertGreater(checked, 100)

    def test_ibscbs_groups(self):
        self.assertEqual(
            self.env["nf3e.10.imposto"]._fields["nf3e10_IBSCBS"].comodel_name,
            "nf3e.10.ttribnf3e",
        )
        self.assertEqual(
            self.env["nf3e.10.total"]._fields["nf3e10_IBSCBSTot"].comodel_name,
            "nf3e.10.tibscbstot",
        )
