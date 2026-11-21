# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

# TBPeTA/infBPe/infValorBPe/Comp/tpComp (bpeTiposBasico_v1.00.xsd): the codes
# differ from the ones of the BP-e (06 is the baggage here)
BPE_TA_COMPONENT_TYPES = [
    ("01", "Fare"),
    ("03", "Boarding Fee"),
    ("06", "Baggage"),
    ("07", "Seat Reservation"),
    ("08", "Animal Transport"),
    ("99", "Other"),
]


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    bpe_ta_component_type = fields.Selection(
        selection=BPE_TA_COMPONENT_TYPES,
        string="BP-e TA Component Type",
        default="01",
        help="Type of the value component (Comp/tpComp) of the BP-e TA.",
    )
