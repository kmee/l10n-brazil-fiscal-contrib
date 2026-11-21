# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    MODELO_FISCAL_NFE,
)
from odoo.addons.l10n_br_nfe.models.document import filter_processador_edoc_nfe

# leiauteNFe_v4.00.xsd: <defensivo maxOccurs="20">
DEFENSIVO_MAX_OCCURS = 20

# NT 2024.003 v1.10, rules ZF02-10 and ZF02-20: pesticide NCM
PESTICIDE_NCM_PREFIXES = (
    "38085200",
    "3808592",
    "38086",
    "3808919",
    "38089220",
    "3808929",
    "3808932",
    "3808933",
    "3808935",
    "38089920",
    "3808999",
)
# rule ZF02-10, exception 4: biological and sanitizing products
PESTICIDE_PRESCRIPTION_EXEMPT_NCM = {
    "38085929",
    "38086100",
    "38086210",
    "38086290",
    "38086990",
    "38089191",
    "38089192",
    "38089193",
    "38089194",
    "38089196",
    "38089197",
    "38089199",
    "38089294",
    "38089299",
    "38089329",
    "38089333",
    "38089359",
    "38089991",
    "38089993",
    "38089995",
    "38089996",
    "38089999",
}
# rule ZF02-10, exceptions 2 and 3: transfers and future delivery
PESTICIDE_PRESCRIPTION_EXEMPT_CFOP_SUFFIXES = ("151", "152", "155", "156")
PESTICIDE_PRESCRIPTION_EXEMPT_CFOP = ("5922", "6922")

ANIMAL_GUIDES = ("1", "2", "3")
VEGETABLE_GUIDES = ("4", "5", "6")
# rules ZF05-14 and ZF05-24
LIVE_ANIMAL_NCM_PREFIXES = ("01", "0301")
VEGETABLE_NCM_PREFIXES = ("06", "07", "08", "12")
# rule ZF05-10, table 4.1 of NT 2024.003 v1.10 (cattle, since 2025-10-01)
ANIMAL_GUIDE_STATES = ("BA", "GO", "MA", "MT")
ANIMAL_GUIDE_NCM_PREFIXES = ("0102",)
ANIMAL_GUIDE_EXEMPT_CFOP_SUFFIXES = (
    "105",
    "106",
    "111",
    "112",
    "113",
    "114",
    "115",
    "155",
    "156",
    "454",
    "907",
    "922",
    "949",
)


def _is_pesticide(ncm):
    return ncm.startswith(PESTICIDE_NCM_PREFIXES)


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _document_check(self):
        result = super()._document_check()
        for record in self.filtered(filter_processador_edoc_nfe):
            if record.issuer == DOCUMENT_ISSUER_COMPANY:
                record._check_nfe40_agropecuario()
        return result

    def _nfe40_agropecuario_errors(self):
        """Errors of the agropecuario group that the SEFAZ rejects, by the
        layout and by the validation rules of NT 2024.003 v1.10."""
        self.ensure_one()
        agro = self.nfe40_agropecuario
        defensivo = agro.nfe40_defensivo
        guia = agro.nfe40_guiaTransito
        errors = []
        if agro and bool(defensivo) == bool(guia):
            errors.append(
                _(
                    "The agricultural group must have either pesticide "
                    "prescriptions or a transit permit, not both."
                )
            )
        if len(defensivo) > DEFENSIVO_MAX_OCCURS:
            errors.append(
                _(
                    "The NF-e accepts at most %(max)s pesticide prescriptions.",
                    max=DEFENSIVO_MAX_OCCURS,
                )
            )
        if self.document_type != MODELO_FISCAL_NFE:
            return errors

        lines = [
            (line, line.ncm_id.code_unmasked or "", line.cfop_id.code or "")
            for line in self.fiscal_line_ids
        ]
        if defensivo and not any(_is_pesticide(ncm) for __, ncm, __ in lines):
            errors.append(
                _(
                    "Rule ZF02-20 (rejection 309): no item is a pesticide, "
                    "remove the pesticide prescription."
                )
            )
        if guia.nfe40_tpGuia in ANIMAL_GUIDES and not any(
            ncm.startswith(LIVE_ANIMAL_NCM_PREFIXES) for __, ncm, __ in lines
        ):
            errors.append(
                _(
                    "Rule ZF05-14 (rejection 310): no item is a live animal, "
                    "remove the animal transit permit."
                )
            )
        if guia.nfe40_tpGuia in VEGETABLE_GUIDES and not any(
            ncm.startswith(VEGETABLE_NCM_PREFIXES) for __, ncm, __ in lines
        ):
            errors.append(
                _(
                    "Rule ZF05-24 (rejection 312): no item is a vegetable "
                    "product, remove the vegetable transit permit."
                )
            )
        if self.edoc_purpose != "1":
            return errors
        for line, ncm, cfop in lines:
            item = line.product_id.display_name or line.name
            if (
                not defensivo
                and self.ind_final == "1"
                and _is_pesticide(ncm)
                and ncm not in PESTICIDE_PRESCRIPTION_EXEMPT_NCM
                and line.cfop_id.ind_retor != "1"
                and cfop[1:] not in PESTICIDE_PRESCRIPTION_EXEMPT_CFOP_SUFFIXES
                and cfop not in PESTICIDE_PRESCRIPTION_EXEMPT_CFOP
            ):
                errors.append(
                    _(
                        "%(item)s: rule ZF02-10 (rejection 835) requires the "
                        "pesticide prescription on a sale to the final consumer.",
                        item=item,
                    )
                )
            if (
                guia.nfe40_tpGuia not in ANIMAL_GUIDES
                and self.company_id.state_id.code in ANIMAL_GUIDE_STATES
                and ncm.startswith(ANIMAL_GUIDE_NCM_PREFIXES)
                and cfop[1:] not in ANIMAL_GUIDE_EXEMPT_CFOP_SUFFIXES
            ):
                errors.append(
                    _(
                        "%(item)s: rule ZF05-10 (rejection 836) requires the "
                        "animal transit permit (GTA, TTA or DTA).",
                        item=item,
                    )
                )
        return errors

    def _check_nfe40_agropecuario(self):
        errors = self._nfe40_agropecuario_errors()
        if errors:
            raise UserError(
                _(
                    "The NF-e agricultural data (agropecuario) is invalid:\n"
                    "%(errors)s",
                    errors="\n".join(errors),
                )
            )
