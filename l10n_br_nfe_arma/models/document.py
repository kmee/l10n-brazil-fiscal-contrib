# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    MODELO_FISCAL_NFCE,
)
from odoo.addons.l10n_br_nfe.models.document import filter_processador_edoc_nfe

# leiauteNFe_v4.00.xsd: <arma maxOccurs="500">
ARMA_MAX_OCCURS = 500
ARMA_FIELDS = ("nfe40_tpArma", "nfe40_nSerie", "nfe40_nCano", "nfe40_descr")


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _document_check(self):
        result = super()._document_check()
        for record in self.filtered(filter_processador_edoc_nfe):
            if record.issuer == DOCUMENT_ISSUER_COMPANY:
                record._check_nfe40_arma()
        return result

    def _check_nfe40_arma(self):
        """Refuse to issue an NF-e the SEFAZ would reject because of the
        firearm groups of its items."""
        self.ensure_one()
        lines = self.fiscal_line_ids.filtered("nfe40_arma")
        if not lines:
            return
        # rule L01-10 (rejection 738), NT 2013/005
        if self.document_type_id.code == MODELO_FISCAL_NFCE:
            raise UserError(_("The NFC-e does not accept the firearm group."))
        errors = []
        for line in lines:
            item = line.product_id.display_name or line.name
            if len(line.nfe40_arma) > ARMA_MAX_OCCURS:
                errors.append(
                    _(
                        "%(item)s: the NF-e accepts at most %(max)s firearms per "
                        "item.",
                        item=item,
                        max=ARMA_MAX_OCCURS,
                    )
                )
            for arma in line.nfe40_arma:
                missing = [
                    arma._fields[name].string for name in ARMA_FIELDS if not arma[name]
                ]
                if missing:
                    errors.append(
                        _(
                            "%(item)s, serial %(serial)s: %(fields)s.",
                            item=item,
                            serial=arma.nfe40_nSerie or "?",
                            fields=", ".join(missing),
                        )
                    )
        if errors:
            raise UserError(
                _(
                    "The NF-e firearm data (arma) is incomplete, these fields "
                    "are required:\n%(errors)s",
                    errors="\n".join(errors),
                )
            )
