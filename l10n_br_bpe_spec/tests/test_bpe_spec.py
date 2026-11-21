# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import dataclasses
import re
import sys
import typing

from nfelib.bpe.bindings.v1_0 import bpe_tipos_basico_v1_00 as bindings

from odoo.tests import TransactionCase

# ICMS groups left out of the generation (XSDATA_SKIP, filled by the
# l10n_br_bpe export) and the xmldsig signature
SKIPPED_TYPES = re.compile(r"^(Icms\d+|Icmssn|Signature)$")


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


class TestBpeSpec(TransactionCase):
    def _spec_models(self):
        return {
            self.env[name]._binding_type: self.env[name]
            for name in self.env.registry
            if name.startswith("bpe.10.") and hasattr(self.env[name], "_binding_type")
        }

    def _check_binding(self, binding, spec_models, seen):
        if binding in seen or SKIPPED_TYPES.match(binding.__name__):
            return
        seen.add(binding)
        model = spec_models.get(binding.__qualname__)
        self.assertIsNotNone(model, f"No spec model for {binding.__qualname__}")
        hints = typing.get_type_hints(binding, vars(sys.modules[binding.__module__]))
        for field in dataclasses.fields(binding):
            sub_bindings = _binding_types(hints[field.name])
            if any(SKIPPED_TYPES.match(b.__name__) for b in sub_bindings):
                continue
            tag = field.metadata.get("name", field.name)
            self.assertIn(
                f"bpe10_{tag}",
                model._fields,
                f"{model._name} has no field for {binding.__qualname__}.{tag}",
            )
            for sub_binding in sub_bindings:
                self._check_binding(sub_binding, spec_models, seen)

    def test_every_binding_group_has_a_model(self):
        """Every group of the BP-e, BP-e TM and BP-e TA bindings is mapped."""
        spec_models = self._spec_models()
        seen = set()
        for root in (bindings.Tbpe, bindings.TbpeTm, bindings.TbpeTa):
            self._check_binding(root, spec_models, seen)
        self.assertIn(bindings.Tbpe.InfBpe.InfValorBpe.Comp, seen)

    def test_buyer_and_value_component_are_distinct_models(self):
        """infBPe/comp (buyer) and infValorBPe/Comp (component) do not clash."""
        infbpe = self.env["bpe.10.tbpe_infbpe"]
        infvalor = self.env["bpe.10.tbpe_infvalorbpe"]
        self.assertEqual(infbpe._fields["bpe10_comp"].comodel_name, "bpe.10.tbpe_comp")
        self.assertEqual(
            infvalor._fields["bpe10_Comp"].comodel_name,
            "bpe.10.tbpe_infvalorbpe_comp",
        )
        self.assertIn("bpe10_xNome", self.env["bpe.10.tbpe_comp"]._fields)
        self.assertIn("bpe10_vComp", self.env["bpe.10.tbpe_infvalorbpe_comp"]._fields)

    def test_ibscbs_group(self):
        """The IBS/CBS group of the reform (NT 2025.001) is mapped."""
        imp = self.env["bpe.10.tbpe_imp"]
        self.assertEqual(imp._fields["bpe10_IBSCBS"].comodel_name, "bpe.10.ttribbpe")
        self.assertIn("bpe10_vTotDFe", imp._fields)
        gibscbs = self.env["bpe.10.tcibs"]
        for tag in ("vBC", "gIBSUF", "gIBSMun", "vIBS", "gCBS"):
            self.assertIn(f"bpe10_{tag}", gibscbs._fields)
