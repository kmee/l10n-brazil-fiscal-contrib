# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import _, api, models
from odoo.exceptions import ValidationError

# leiauteNFe_v4.00.xsd, veicProd/chassi
CHASSIS_PATTERN = re.compile(r"[A-Z0-9]{17}")


class NFeVeicProd(models.AbstractModel):
    _inherit = "nfe.40.veicprod"

    def name_get(self):
        return [
            (record.id, record.nfe40_chassi or record.nfe40_cMod or "")
            for record in self
        ]

    @api.constrains("nfe40_chassi")
    def _check_nfe40_chassi(self):
        for record in self.filtered("nfe40_chassi"):
            if not CHASSIS_PATTERN.fullmatch(record.nfe40_chassi):
                raise ValidationError(
                    _("The chassis (VIN) must have 17 capital letters or digits.")
                )

    def _nfe40_missing_fields(self):
        """Labels of the fields the layout requires and are empty."""
        self.ensure_one()
        return [
            field.string
            for name, field in self._fields.items()
            if getattr(field, "xsd_required", False) and not self[name]
        ]
