# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    MODELO_FISCAL_NFE,
)
from odoo.addons.l10n_br_nfe.models.document import filter_processador_edoc_nfe

# leiauteNFe_v4.00.xsd, TVeiculo/placa (NT 2011.004) and transp/reboque
PLATE_PATTERN = re.compile(r"[A-Z]{2,3}[0-9]{4}|[A-Z]{3,4}[0-9]{3}|[A-Z0-9]{7}")
TRAILER_MAX_OCCURS = 5
RNTC_MAX_LENGTH = 20


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    transport_vehicle_id = fields.Many2one(
        comodel_name="l10n_br_delivery.carrier.vehicle",
        string="Vehicle",
        compute="_compute_transport_vehicle_id",
        store=True,
        readonly=False,
        domain="['|', ('carrier_id', '=', False), ('carrier_id', '=', carrier_id)]",
        help="Vehicle reported in the veicTransp group of the NF-e. By "
        "default, the vehicle of the carrier when it has only one.",
    )

    transport_trailer_ids = fields.Many2many(
        comodel_name="l10n_br_delivery.carrier.vehicle",
        relation="l10n_br_fiscal_document_transport_trailer_rel",
        column1="document_id",
        column2="vehicle_id",
        string="Trailers",
        domain="['|', ('carrier_id', '=', False), ('carrier_id', '=', carrier_id)]",
        help="Trailers or dollies reported in the reboque groups of the NF-e "
        "(at most 5).",
    )

    ret_transp_service_value = fields.Monetary(
        string="Freight Service Value",
        currency_field="currency_id",
        help="Value of the freight service whose ICMS is retained by the "
        "issuer (retTransp/vServ).",
    )

    ret_transp_base = fields.Monetary(
        string="ICMS Retention Base",
        currency_field="currency_id",
        compute="_compute_ret_transp_base",
        store=True,
        readonly=False,
    )

    ret_transp_percent = fields.Float(
        string="ICMS Retention Rate",
        digits=(5, 2),
    )

    ret_transp_value = fields.Monetary(
        string="ICMS Retained",
        currency_field="currency_id",
        compute="_compute_ret_transp_value",
        store=True,
        readonly=False,
    )

    ret_transp_cfop_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="Freight CFOP",
    )

    ret_transp_city_id = fields.Many2one(
        comodel_name="res.city",
        string="Freight Taxable Event City",
        compute="_compute_ret_transp_city_id",
        store=True,
        readonly=False,
    )

    @api.depends("carrier_id")
    def _compute_transport_vehicle_id(self):
        for record in self:
            vehicles = record.carrier_id.vehicle_ids
            if len(vehicles) == 1:
                record.transport_vehicle_id = vehicles
            elif record.transport_vehicle_id.carrier_id == record.carrier_id:
                record.transport_vehicle_id = record.transport_vehicle_id
            else:
                record.transport_vehicle_id = False

    @api.depends("ret_transp_service_value")
    def _compute_ret_transp_base(self):
        for record in self:
            record.ret_transp_base = record.ret_transp_service_value

    @api.depends("ret_transp_base", "ret_transp_percent")
    def _compute_ret_transp_value(self):
        for record in self:
            record.ret_transp_value = record.currency_id.round(
                record.ret_transp_base * record.ret_transp_percent / 100
            )

    @api.depends("ret_transp_service_value", "company_id")
    def _compute_ret_transp_city_id(self):
        for record in self:
            if record.ret_transp_service_value and not record.ret_transp_city_id:
                record.ret_transp_city_id = record.company_id.partner_id.city_id
            else:
                record.ret_transp_city_id = record.ret_transp_city_id

    @api.constrains("transport_trailer_ids")
    def _check_transport_trailer_ids(self):
        for record in self:
            if len(record.transport_trailer_ids) > TRAILER_MAX_OCCURS:
                raise ValidationError(
                    _(
                        "The NF-e accepts at most %(max)s trailers.",
                        max=TRAILER_MAX_OCCURS,
                    )
                )

    def _nfe40_vehicle_allowed(self):
        """Vehicle and trailers are refused in the NFC-e and in the NF-e
        with the simplified DANFE (rules X18-10 and X22-10, rejections 756
        and 757) and in interstate operations (rule X02-20, rejection 868,
        NT 2017.002)."""
        self.ensure_one()
        return (
            self.document_type == MODELO_FISCAL_NFE
            and self.nfe40_tpImp != "6"
            and self.nfe40_idDest != "2"
        )

    def _nfe40_ret_transp_allowed(self):
        """Rule X11-10 (rejection 755): no ICMS retention of the transport in
        the NFC-e nor in the NF-e with the simplified DANFE."""
        self.ensure_one()
        return self.document_type == MODELO_FISCAL_NFE and self.nfe40_tpImp != "6"

    @staticmethod
    def _nfe40_plate(vehicle):
        return re.sub(r"[^A-Z0-9]", "", (vehicle.plate or "").upper())

    def _nfe40_tveiculo(self, vehicle):
        tveiculo = self._get_binding_class(self.env["nfe.40.tveiculo"])
        return tveiculo(
            placa=self._nfe40_plate(vehicle),
            UF=vehicle.state_id.code or None,
            RNTC=(vehicle.rntc_code or "").strip()[:RNTC_MAX_LENGTH] or None,
        )

    def _export_fields_nfe_40_transp(self, xsd_fields, class_obj, export_dict):
        """Build veicTransp, reboque and retTransp from the document fields
        (dispatched by spec_driven_model while exporting the transp group)."""
        exported = []
        if not self._nfe40_vehicle_allowed():
            exported += ["nfe40_veicTransp", "nfe40_reboque"]
        else:
            if self.transport_vehicle_id:
                export_dict["veicTransp"] = self._nfe40_tveiculo(
                    self.transport_vehicle_id
                )
                exported.append("nfe40_veicTransp")
            if self.transport_trailer_ids:
                export_dict["reboque"] = [
                    self._nfe40_tveiculo(trailer)
                    for trailer in self.transport_trailer_ids
                ]
                exported.append("nfe40_reboque")
        if not self._nfe40_ret_transp_allowed():
            exported.append("nfe40_retTransp")
        elif self.ret_transp_service_value:
            ret_transp = self._get_binding_class(self.env["nfe.40.rettransp"])
            export_dict["retTransp"] = ret_transp(
                vServ=f"{self.ret_transp_service_value:.2f}",
                vBCRet=f"{self.ret_transp_base:.2f}",
                pICMSRet=f"{self.ret_transp_percent:.2f}",
                vICMSRet=f"{self.ret_transp_value:.2f}",
                CFOP=self.ret_transp_cfop_id.code,
                cMunFG=self.ret_transp_city_id.ibge_code,
            )
            exported.append("nfe40_retTransp")
        for field_name in exported:
            if field_name in xsd_fields:
                xsd_fields.remove(field_name)

    def _document_check(self):
        result = super()._document_check()
        for record in self.filtered(filter_processador_edoc_nfe):
            if record.issuer == DOCUMENT_ISSUER_COMPANY:
                record._check_nfe40_transp()
        return result

    def _check_nfe40_transp(self):
        self.ensure_one()
        errors = []
        if self._nfe40_vehicle_allowed():
            for vehicle in self.transport_vehicle_id | self.transport_trailer_ids:
                if not PLATE_PATTERN.fullmatch(self._nfe40_plate(vehicle)):
                    errors.append(
                        _(
                            "%(vehicle)s: the plate must have 7 letters and digits.",
                            vehicle=vehicle.display_name,
                        )
                    )
        if self.ret_transp_service_value:
            if not self._nfe40_ret_transp_allowed():
                errors.append(
                    _(
                        "The ICMS retention of the transport is not accepted in "
                        "the NFC-e nor in the NF-e with the simplified DANFE."
                    )
                )
            elif not (self.ret_transp_cfop_id and self.ret_transp_city_id):
                errors.append(
                    _(
                        "The ICMS retention of the transport needs the freight "
                        "CFOP and the city of the taxable event."
                    )
                )
        if errors:
            raise UserError("\n".join(errors))
