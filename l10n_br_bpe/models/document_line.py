# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

# infValorBPe/Comp/tpComp of the BP-e (bpeTiposBasico_v1.00.xsd)
BPE_COMPONENT_TYPES = [
    ("01", "Fare"),
    ("02", "Toll"),
    ("03", "Boarding Fee"),
    ("04", "Insurance"),
    ("05", "Road Maintenance Fee (TMR)"),
    ("06", "Integrated Sale Service (SVI)"),
    ("99", "Other"),
]


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    bpe_component_type = fields.Selection(
        selection=BPE_COMPONENT_TYPES,
        string="BP-e Component Type",
        default="01",
        help="Type of the value component (Comp/tpComp) of the BP-e.",
    )

    bpe_layout = fields.Selection(related="document_id.bpe_layout")
