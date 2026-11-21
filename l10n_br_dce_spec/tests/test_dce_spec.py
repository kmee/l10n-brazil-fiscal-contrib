# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import dataclasses
import sys
import typing

from odoo.tests import TransactionCase

from ..bindings.v1_0 import dce_tipos_basico_v1_00 as bindings

# xmldsig signature, and the xCampo attribute of the obs* groups, which has no
# type in the xsd (anySimpleType) and is not mapped by xsdata-odoo
SKIPPED_TYPES = ("Signature",)
SKIPPED_TAGS = ("xCampo",)


def _binding_types(annotation):
    """Dataclass types behind a field annotation (Optional, list, union)."""
    if dataclasses.is_dataclass(annotation):
        return [annotation]
    return [
        arg
        for sub in typing.get_args(annotation)
        for arg in _binding_types(sub)
        if arg is not type(None)
    ]


class TestDceSpec(TransactionCase):
    def _spec_models(self):
        return {
            self.env[name]._binding_type: self.env[name]
            for name in self.env.registry
            if name.startswith("dce.10.") and hasattr(self.env[name], "_binding_type")
        }

    def _check_binding(self, binding, spec_models, seen):
        if binding in seen or binding.__name__ in SKIPPED_TYPES:
            return
        seen.add(binding)
        model = spec_models.get(binding.__qualname__)
        self.assertIsNotNone(model, f"No spec model for {binding.__qualname__}")
        hints = typing.get_type_hints(binding, vars(sys.modules[binding.__module__]))
        for field in dataclasses.fields(binding):
            tag = field.metadata.get("name", field.name)
            sub_bindings = _binding_types(hints[field.name])
            if tag in SKIPPED_TAGS or any(
                b.__name__ in SKIPPED_TYPES for b in sub_bindings
            ):
                continue
            self.assertIn(
                f"dce10_{tag}",
                model._fields,
                f"{model._name} has no field for {binding.__qualname__}.{tag}",
            )
            for sub_binding in sub_bindings:
                self._check_binding(sub_binding, spec_models, seen)

    def test_every_binding_group_has_a_model(self):
        """Every group of the DC-e bindings is mapped to a spec model."""
        seen = set()
        self._check_binding(bindings.Tdce, self._spec_models(), seen)
        self.assertIn(bindings.Tdce.InfDce.Det.Prod, seen)
        self.assertIn(bindings.Tdce.InfDce.InfDec, seen)

    def test_issuer_groups(self):
        """The Fisco, Marketplace, Transportadora and ECT groups are a choice."""
        infdce = self.env["dce.10.infdce"]
        for tag in ("Fisco", "Marketplace", "Transportadora", "ECT"):
            self.assertEqual(infdce._fields[f"dce10_{tag}"].choice, "infdce")
        self.assertIn("dce10_Site", self.env["dce.10.marketplace"]._fields)
        self.assertIn("dce10_tpEmit", self.env["dce.10.ide"]._fields)
        self.assertIn("dce10_nSiteAutoriz", self.env["dce.10.ide"]._fields)
