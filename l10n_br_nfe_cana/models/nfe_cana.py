# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# leiauteNFe_v4.00.xsd, cana/ref and cana/forDia/@dia
REF_PATTERN = re.compile(r"(0[1-9]|1[0-2])/2[0-9]{3}")
DIA_PATTERN = re.compile(r"[1-9]|[1][0-9]|[2][0-9]|[3][0-1]")


class NFeCana(models.AbstractModel):
    _inherit = "nfe.40.cana"

    nfe40_qTotMes = fields.Float(
        compute="_compute_nfe40_qTotMes", store=True, readonly=False
    )
    nfe40_qTotGer = fields.Float(
        compute="_compute_nfe40_qTotGer", store=True, readonly=False
    )
    nfe40_vTotDed = fields.Monetary(
        compute="_compute_nfe40_vTotDed", store=True, readonly=False
    )
    nfe40_vLiqFor = fields.Monetary(
        compute="_compute_nfe40_vLiqFor", store=True, readonly=False
    )

    @api.depends("nfe40_forDia.nfe40_qtde")
    def _compute_nfe40_qTotMes(self):
        for record in self:
            record.nfe40_qTotMes = sum(record.nfe40_forDia.mapped("nfe40_qtde"))

    @api.depends("nfe40_qTotMes", "nfe40_qTotAnt")
    def _compute_nfe40_qTotGer(self):
        for record in self:
            record.nfe40_qTotGer = record.nfe40_qTotMes + record.nfe40_qTotAnt

    @api.depends("nfe40_deduc.nfe40_vDed")
    def _compute_nfe40_vTotDed(self):
        for record in self:
            record.nfe40_vTotDed = sum(record.nfe40_deduc.mapped("nfe40_vDed"))

    @api.depends("nfe40_vFor", "nfe40_vTotDed")
    def _compute_nfe40_vLiqFor(self):
        for record in self:
            record.nfe40_vLiqFor = record.nfe40_vFor - record.nfe40_vTotDed

    @api.depends("nfe40_safra", "nfe40_ref")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.nfe40_safra or ''} {record.nfe40_ref or ''}"

    @api.constrains("nfe40_safra", "nfe40_ref", "nfe40_forDia")
    def _check_nfe40_cana(self):
        for record in self:
            if not 4 <= len((record.nfe40_safra or "").strip()) <= 9:
                raise ValidationError(
                    _(
                        "The harvest (safra) must have 4 to 9 characters, "
                        "e.g. 2025/2026."
                    )
                )
            if not REF_PATTERN.fullmatch(record.nfe40_ref or ""):
                raise ValidationError(
                    _("The reference month must be in the MM/YYYY format.")
                )
            days = record.nfe40_forDia.mapped("nfe40_dia")
            if len(days) != len(set(days)):
                raise ValidationError(
                    _("Each day of the month can have a single daily supply.")
                )


class NFeForDia(models.AbstractModel):
    _inherit = "nfe.40.fordia"

    @api.constrains("nfe40_dia")
    def _check_nfe40_dia(self):
        for record in self:
            if not DIA_PATTERN.fullmatch(record.nfe40_dia or ""):
                raise ValidationError(_("The day must be a number from 1 to 31."))
