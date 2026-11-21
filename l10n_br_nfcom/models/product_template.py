# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.l10n_br_nfcom_spec.models.v1_0.nfcom_tipos_basico_v1_00 import (
    TUMEDITEM,
)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    nfcom_cclass = fields.Char(
        string="NFCom Item Classification",
        size=7,
        help="Code of the item classification table of the NFCom (cClass).",
    )

    nfcom_umed = fields.Selection(
        selection=TUMEDITEM,
        string="NFCom Unit of Measure",
        default="4",
        help="1 - Minute, 2 - MB, 3 - GB, 4 - Unit (uMed).",
    )
