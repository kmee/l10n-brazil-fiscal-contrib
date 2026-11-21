# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from erpbrasil.base.misc import punctuation_rm

from odoo import _, fields, models

# bpeTM_v1.00.xsd: idEqpCont and nViagem go from 1 to 990
MAX_TRIPS = 990


class FiscalDocumentLine(models.Model):
    """In a BP-e TM each fiscal line is a trip (detBPeTM/det): the quantity
    is the number of passengers (qPass) and the gross amount the sum of the
    tickets of the trip (vBP). The trips of the same counter equipment are
    grouped in one detBPeTM."""

    _inherit = "l10n_br_fiscal.document.line"

    bpe_tm_equipment = fields.Integer(
        string="Counter Equipment",
        help="detBPeTM/idEqpCont: identifier (1 to 990) of the turnstile or "
        "counter that registered the trip.",
    )

    bpe_tm_plate = fields.Char(
        string="Vehicle Plate",
        help="detBPeTM/placa, informed once per counter equipment.",
    )

    bpe_tm_line_prefix = fields.Char(
        string="Line Prefix",
        size=20,
        help="detBPeTM/prefixo, informed once per counter equipment.",
    )

    bpe_tm_trip = fields.Integer(
        string="Trip Number",
        help="det/nViagem (1 to 990). When empty, the trips of each counter "
        "equipment are numbered in order.",
    )

    bpe_tm_start_city_id = fields.Many2one(
        comodel_name="res.city",
        string="Trip Start City",
        domain=[("country_id.code", "=", "BR")],
    )

    bpe_tm_end_city_id = fields.Many2one(
        comodel_name="res.city",
        string="Trip End City",
        domain=[("country_id.code", "=", "BR")],
    )

    bpe_tm_counter_start = fields.Char(
        string="Counter at Start", size=20, help="det/nContInicio"
    )

    bpe_tm_counter_end = fields.Char(
        string="Counter at End", size=20, help="det/nContFim"
    )

    bpe_tm_component_ids = fields.One2many(
        comodel_name="l10n_br_bpe_tm.component",
        inverse_name="line_id",
        string="Trip Components",
        copy=True,
    )

    def _bpe_tm_check_trip(self):
        self.ensure_one()
        errors = []
        name = self.name or self.product_id.display_name
        if not self.bpe_tm_start_city_id:
            errors.append(_("Trip %s: fill in the trip start city.", name))
        if self.bpe_tm_trip and not 1 <= self.bpe_tm_trip <= MAX_TRIPS:
            errors.append(
                _(
                    "Trip %(trip)s: the trip number goes from 1 to %(max)s.",
                    trip=name,
                    max=MAX_TRIPS,
                )
            )
        if self.quantity < 1 or self.quantity != int(self.quantity):
            errors.append(
                _("Trip %s: the quantity is the whole number of passengers.", name)
            )
        start = punctuation_rm(self.bpe_tm_counter_start or "")
        end = punctuation_rm(self.bpe_tm_counter_end or "")
        if bool(start) != bool(end):
            errors.append(
                _("Trip %s: inform both counters (start and end) or none.", name)
            )
        # rule H16 (rejection 695)
        elif start.isdigit() and end.isdigit() and int(end) <= int(start):
            errors.append(
                _("Trip %s: the end counter must be greater than the start one.", name)
            )
        components = self.bpe_tm_component_ids
        if not components:
            errors.append(
                _("Trip %s: inform at least one trip component (det/Comp).", name)
            )
        # rule H31 (rejection 696), with the tolerance of 1 of the NT
        elif abs(sum(components.mapped("quantity")) - self.quantity) > 1:
            errors.append(
                _(
                    "Trip %s: the components quantities must add up to the "
                    "number of passengers.",
                    name,
                )
            )
        return errors
