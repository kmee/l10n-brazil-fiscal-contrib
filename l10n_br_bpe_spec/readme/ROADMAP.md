- Propose to xsdata-odoo that class names be compared after normalization, so
  that the BP-e generation comes out correct without a local patch
  (`infBPe/comp` and `infValorBPe/Comp`).
- Generate the BP-e event models (`eventoBPeTiposBasico_v1.00.xsd`) if any
  module needs them; today the events are built directly with the `nfelib`
  bindings.
