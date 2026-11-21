# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from importlib import import_module

from odoo import fields
from odoo.tests import TransactionCase, tagged
from odoo.tools.misc import file_path

from ..bindings.v1_0.nfag_v1_00 import Nfag
from ..models.v1_0 import dfe_tipos_basicos_v1_00, nfag_tipos_basico_v1_00

# xs:gYearMonth has no Odoo field type (xsdata-odoo skips it)
SKIPPED_TAGS = {
    ("nfag.10.tajustecompet", "competApur"),
    ("nfag.10.tcredpresibszfm", "competApur"),
}


@tagged("post_install", "-at_install")
class TestNfagSpec(TransactionCase):
    def test_spec_models_cover_bindings(self):
        """Every tag of the bindings has its nfag10_ field."""
        checked = 0
        for spec_module in (nfag_tipos_basico_v1_00, dfe_tipos_basicos_v1_00):
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
                        f"nfag10_{tag}",
                        odoo_fields,
                        f"{spec_class._name} misses the {tag} tag",
                    )
                self.assertIn(spec_class._name, self.env)
                checked += 1
        self.assertGreater(checked, 90)

    def test_ibscbs_groups(self):
        """The IBSCBS group of the item is required (MOC NFAg 1.00l)."""
        ibscbs = self.env["nfag.10.imposto"]._fields["nfag10_IBSCBS"]
        self.assertEqual(ibscbs.comodel_name, "nfag.10.ttribnfag")
        self.assertTrue(ibscbs.xsd_required)
        self.assertEqual(
            self.env["nfag.10.total"]._fields["nfag10_IBSCBSTot"].comodel_name,
            "nfag.10.tibscbstot",
        )

    def test_schema_validation(self):
        """The bundled schemas load and reject an empty NFAg."""
        schema = file_path("l10n_br_nfag_spec/schemas/v1_0/nfag_v1.00.xsd")
        errors = Nfag.schema_validation(
            '<NFAg xmlns="http://www.portalfiscal.inf.br/nfag"/>', schema
        )
        self.assertTrue(errors)
