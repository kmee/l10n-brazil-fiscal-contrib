# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from importlib import import_module

from odoo.tests import TransactionCase, tagged

BINDING_MODULES = (
    "nfelib.nfcom.bindings.v1_0.nfcom_tipos_basico_v1_00",
    "nfelib.nfcom.bindings.v1_0.dfe_tipos_basicos_v1_00",
)


@tagged("post_install", "-at_install")
class TestNfcomSpec(TransactionCase):
    def _binding_class(self, binding_type):
        for module_name in BINDING_MODULES:
            binding = import_module(module_name)
            try:
                for attr in binding_type.split("."):
                    binding = getattr(binding, attr)
            except AttributeError:
                continue
            return binding
        return None

    def test_spec_fields_match_nfelib_bindings(self):
        models = [name for name in self.env if name.startswith("nfcom.10.")]
        self.assertGreater(len(models), 100)
        for model_name in models:
            model = self.env[model_name]
            binding_class = self._binding_class(model._binding_type)
            self.assertTrue(binding_class, model_name)
            tags = set()
            for name, spec in binding_class.__dataclass_fields__.items():
                tags |= {name, spec.metadata.get("name", name)}
            for field_name in model._fields:
                if not field_name.startswith("nfcom10_") or field_name.endswith("_id"):
                    continue
                if field_name.startswith("nfcom10_choice"):
                    continue
                self.assertIn(field_name[len("nfcom10_") :], tags, field_name)
