# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""BP-e TA: the BP-e of the air passenger transport (NT BP-e 2025.002 v2.00,
bpeTA_v1.00.xsd).

The infBPe of the BP-e TA uses the bpe10_ names of the BP-e with other
contents (flights in infViagem, imp with IBSCBS and no ICMS, other codes
in tpComp and tpDesconto), so it is not stacked in the fiscal document next
to the BP-e: the binding is built here from the document, its lines, its
flights and the values the l10n_br_bpe already computes (ide, emit, buyer,
passenger, payments, IBSCBS).
"""

import os

import nfelib
from nfelib.bpe.bindings.v1_0.bpe_ta_v1_00 import BpeTa
from nfelib.bpe.bindings.v1_0.bpe_tipos_basico_v1_00 import (
    TbpeTa,
    TendeEmi,
    Tendereco,
    TrespTec,
)

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_bpe.bpe_client.client import BPE_VERSION

BPE_TA_LAYOUT = "ta"

# NT BP-e 2025.002 v2.00, item 4.1: the modal of the BP-e TA is 2 (air)
BPE_TA_MODAL = "2"

# NT BP-e 2025.002 v2.00, items 2.2 and 4.1: the BP-e TA is authorized by
# the SEFAZ Virtual; the Portal BP-e lists BPeRecepcaoTA on SVRS only
BPE_TA_AUTHORIZER = "SVRS"

BPE_TA_SCHEMA = os.path.join(
    os.path.dirname(nfelib.__file__), "bpe", "schemas", "v1_0", "bpeTA_v1.00.xsd"
)

# TBPeTA/infBPe/ide/tpCompra
PURCHASE_TYPES = [
    ("0", "Normal"),
    ("1", "Multiple (charter)"),
    ("2", "Linked to a Multiple BP-e"),
]

# TBPeTA/infBPe/infValorBPe/tpDesconto
DISCOUNT_TYPES = [
    ("03", "Children"),
    ("09", "Company Professional (employees or crew)"),
    ("10", "Loyalty Program (Miles)"),
    ("11", "Corporate Agreements"),
    ("12", "Passenger Group Agreements"),
    ("13", "Companion of a Passenger with Special Needs"),
    ("99", "Other"),
]

# card group required for credit and debit cards (rule F71)
CARD_PAYMENTS = ("03", "04")

FOREIGN_CITY_CODE = "9999999"


def _money(value):
    return f"{value or 0.0:.2f}"


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    bpe_layout = fields.Selection(
        selection_add=[(BPE_TA_LAYOUT, "BP-e TA")],
        ondelete={BPE_TA_LAYOUT: "set default"},
    )

    bpe_ta_purchase_type = fields.Selection(
        selection=PURCHASE_TYPES,
        string="BP-e TA Purchase Type",
        default="0",
        help="ide/tpCompra",
    )

    bpe_ta_multiple_key = fields.Char(
        string="Multiple BP-e Access Key",
        size=44,
        help="infBPeVinculado/chBPeMultiplo, for the purchase linked to a "
        "multiple BP-e.",
    )

    bpe_ta_iata_number = fields.Char(
        string="IATA Ticket Number", size=20, help="ide/nroBPIATA"
    )

    bpe_ta_destination_abroad = fields.Boolean(
        string="Destination Abroad",
        help="International flight: the trip ends abroad (UFFim EX and "
        "cMunFim 9999999, NT BP-e 2025.002 v2.00, rule F17).",
    )

    bpe_ta_discount_type = fields.Selection(
        selection=DISCOUNT_TYPES,
        string="BP-e TA Discount Type",
        help="infValorBPe/tpDesconto",
    )

    bpe_ta_discount_code = fields.Char(
        string="BP-e TA Discount Code",
        size=20,
        help="infValorBPe/cDesconto, with the discount type Other.",
    )

    bpe_ta_flight_ids = fields.One2many(
        comodel_name="l10n_br_bpe_ta.flight",
        inverse_name="document_id",
        string="Flights",
        copy=True,
    )

    def _is_bpe_ta(self):
        self.ensure_one()
        return self.bpe_layout == BPE_TA_LAYOUT

    def _bpe_server_key(self):
        if self._is_bpe_ta():
            return BPE_TA_AUTHORIZER
        return super()._bpe_server_key()

    ################################
    # Binding
    ################################

    def _bpe_ta_ide(self):
        abroad = self.bpe_ta_destination_abroad
        return TbpeTa.InfBpe.Ide(
            cUF=self.bpe10_cUF,
            tpAmb=self.bpe_environment,
            mod=self.document_type_id.code,
            serie=self.document_serie,
            nBP=self.document_number,
            cBP=self.key_random_code,
            cDV=self.key_check_digit,
            modal=BPE_TA_MODAL,
            dhEmi=self._export_datetime("document_date"),
            tpEmis=self.bpe10_tpEmis,
            verProc=self.bpe10_verProc,
            tpBPe="0",
            tpCompra=self.bpe_ta_purchase_type,
            indPres=self.bpe10_indPres,
            UFIni=self.bpe10_UFIni,
            cMunIni=self.bpe10_cMunIni,
            UFFim="EX" if abroad else self.bpe10_UFFim,
            cMunFim=FOREIGN_CITY_CODE if abroad else self.bpe10_cMunFim,
            nroBPIATA=self.bpe_ta_iata_number or None,
        )

    def _bpe_ta_emit(self):
        return TbpeTa.InfBpe.Emit(
            CNPJ=self.bpe10_CNPJ,
            # optional in the BP-e TA (NT BP-e 2025.002 v1.02)
            IE=self.bpe10_IE or None,
            xNome=self.bpe10_xNome,
            xFant=self.bpe10_xFant or None,
            CRT=self.bpe10_CRT,
            enderEmit=TendeEmi(
                xLgr=self.bpe10_xLgr,
                nro=self.bpe10_nro,
                xCpl=self.bpe10_xCpl or None,
                xBairro=self.bpe10_xBairro,
                cMun=self.bpe10_cMun,
                xMun=self.bpe10_xMun,
                CEP=self.bpe10_CEP or None,
                UF=self.bpe10_UF,
                fone=self.bpe10_fone or None,
                email=self.bpe10_email or None,
            ),
        )

    def _bpe_ta_comp(self):
        if not self.partner_id:
            return None
        buyer, address = {}, {}
        self._export_tag_bpe_10_comp([], None, buyer)
        self._export_tag_bpe_10_endercomp([], None, address)
        address = {key: value for key, value in address.items() if value}
        return TbpeTa.InfBpe.Comp(**buyer, enderComp=Tendereco(**address))

    def _bpe_ta_passenger(self):
        passenger = self.bpe10_infPassageiro
        if not passenger or self.bpe_ta_purchase_type == "1":
            return None
        return TbpeTa.InfBpe.InfPassagem.InfPassageiro(
            xNome=passenger.bpe10_xNome,
            CPF=passenger.bpe10_CPF or None,
            tpDoc=passenger.bpe10_tpDoc,
            nDoc=passenger.bpe10_nDoc,
            xDoc=passenger.bpe10_xDoc or None,
            dNasc=passenger.bpe10_dNasc or None,
            fone=passenger.bpe10_fone or None,
            email=passenger.bpe10_email or None,
        )

    def _bpe_ta_values(self):
        return TbpeTa.InfBpe.InfValorBpe(
            vBP=_money(self.bpe10_vBP),
            vDesconto=_money(self.bpe10_vDesconto),
            vPgto=_money(self.bpe10_vPgto),
            vTroco=_money(self.bpe10_vTroco),
            tpDesconto=self.bpe_ta_discount_type or None,
            xDesconto=self.bpe10_xDesconto or None,
            cDesconto=self.bpe_ta_discount_code or None,
            comp=[
                TbpeTa.InfBpe.InfValorBpe.Comp(
                    tpComp=line.bpe_ta_component_type, vComp=_money(line.price_gross)
                )
                for line in self.fiscal_line_ids
            ],
        )

    def _bpe_ta_imp(self):
        return TbpeTa.InfBpe.Imp(
            IBSCBS=self._bpe_ibscbs_binding() or None,
            vTotTrib=_money(self.amount_estimate_tax)
            if self.amount_estimate_tax
            else None,
            # NT BP-e 2025.002 v2.00, rule F140 (rejection 365): vBP in 2026,
            # vBP plus IBS and CBS from 2027
            vTotDFe=_money(self.bpe10_vTotDFe),
        )

    def _bpe_ta_card(self, card):
        if not card:
            return None
        return TbpeTa.InfBpe.Pag.Card(
            tpIntegra=card.bpe10_tpIntegra,
            CNPJ=card.bpe10_CNPJ or None,
            tBand=card.bpe10_tBand or None,
            xBand=card.bpe10_xBand or None,
            cAut=card.bpe10_cAut or None,
            nsuTrans=card.bpe10_nsuTrans or None,
            nsuHost=card.bpe10_nsuHost or None,
            nParcelas=card.bpe10_nParcelas or None,
            infAdCard=card.bpe10_infAdCard or None,
        )

    def _bpe_ta_pag(self):
        return [
            TbpeTa.InfBpe.Pag(
                tPag=payment.bpe10_tPag,
                xPag=payment.bpe10_xPag or None,
                nDocPag=payment.bpe10_nDocPag or None,
                vPag=_money(payment.bpe10_vPag),
                card=self._bpe_ta_card(payment.bpe10_card),
            )
            for payment in self.bpe10_pag
        ]

    def _bpe_ta_inf_adic(self):
        values = {}
        self._export_tag_bpe_10_infadic([], None, values)
        return values and TbpeTa.InfBpe.InfAdic(**values) or None

    def _bpe_ta_resp_tec(self):
        values = {}
        self._export_tag_bpe_10_infresptec([], None, values)
        return values and TrespTec(**values) or None

    def _bpe_binding(self):
        if not self._is_bpe_ta():
            return super()._bpe_binding()
        inf_bpe = TbpeTa.InfBpe(
            versao=BPE_VERSION,
            Id=self.bpe10_Id,
            ide=self._bpe_ta_ide(),
            emit=self._bpe_ta_emit(),
            comp=self._bpe_ta_comp(),
            infPassagem=TbpeTa.InfBpe.InfPassagem(
                dhEmb=self._export_datetime("bpe10_dhEmb"),
                dhValidade=self._export_datetime("bpe10_dhValidade"),
                infPassageiro=self._bpe_ta_passenger(),
            ),
            infViagem=[flight._bpe_ta_binding() for flight in self.bpe_ta_flight_ids],
            infAdic=self._bpe_ta_inf_adic(),
            infRespTec=self._bpe_ta_resp_tec(),
        )
        # NT BP-e 2025.002 v2.00, rules F53 and F54: values, taxes and
        # payments, or the key of the multiple BP-e the purchase is linked to
        if self.bpe_ta_purchase_type == "2":
            inf_bpe.infBPeVinculado = TbpeTa.InfBpe.InfBpeVinculado(
                chBPeMultiplo=self.bpe_ta_multiple_key
            )
        else:
            inf_bpe.infValorBPe = self._bpe_ta_values()
            inf_bpe.imp = self._bpe_ta_imp()
            inf_bpe.pag = self._bpe_ta_pag()
        return BpeTa(
            infBPe=inf_bpe,
            infBPeSupl=TbpeTa.InfBpeSupl(qrCodBPe=self._get_bpe_qrcode()),
        )

    def _bpe_schema_validation(self, xml_file):
        if not self._is_bpe_ta():
            return super()._bpe_schema_validation(xml_file)
        return BpeTa.schema_validation(xml_file, schema_path=BPE_TA_SCHEMA)

    def _bpe_transmit(self, signed_xml):
        if not self._is_bpe_ta():
            return super()._bpe_transmit(signed_xml)
        return self._get_bpe_client().envia_bpe_ta(signed_xml)

    ################################
    # Checks
    ################################

    def _check_bpe_required_fields(self):
        if not self._is_bpe_ta():
            return super()._check_bpe_required_fields()
        company = self.company_id
        linked = self.bpe_ta_purchase_type == "2"
        checks = [
            (company.vat, _("Company CNPJ")),
            (company.state_id, _("Company State")),
            (company.sudo().certificate, _("Digital Certificate")),
            (self.bpe_environment, _("BP-e Environment")),
            (self.bpe_origin_city_id, _("Origin City")),
            (
                self.bpe_destination_city_id or self.bpe_ta_destination_abroad,
                _("Destination City"),
            ),
            (self.bpe10_dhEmb, _("Boarding Date")),
            (self.bpe10_dhValidade, _("Ticket Validity Date")),
            (self.bpe_ta_flight_ids, _("Flights")),
        ]
        if linked:
            checks.append((self.bpe_ta_multiple_key, _("Multiple BP-e Access Key")))
        else:
            checks += [
                (self.fiscal_line_ids, _("Value Components (fiscal lines)")),
                (self.bpe10_pag, _("Payment Information")),
                # imp/IBSCBS is required in bpeTA_v1.00.xsd
                (self._get_bpe_ibscbs_lines(), _("IBS and CBS of the lines")),
            ]
        missing = [label for value, label in checks if not value]
        if missing:
            raise UserError(
                _("Fill in the required BP-e TA fields:\n- %s") % "\n- ".join(missing)
            )
        errors = self._bpe_ta_check_purchase() + self._bpe_ta_check_flights()
        if not linked:
            errors += self._bpe_ta_check_values()
        if errors:
            raise UserError("\n".join(errors))

    def _bpe_ta_check_purchase(self):
        """NT BP-e 2025.002 v2.00, rules F49 to F54."""
        errors = []
        purchase_type = self.bpe_ta_purchase_type
        # F50 and F51 (rejections 441 and 442)
        if purchase_type in ("0", "2") and not self.bpe10_infPassageiro:
            errors.append(_("Inform the passenger of the BP-e TA."))
        # F52 (rejection 443)
        if purchase_type == "1" and not self.partner_id:
            errors.append(_("A multiple BP-e TA requires the buyer (partner)."))
        # F55 (rejection 446)
        key = self.bpe_ta_multiple_key or ""
        if purchase_type == "2" and not (len(key) == 44 and key[20:22] == "63"):
            errors.append(_("Invalid access key of the multiple BP-e."))
        # F49 (rejection 254)
        if self.bpe10_dhEmb and self.document_date > self.bpe10_dhEmb:
            errors.append(_("The boarding date must not be before the issue date."))
        return errors

    def _bpe_ta_check_flights(self):
        """NT BP-e 2025.002 v2.00, rules F19 to F23."""
        errors = []
        flights = self.bpe_ta_flight_ids
        legs = flights.mapped("leg_type")
        # F19 and F20 (rejections 419 and 420)
        if len(flights) == 1 and legs != ["1"]:
            errors.append(_("A single flight must have the leg type Normal."))
        if len(flights) > 1 and (
            legs.count("2") != 1 or legs.count("3") != len(flights) - 1
        ):
            errors.append(
                _(
                    "With connections, one flight is the Initial Leg and the "
                    "others are Connection legs."
                )
            )
        for flight in flights:
            connection = flight.leg_type == "3"
            # F21 and F22 (rejections 484 and 485)
            if connection != bool(flight.connection_date):
                errors.append(
                    _(
                        "Flight %s: the connection date is informed on the "
                        "Connection legs only.",
                        flight.flight_number,
                    )
                )
            # F23 (rejection 486)
            elif connection and flight.connection_date <= self.bpe10_dhEmb:
                errors.append(
                    _(
                        "Flight %s: the connection date must be after the "
                        "boarding date.",
                        flight.flight_number,
                    )
                )
        return errors

    def _bpe_ta_check_values(self):
        """NT BP-e 2025.002 v2.00, rules F65 to F71."""
        errors = []
        discount = self.bpe10_vDesconto
        if self.bpe_ta_discount_type:
            # F65 (rejection 437) and F66 (rejection 401)
            if not self.bpe10_xDesconto:
                errors.append(_("Inform the description of the discount."))
            if discount <= 0:
                errors.append(_("A discount type requires a discount value."))
        # F67 (rejection 500)
        elif discount > 0 or self.bpe10_xDesconto:
            errors.append(_("Inform the discount type of the BP-e TA."))
        # F69 (rejection 438), with the tolerance of 1.00 of the NT; from 2027
        # on the payments also cover IBS and CBS, the part of vTotDFe above vBP
        paid = sum(self.bpe10_pag.mapped("bpe10_vPag"))
        due = (
            self.bpe10_vPgto + self.bpe10_vTroco + (self.bpe10_vTotDFe - self.bpe10_vBP)
        )
        if abs(paid - due) > 1:
            errors.append(
                _("The payments must add up to the amount paid plus the change.")
            )
        # F71 (rejection 475)
        if any(
            payment.bpe10_tPag in CARD_PAYMENTS and not payment.bpe10_card
            for payment in self.bpe10_pag
        ):
            errors.append(_("Card payments require the card group."))
        return errors
