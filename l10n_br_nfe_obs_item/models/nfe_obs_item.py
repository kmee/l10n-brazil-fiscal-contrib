# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.exceptions import ValidationError

# leiauteNFe_v4.00.xsd, obsItem/obsCont and obsItem/obsFisco
XCAMPO_MAX_LENGTH = 20
XTEXTO_MAX_LENGTH = 60


class NFeObsItem(models.AbstractModel):
    _inherit = "nfe.40.obsitem"

    @api.depends("nfe40_obsCont", "nfe40_obsFisco")
    def _compute_display_name(self):
        for record in self:
            record.display_name = " / ".join(
                obs.display_name
                for obs in (record.nfe40_obsCont, record.nfe40_obsFisco)
                if obs
            )


def _check_obs(records):
    for record in records:
        field_name = (record.nfe40_xCampo or "").strip()
        text = (record.nfe40_xTexto or "").strip()
        if not 1 <= len(field_name) <= XCAMPO_MAX_LENGTH:
            raise ValidationError(
                records.env._(
                    "The field name of an NF-e item observation must have "
                    "1 to %(max)s characters.",
                    max=XCAMPO_MAX_LENGTH,
                )
            )
        if not 1 <= len(text) <= XTEXTO_MAX_LENGTH:
            raise ValidationError(
                records.env._(
                    "The text of an NF-e item observation must have 1 to "
                    "%(max)s characters.",
                    max=XTEXTO_MAX_LENGTH,
                )
            )


def _obs_display_name(records):
    for record in records:
        record.display_name = f"{record.nfe40_xCampo}: {record.nfe40_xTexto}"


class NFeDetObsCont(models.AbstractModel):
    _inherit = "nfe.40.det_obscont"

    @api.depends("nfe40_xCampo", "nfe40_xTexto")
    def _compute_display_name(self):
        _obs_display_name(self)

    @api.constrains("nfe40_xCampo", "nfe40_xTexto")
    def _check_nfe40_xCampo_xTexto(self):
        _check_obs(self)


class NFeDetObsFisco(models.AbstractModel):
    _inherit = "nfe.40.det_obsfisco"

    @api.depends("nfe40_xCampo", "nfe40_xTexto")
    def _compute_display_name(self):
        _obs_display_name(self)

    @api.constrains("nfe40_xCampo", "nfe40_xTexto")
    def _check_nfe40_xCampo_xTexto(self):
        _check_obs(self)
