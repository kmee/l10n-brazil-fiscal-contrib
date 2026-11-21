# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import _, api, models
from odoo.exceptions import ValidationError

# leiauteNFe_v4.00.xsd, comb/cProdANP
ANP_CODE_PATTERN = re.compile(r"[0-9]{9}")
GLP_ANP_CODE = "210203001"
GLP_PERCENT_FIELDS = ("nfe40_pGLP", "nfe40_pGNn", "nfe40_pGNi")


class NFeComb(models.AbstractModel):
    _inherit = "nfe.40.comb"

    def name_get(self):
        return [
            (
                record.id,
                " - ".join(filter(None, (record.nfe40_cProdANP, record.nfe40_descANP))),
            )
            for record in self
        ]

    @api.constrains("nfe40_cProdANP")
    def _check_nfe40_cProdANP(self):
        for record in self:
            if not ANP_CODE_PATTERN.fullmatch(record.nfe40_cProdANP or ""):
                raise ValidationError(_("The ANP product code must have 9 digits."))

    def _export_field(self, xsd_field, class_obj, member_spec, export_value=None):
        # the generic format of these percentages has no decimals, and the
        # SEFAZ checks that their sum is 100
        if xsd_field in GLP_PERCENT_FIELDS and self[xsd_field]:
            return f"{self[xsd_field]:.2f}"
        if xsd_field == "nfe40_UFCons" and not self.nfe40_UFCons:
            # set by the document line from the delivery address
            return self.env.context.get("nfe40_comb_uf_cons")
        return super()._export_field(xsd_field, class_obj, member_spec, export_value)


class NFeOrigComb(models.AbstractModel):
    _inherit = "nfe.40.origcomb"

    @api.constrains("nfe40_pOrig")
    def _check_nfe40_pOrig(self):
        for record in self:
            if not 0 < record.nfe40_pOrig <= 100:
                raise ValidationError(
                    _("The origin percentage must be greater than 0 and up to 100.")
                )
