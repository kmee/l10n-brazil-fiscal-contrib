# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.tools import float_compare

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EDOC_PURPOSE_COMPLEMENTAR,
    EDOC_PURPOSE_DEVOLUCAO,
    MODELO_FISCAL_NFE,
)

from .nfe_comb import GLP_ANP_CODE, GLP_PERCENT_FIELDS

# rule LA11-20: sale of fuel to the final consumer
METER_CFOPS = ("5656", "5667")
# rule LA21-20: LPG codes whose origin adds up to 100 per national/imported
LPG_ANP_CODES = ("210203001", "210203003", "210203004", "210203005")
ORIGIN_TOLERANCE = 0.1


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    nfe40_comb = fields.Many2one(
        compute="_compute_nfe40_comb",
        store=True,
        readonly=False,
    )

    @api.depends("product_id")
    def _compute_nfe40_comb(self):
        for line in self:
            line.nfe40_comb = line.product_id.nfe40_comb

    def _nfe40_comb_consumption_state(self):
        """State where the fuel is consumed, used when the fuel group has
        none: the delivery address, or EX for a foreign customer."""
        self.ensure_one()
        if self.nfe40_comb.nfe40_UFCons:
            return self.nfe40_comb.nfe40_UFCons
        document = self.document_id
        partner = document.partner_shipping_id or document.partner_id
        if partner.country_id and partner.country_id.code != "BR":
            return "EX"
        return partner.state_id.code or False

    def _export_field(self, xsd_field, class_obj, member_spec, export_value=None):
        record = self
        if xsd_field == "nfe40_comb" and self.nfe40_comb:
            record = self.with_context(
                nfe40_comb_uf_cons=self._nfe40_comb_consumption_state()
            )
        return super(FiscalDocumentLine, record)._export_field(
            xsd_field, class_obj, member_spec, export_value
        )

    def _nfe40_comb_errors(self):
        """Errors of the fuel group the SEFAZ would reject."""
        self.ensure_one()
        comb = self.nfe40_comb
        document = self.document_id
        item = self.product_id.display_name or self.name
        errors = []
        if not comb.nfe40_descANP:
            errors.append(_("%(item)s: the ANP description is required.", item=item))
        if not self._nfe40_comb_consumption_state():
            errors.append(_("%(item)s: the consumption state is required.", item=item))
        # rules LA03c-10 and LA03c-20, NT 2016.002
        percentages = [comb[field] for field in GLP_PERCENT_FIELDS]
        if comb.nfe40_cProdANP == GLP_ANP_CODE:
            if float_compare(sum(percentages), 100, precision_digits=2):
                errors.append(
                    _(
                        "%(item)s: the LPG percentages (oil, national and "
                        "imported natural gas) must add up to 100 (rejection 855).",
                        item=item,
                    )
                )
        elif any(percentages):
            errors.append(
                _(
                    "%(item)s: the LPG percentages are only allowed for the ANP "
                    "code %(code)s (rejection 461).",
                    item=item,
                    code=GLP_ANP_CODE,
                )
            )
        # rules LA11-20 and LA16-10, NT 2015.002
        meter = comb.nfe40_encerrante
        if meter:
            if (
                document.document_type_id.code == MODELO_FISCAL_NFE
                and self.cfop_id.code not in METER_CFOPS
            ):
                errors.append(
                    _(
                        "%(item)s: the pump meter group is only allowed in the "
                        "NF-e with the CFOP 5656 or 5667 (rejection 379).",
                        item=item,
                    )
                )
            if meter.nfe40_vEncFin <= meter.nfe40_vEncIni:
                errors.append(
                    _(
                        "%(item)s: the pump meter at the end must be greater than "
                        "at the start (rejection 380).",
                        item=item,
                    )
                )
        # rules LA18-20, LA21-10 and LA21-20, NT 2023.001
        origins = comb.nfe40_origComb
        origin_exempt = (
            document.ind_final == "1"
            or document.edoc_purpose
            in (EDOC_PURPOSE_COMPLEMENTAR, EDOC_PURPOSE_DEVOLUCAO)
            or self.cfop_id.code in ("5922", "6922")
        )
        if (comb.nfe40_pGNn or comb.nfe40_pGNi) and not origins and not origin_exempt:
            errors.append(
                _(
                    "%(item)s: the fuel origin is required when the LPG has "
                    "natural gas (rejection 909).",
                    item=item,
                )
            )
        if comb.nfe40_cProdANP in LPG_ANP_CODES:
            groups = [
                origins.filtered(lambda o, i=ind: o.nfe40_indImport == i)
                for ind in ("0", "1")
            ]
        else:
            groups = [origins]
        for group in groups:
            total = sum(group.mapped("nfe40_pOrig"))
            if group and abs(total - 100) > ORIGIN_TOLERANCE:
                errors.append(
                    _(
                        "%(item)s: the origin percentages must add up to 100 "
                        "(rejection 958).",
                        item=item,
                    )
                )
        return errors
