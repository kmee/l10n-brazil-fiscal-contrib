# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from nfelib.bpe.bindings.v1_0.bpe_tipos_basico_v1_00 import TbpeTa

from odoo import fields, models

# bpeTiposBasico_v1.00.xsd, TBPeTA/infBPe/infViagem
TRIP_TYPES = [
    ("00", "Regular Domestic"),
    ("01", "Regular International"),
    ("02", "Non Regular Domestic"),
    ("03", "Non Regular International"),
]

SERVICE_TYPES = [("12", "Commercial"), ("13", "Executive")]

ACCOMMODATION_TYPES = [("6", "Common"), ("7", "Comfort")]

LEG_TYPES = [("1", "Normal"), ("2", "Initial Leg"), ("3", "Connection")]


class BpeTaFlight(models.Model):
    """A flight of a BP-e TA (infViagem)."""

    _name = "l10n_br_bpe_ta.flight"
    _description = "BP-e TA Flight"
    _order = "document_id, sequence, id"

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        required=True,
        ondelete="cascade",
        index=True,
    )

    sequence = fields.Integer(default=10)

    flight_number = fields.Char(required=True, size=20, help="nroVoo")

    airline_code = fields.Char(
        string="Operating Airline",
        required=True,
        size=3,
        help="SiglaCiaOperVoo: IATA code of the airline that operates the flight.",
    )

    trip_type = fields.Selection(
        selection=TRIP_TYPES, required=True, default="00", help="tpViagem"
    )

    origin_airport = fields.Char(
        required=True, size=4, help="cAeroOrig: IATA code of the origin airport."
    )

    destination_airport = fields.Char(
        required=True,
        size=4,
        help="cAeroDest: IATA code of the destination airport.",
    )

    service_type = fields.Selection(
        selection=SERVICE_TYPES, required=True, default="12", help="tpServ"
    )

    accommodation_type = fields.Selection(
        selection=ACCOMMODATION_TYPES, required=True, default="6", help="tpAcomodacao"
    )

    leg_type = fields.Selection(
        selection=LEG_TYPES, required=True, default="1", help="tpTrecho"
    )

    departure_date = fields.Datetime(
        string="Flight Date", required=True, help="dhViagem"
    )

    connection_date = fields.Datetime(
        help="dhConexao: informed only on the connection legs."
    )

    def _bpe_ta_datetime(self, value):
        return (
            value
            and fields.Datetime.context_timestamp(self, value).isoformat("T")
            or None
        )

    def _bpe_ta_binding(self):
        self.ensure_one()
        return TbpeTa.InfBpe.InfViagem(
            nroVoo=self.flight_number,
            SiglaCiaOperVoo=self.airline_code.upper(),
            tpViagem=self.trip_type,
            cAeroOrig=self.origin_airport.upper(),
            cAeroDest=self.destination_airport.upper(),
            tpServ=self.service_type,
            tpAcomodacao=self.accommodation_type,
            tpTrecho=self.leg_type,
            dhViagem=self._bpe_ta_datetime(self.departure_date),
            dhConexao=self._bpe_ta_datetime(self.connection_date),
        )
