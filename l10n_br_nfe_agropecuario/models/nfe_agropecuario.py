# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from erpbrasil.base.fiscal import cnpj_cpf

from odoo import _, api, models
from odoo.exceptions import ValidationError

# leiauteNFe_v4.00.xsd, agropecuario/guiaTransito/nGuia
GUIA_NUMBER_PATTERN = re.compile(r"[0-9]{1,9}")


class NFeAgropecuario(models.AbstractModel):
    _inherit = "nfe.40.agropecuario"

    @api.depends("nfe40_defensivo", "nfe40_guiaTransito")
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.nfe40_guiaTransito.display_name or ", ".join(
                record.nfe40_defensivo.mapped("display_name")
            )


class NFeDefensivo(models.AbstractModel):
    _inherit = "nfe.40.defensivo"

    @api.depends("nfe40_nReceituario")
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.nfe40_nReceituario or ""

    @api.constrains("nfe40_nReceituario", "nfe40_CPFRespTec")
    def _check_nfe40_defensivo(self):
        for record in self:
            if not 1 <= len((record.nfe40_nReceituario or "").strip()) <= 30:
                raise ValidationError(
                    _("The prescription number must have 1 to 30 characters.")
                )
            cpf = record.nfe40_CPFRespTec or ""
            # rule ZF03a-10 (rejection 308), NT 2024.003
            if not (len(cpf) == 11 and cpf.isdigit() and cnpj_cpf.validar_cpf(cpf)):
                raise ValidationError(
                    _(
                        "The CPF of the technician responsible for the "
                        "prescription is invalid (11 digits, no punctuation)."
                    )
                )


class NFeGuiaTransito(models.AbstractModel):
    _inherit = "nfe.40.guiatransito"

    @api.depends("nfe40_tpGuia", "nfe40_UFGuia", "nfe40_serieGuia", "nfe40_nGuia")
    def _compute_display_name(self):
        for record in self:
            kind = dict(self._fields["nfe40_tpGuia"].selection).get(
                record.nfe40_tpGuia, ""
            )
            record.display_name = " ".join(
                part
                for part in (
                    kind,
                    record.nfe40_UFGuia,
                    record.nfe40_serieGuia,
                    record.nfe40_nGuia,
                )
                if part
            )

    @api.constrains("nfe40_nGuia", "nfe40_serieGuia")
    def _check_nfe40_guiaTransito(self):
        for record in self:
            if not GUIA_NUMBER_PATTERN.fullmatch(record.nfe40_nGuia or ""):
                raise ValidationError(
                    _("The transit permit number must have 1 to 9 digits.")
                )
            if len(record.nfe40_serieGuia or "") > 9:
                raise ValidationError(
                    _("The transit permit series must have at most 9 characters.")
                )
