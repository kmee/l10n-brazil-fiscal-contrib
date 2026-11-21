# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from nfelib.nfse.bindings.v1_0.tipos_complexos_v1_01 import TcrtclocacaoImovel

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

# Anexo VI, leiaute 1.04.01 of NT 009: rule E0931 refuses the imovel group
# for these construction services
OBRA_TAXATION_CODES = (
    "070201",
    "070202",
    "070401",
    "070501",
    "070502",
    "070601",
    "070602",
    "070701",
    "070801",
    "071701",
    "071901",
)
# rules E0932 and E0928: operation indicators of real estate operations
REAL_ESTATE_INDICATORS = ("020101", "020201", "020202", "020301", "020401")
# rule E0938: indicators that need the real estate units
UNIT_INDICATORS = ("020101", "020201", "020301")
# rules E0936, E0937 and E0939: lease of real estate, subitem 99.03
LEASE_SUBITEM = "9903"
# rule E0944: social reducer only for the residential lease
RESIDENTIAL_LEASE_NBS = "110021000"


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    nfse_real_estate_city_id = fields.Many2one(
        comodel_name="res.city",
        string="Property City",
        compute="_compute_nfse_real_estate_city_id",
        store=True,
        readonly=False,
        help="City of the real estate of the operation (imovel/cMun).",
    )
    nfse_real_estate_unit_ids = fields.One2many(
        comodel_name="l10n_br_nfse_nacional.real.estate.unit",
        inverse_name="document_id",
        string="Real Estate Units",
        copy=True,
    )
    nfse_lease_coownership_percent = fields.Float(
        string="Co-ownership (%)",
        default=100.0,
        digits=(5, 2),
        help="Share of the lessor when the property has several owners.",
    )
    nfse_lease_total_amount = fields.Monetary(
        string="Lease Total Amount",
        compute="_compute_nfse_lease_total_amount",
        store=True,
        readonly=False,
        help="Total amount of the lease, not the share of the co-owner.",
    )
    nfse_lease_unconditional_discount = fields.Monetary(
        string="Lease Unconditional Discount",
        compute="_compute_nfse_lease_unconditional_discount",
        store=True,
        readonly=False,
    )
    nfse_lease_conditional_discount = fields.Monetary(
        string="Lease Conditional Discount",
        compute="_compute_nfse_lease_conditional_discount",
        store=True,
        readonly=False,
    )
    nfse_lease_due_date = fields.Date(
        string="Lease Original Due Date",
    )

    @api.depends(
        "nfse_real_estate_unit_ids.partner_id.city_id",
        "fiscal_line_ids.issqn_fg_city_id",
    )
    def _compute_nfse_real_estate_city_id(self):
        for doc in self:
            partners = doc.nfse_real_estate_unit_ids.partner_id
            doc.nfse_real_estate_city_id = (
                partners[:1].city_id or doc.fiscal_line_ids[:1].issqn_fg_city_id
            )

    def _compute_nfse_lease_amount(self, field_name, line_field):
        # one compute per field, so a value given on create protects only it
        for doc in self:
            doc[field_name] = doc.fiscal_line_ids[:1][line_field]

    @api.depends("fiscal_line_ids.price_gross")
    def _compute_nfse_lease_total_amount(self):
        self._compute_nfse_lease_amount("nfse_lease_total_amount", "price_gross")

    @api.depends("fiscal_line_ids.discount_value")
    def _compute_nfse_lease_unconditional_discount(self):
        self._compute_nfse_lease_amount(
            "nfse_lease_unconditional_discount", "discount_value"
        )

    @api.depends("fiscal_line_ids.issqn_desc_cond_amount")
    def _compute_nfse_lease_conditional_discount(self):
        self._compute_nfse_lease_amount(
            "nfse_lease_conditional_discount", "issqn_desc_cond_amount"
        )

    @api.constrains("nfse_lease_coownership_percent")
    def _check_nfse_lease_coownership_percent(self):
        for doc in self:
            if not 0 <= doc.nfse_lease_coownership_percent <= 100:
                raise ValidationError(
                    self.env._("E0940: the co-ownership must be from 0 to 100%.")
                )

    def _export_tag_nfse_10_imovel(self, xsd_fields, class_obj, export_dict):
        """Build the IBSCBS/imovel group of the DPS.

        Called by spec_driven_model while exporting the IBSCBS group of the
        document, so only when the NFS-e carries the tax reform data."""
        line = self._nfse_ibscbs_line()
        code = line.nfse10_cTribNac or ""
        indicator = line.operation_indicator_id.code
        units = self.nfse_real_estate_unit_ids
        if code in OBRA_TAXATION_CODES or indicator not in REAL_ESTATE_INDICATORS:
            if units:
                raise UserError(
                    self.env._(
                        "E0928/E0931: the real estate units of %(document)s are "
                        "only reported for a real estate operation indicator "
                        "outside the construction services.",
                        document=self.display_name,
                    )
                )
            return
        lease = code[:4] == LEASE_SUBITEM
        errors = self._nfse_real_estate_errors(line, indicator, lease)
        if errors:
            raise UserError("\n".join(errors))
        export_dict["cMun"] = self.nfse_real_estate_city_id.ibge_code
        if lease:
            export_dict["gLocacao"] = self._nfse_lease_binding()
        if units:
            export_dict["gUnidImob"] = [unit._nfse_binding() for unit in units]

    def _nfse_real_estate_errors(self, line, indicator, lease):
        """Rules of the imovel group (Anexo VI, leiaute 1.04.01 of NT 009)
        that depend on the service of the line."""
        units = self.nfse_real_estate_unit_ids
        adjustments = units.adjustment_ids
        errors = []
        if indicator in UNIT_INDICATORS and not units:
            errors.append(
                self.env._(
                    "E0938: the operation indicator %(indicator)s needs the "
                    "real estate units.",
                    indicator=indicator,
                )
            )
        if adjustments and not lease:
            errors.append(
                self.env._(
                    "E0939: the tax base adjustments of the units are only "
                    "reported for the lease of real estate (subitem 99.03)."
                )
            )
        if (
            "04" in adjustments.mapped("adjustment_type")
            and line.nfse10_cNBS != RESIDENTIAL_LEASE_NBS
        ):
            errors.append(
                self.env._(
                    "E0944: the social reducer is only deducted from the "
                    "residential lease (NBS 1.1002.10.00)."
                )
            )
        if lease and any(a.amount > self.nfse_lease_total_amount for a in adjustments):
            errors.append(
                self.env._(
                    "E0966: a tax base adjustment exceeds the lease total amount."
                )
            )
        return errors

    def _nfse_lease_binding(self):
        """gLocacao element (TCRTCLocacaoImovel)."""
        self.ensure_one()
        return TcrtclocacaoImovel(
            pCopropriedade=f"{self.nfse_lease_coownership_percent:.2f}",
            vTotOper=f"{self.nfse_lease_total_amount:.2f}",
            vDescIncondTot=self.nfse_lease_unconditional_discount
            and f"{self.nfse_lease_unconditional_discount:.2f}"
            or None,
            vDescCondTot=self.nfse_lease_conditional_discount
            and f"{self.nfse_lease_conditional_discount:.2f}"
            or None,
            dVencOrig=self.nfse_lease_due_date
            and fields.Date.to_string(self.nfse_lease_due_date)
            or None,
        )
