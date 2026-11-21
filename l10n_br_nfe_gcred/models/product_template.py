# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# leiauteNFe_v4.00.xsd, gCred/cCredPresumido
CRED_PRESUMIDO_CODE_PATTERN = re.compile(r"[!-\xff]{8}|[!-\xff]{10}")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    nfe_cred_presumido_code = fields.Char(
        string="Presumed Credit Code",
        size=10,
        company_dependent=True,
        help="Code of the ICMS presumed credit benefit granted by the state of "
        "the company, the same code used in the EFD (8 or 10 characters). "
        "It is reported in the gCred group of the NF-e items of this product.",
    )

    nfe_cred_presumido_percent = fields.Float(
        string="Presumed Credit (%)",
        digits=(7, 4),
        company_dependent=True,
        help="Percentage of the ICMS presumed credit, applied to the ICMS base "
        "of the NF-e item.",
    )

    @api.constrains("nfe_cred_presumido_code", "nfe_cred_presumido_percent")
    def _check_nfe_cred_presumido(self):
        for record in self:
            code = record.nfe_cred_presumido_code
            if code and not CRED_PRESUMIDO_CODE_PATTERN.fullmatch(code):
                raise ValidationError(
                    _(
                        "The presumed credit code must have 8 or 10 characters, "
                        "without spaces."
                    )
                )
            if not 0 <= record.nfe_cred_presumido_percent < 1000:
                raise ValidationError(
                    _("The presumed credit percentage must be between 0 and 999.")
                )
