# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # When l10n_br_cte makes the GTV-e spec mixins concrete before this module
    # is installed, their address tags point to res.partner, which carries
    # several CT-e address types.
    _cte40_binding_type_enderEmit = "TendeEmi"
    _cte40_binding_type_enderReme = "Tendereco"
    _cte40_binding_type_enderDest = "Tendereco"
    _cte40_binding_type_enderToma = "Tendereco"
