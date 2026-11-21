# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BpeTmComponent(models.Model):
    """Component of a BP-e TM trip (detBPeTM/det/Comp): how many passengers
    of the trip paid with each kind of ticket (cash, transport voucher,
    exempt...)."""

    _name = "l10n_br_bpe_tm.component"
    _description = "BP-e TM Trip Component"
    _order = "line_id, id"

    line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.line",
        string="Trip",
        required=True,
        ondelete="cascade",
        index=True,
    )

    name = fields.Char(
        required=True,
        size=15,
        help="Comp/xNome, e.g. ISENTOS, VT, CARTAO PRE-PAGO, IDOSOS.",
    )

    quantity = fields.Integer(required=True, help="Comp/qComp (up to 99999).")
