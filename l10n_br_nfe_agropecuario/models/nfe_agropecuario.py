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

    def name_get(self):
        return [
            (
                record.id,
                record.nfe40_guiaTransito.display_name
                or ", ".join(record.nfe40_defensivo.mapped("display_name")),
            )
            for record in self
        ]


class NFeDefensivo(models.AbstractModel):
    _inherit = "nfe.40.defensivo"

    def name_get(self):
        return [(record.id, record.nfe40_nReceituario or "") for record in self]

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

    def name_get(self):
        kinds = dict(self._fields["nfe40_tpGuia"].selection)
        return [
            (
                record.id,
                " ".join(
                    part
                    for part in (
                        kinds.get(record.nfe40_tpGuia, ""),
                        record.nfe40_UFGuia,
                        record.nfe40_serieGuia,
                        record.nfe40_nGuia,
                    )
                    if part
                ),
            )
            for record in self
        ]

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
