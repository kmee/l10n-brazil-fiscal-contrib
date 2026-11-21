# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from erpbrasil.base.misc import punctuation_rm

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models

from ...constants.nfeabi import NFEABI_PROPERTY_CLASSES, NFEABI_PROPERTY_KINDS


class NfeAbiProperty(spec_models.SpecModel):
    """Real estate property of the NF-e ABI (MOC NF-e ABI 1.00a, group G and
    NT 2026.001, group G). The record is also its cadastro (G03) and its
    address (G12)."""

    _name = "l10n_br_nfeabi.property"
    _inherit = ["nfeabi.10.timovel", "nfeabi.10.tcadastroimovel"]
    _description = "NF-e ABI Real Estate Property"
    # the binding of the imovel tag of the document; cadastro and enderImovel
    # are resolved by the xsd_type of their fields
    _nfeabi10_binding_type_imovel = "Timovel"

    name = fields.Char(required=True)

    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
    )

    nfeabi10_tipo = fields.Selection(
        selection=[("1", "Urbano"), ("2", "Rural")],
        string="Property Type",
        required=True,
        default="1",
    )

    nfeabi10_cadastro = fields.Many2one(
        comodel_name="l10n_br_nfeabi.property", compute="_compute_nfeabi_self"
    )

    nfeabi10_cCIB = fields.Char(string="CIB")

    nfeabi10_nIPTU = fields.Char(string="IPTU Number")

    nfeabi10_indIPTU = fields.Char(compute="_compute_nfeabi_indicators")

    nfeabi10_nINCRA = fields.Char(string="INCRA Number")

    nfeabi10_indINCRA = fields.Char(compute="_compute_nfeabi_indicators")

    nfeabi10_nRIP = fields.Char(string="RIP Number")

    nfeabi10_indRIP = fields.Char(compute="_compute_nfeabi_indicators")

    nfeabi10_espImovel = fields.Selection(
        selection=NFEABI_PROPERTY_KINDS,
        string="Property Kind",
        required=True,
    )

    nfeabi10_xOutrosEspecies = fields.Char(string="Other Kind")

    nfeabi10_enquadramento = fields.Selection(
        selection=NFEABI_PROPERTY_CLASSES,
        string="Property Class",
        required=True,
    )

    nfeabi10_obsLocalImovel = fields.Char(string="Location Notes")

    nfeabi10_areaTotal = fields.Float(
        string="Total Area", digits=(13, 2), xsd_type="TDec_1302"
    )

    nfeabi10_uAreaTotal = fields.Selection(
        selection=[("m2", "Square meters (m2)"), ("ha", "Hectares (ha)")],
        string="Total Area Unit",
    )

    nfeabi10_cartorioRegistro = fields.Char(string="Registry Office")

    nfeabi10_matricTransc = fields.Char(string="Registration Number")

    street_name = fields.Char()
    street_number = fields.Char()
    street2 = fields.Char()
    district = fields.Char()
    city_id = fields.Many2one(comodel_name="res.city", string="City")
    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="State",
        related="city_id.state_id",
        store=True,
        readonly=True,
    )
    zip = fields.Char()

    nfeabi10_enderImovel = fields.Many2one(
        comodel_name="l10n_br_nfeabi.property", compute="_compute_nfeabi_self"
    )
    nfeabi10_xLgr = fields.Char(related="street_name")
    nfeabi10_nro = fields.Char(related="street_number")
    nfeabi10_xCpl = fields.Char(related="street2")
    nfeabi10_xBairro = fields.Char(related="district")
    nfeabi10_cMun = fields.Char(related="city_id.ibge_code")
    nfeabi10_xMun = fields.Char(related="city_id.name")
    nfeabi10_UF = fields.Char(related="state_id.code")
    nfeabi10_CEP = fields.Char(compute="_compute_nfeabi_cep")

    def _compute_nfeabi_self(self):
        for record in self:
            record.nfeabi10_cadastro = record
            record.nfeabi10_enderImovel = record

    @api.depends("nfeabi10_nIPTU", "nfeabi10_nINCRA", "nfeabi10_nRIP")
    def _compute_nfeabi_indicators(self):
        # NT 2026.001, rules G06-10, G08-10 and G08b-10: the indicator is 1
        # when the number is informed
        for record in self:
            record.nfeabi10_indIPTU = "1" if record.nfeabi10_nIPTU else "0"
            record.nfeabi10_indINCRA = "1" if record.nfeabi10_nINCRA else "0"
            record.nfeabi10_indRIP = "1" if record.nfeabi10_nRIP else "0"

    @api.depends("zip")
    def _compute_nfeabi_cep(self):
        for record in self:
            record.nfeabi10_CEP = punctuation_rm(record.zip or "") or False

    def _nfeabi_missing_fields(self):
        """Labels of the property fields the layout needs and are empty."""
        self.ensure_one()
        missing = []
        for field_name in ("street_name", "street_number", "city_id"):
            if not self[field_name]:
                missing.append(self._fields[field_name].string)
        if self.nfeabi10_espImovel == "99" and not self.nfeabi10_xOutrosEspecies:
            # MOC NF-e ABI 1.00a, G10
            missing.append(self._fields["nfeabi10_xOutrosEspecies"].string)
        if self.nfeabi10_tipo == "2":
            # MOC NF-e ABI 1.00a, G24 and G25: area of the rural property
            for field_name in ("nfeabi10_areaTotal", "nfeabi10_uAreaTotal"):
                if not self[field_name]:
                    missing.append(self._fields[field_name].string)
        return missing
