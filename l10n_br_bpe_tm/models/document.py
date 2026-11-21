# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""BP-e TM: the BP-e of the metropolitan and semi-urban passenger transport
charged by turnstile or counter (NT BP-e 2020.002 v1.01, bpeTM_v1.00.xsd).

The infBPe of the BP-e TM uses the bpe10_ names of the BP-e with other
contents (ide without the trip, detBPeTM grouped by counter equipment, total
instead of infValorBPe and imp), so it is not stacked in the fiscal document
next to the BP-e: the binding is built here from the document, its lines and
the values the l10n_br_bpe already computes (ide, emit, ICMS, IBSCBS).
"""

import os
import re

import nfelib
from nfelib.bpe.bindings.v1_0.bpe_tipos_basico_v1_00 import (
    TbpeTm,
    TendeEmi,
    Timp,
    TrespTec,
)
from nfelib.bpe.bindings.v1_0.bpe_tm_v1_00 import BpeTm
from nfelib.bpe.bindings.v1_0.dfe_tipos_basicos_v1_00 import Tibscbstot

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_bpe.bpe_client.client import BPE_VERSION
from odoo.addons.l10n_br_bpe.bpe_client.servers import Endpoint, get_location

BPE_TM_LAYOUT = "tm"

# NT BP-e 2020.002 v1.01, item 6 (ide/tpBPe): 4 - BP-e Transporte Metropolitano
BPE_TM_TYPE = "4"

BPE_TM_SCHEMA = os.path.join(
    os.path.dirname(nfelib.__file__), "bpe", "schemas", "v1_0", "bpeTM_v1.00.xsd"
)

# bpeTM_v1.00.xsd: up to 99 detBPeTM, each with up to 990 det; idEqpCont and
# nViagem go from 1 to 990
MAX_EQUIPMENTS = 99
MAX_TRIPS = 990

Det = TbpeTm.InfBpe.DetBpeTm.Det


def _money(value):
    return f"{value or 0.0:.2f}"


def _plate(value):
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper()) or None


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    bpe_layout = fields.Selection(
        selection_add=[(BPE_TM_LAYOUT, "BP-e TM")],
        ondelete={BPE_TM_LAYOUT: "set default"},
    )

    bpe_tm_competence_date = fields.Date(
        string="BP-e TM Competence Date",
        compute="_compute_bpe_tm_competence_date",
        store=True,
        readonly=False,
        help="ide/dCompet: day of the trips of the BP-e TM.",
    )

    bpe_tm_cfop_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="BP-e TM CFOP",
        compute="_compute_bpe_tm_cfop_id",
        store=True,
        readonly=False,
        help="ide/CFOP: the BP-e TM has a single CFOP, taken from the lines.",
    )

    @api.depends("document_date")
    @api.depends_context("tz")
    def _compute_bpe_tm_competence_date(self):
        for record in self:
            record.bpe_tm_competence_date = (
                record.document_date
                and fields.Datetime.context_timestamp(
                    record, record.document_date
                ).date()
            )

    @api.depends("fiscal_line_ids.cfop_id")
    def _compute_bpe_tm_cfop_id(self):
        for record in self:
            record.bpe_tm_cfop_id = record.fiscal_line_ids.cfop_id[:1]

    def _is_bpe_tm(self):
        self.ensure_one()
        return self.bpe_layout == BPE_TM_LAYOUT

    ################################
    # Binding
    ################################

    def _bpe_tm_equipments(self):
        """Lines (trips) of each counter equipment, in the line order."""
        equipments = {}
        for line in self.fiscal_line_ids:
            equipments.setdefault(line.bpe_tm_equipment, []).append(line)
        return equipments

    def _bpe_tm_ide(self):
        return TbpeTm.InfBpe.Ide(
            cUF=self.bpe10_cUF,
            tpAmb=self.bpe_environment,
            mod=self.document_type_id.code,
            serie=self.document_serie,
            nBP=self.document_number,
            cBP=self.key_random_code,
            cDV=self.key_check_digit,
            modal=self.bpe10_modal,
            dhEmi=self._export_datetime("document_date"),
            dCompet=str(self.bpe_tm_competence_date),
            tpEmis=self.bpe10_tpEmis,
            verProc=self.bpe10_verProc,
            tpBPe=BPE_TM_TYPE,
            CFOP=self.bpe_tm_cfop_id.code,
        )

    def _bpe_tm_emit(self):
        company = self.company_id
        return TbpeTm.InfBpe.Emit(
            CNPJ=self.bpe10_CNPJ,
            IE=self.bpe10_IE,
            xNome=self.bpe10_xNome,
            xFant=self.bpe10_xFant or None,
            IM=self.bpe10_IM or None,
            CNAE=self.bpe10_CNAE or None,
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
            TAR=company.bpe_tm_tar or None,
        )

    def _bpe_tm_det(self, line, number):
        components = line.bpe_tm_component_ids
        return Det(
            nViagem=str(line.bpe_tm_trip or number),
            cMunIni=line.bpe_tm_start_city_id.ibge_code,
            cMunFim=line.bpe_tm_end_city_id.ibge_code or None,
            nContInicio=line.bpe_tm_counter_start or None,
            nContFim=line.bpe_tm_counter_end or None,
            qPass=str(int(line.quantity)),
            vBP=_money(line.price_gross),
            imp=Det.Imp(
                ICMS=Timp(**self._bpe_icms_groups(line)),
                IBSCBS=self._bpe_ibscbs_binding(line) or None,
            ),
            comp=[
                Det.Comp(xNome=component.name, qComp=f"{component.quantity:05d}")
                for component in components
            ],
        )

    def _bpe_tm_det_bpe_tm(self):
        groups = []
        for equipment, lines in self._bpe_tm_equipments().items():
            first = lines[0]
            end_states = {
                line.bpe_tm_end_city_id.state_id.code
                for line in lines
                if line.bpe_tm_end_city_id
            }
            groups.append(
                TbpeTm.InfBpe.DetBpeTm(
                    idEqpCont=str(equipment),
                    UFIniViagem=first.bpe_tm_start_city_id.state_id.code,
                    UFFimViagem=end_states.pop() if end_states else None,
                    placa=_plate(first.bpe_tm_plate),
                    prefixo=first.bpe_tm_line_prefix or None,
                    det=[
                        self._bpe_tm_det(line, number)
                        for number, line in enumerate(lines, 1)
                    ],
                )
            )
        return groups

    def _bpe_tm_total(self):
        lines = self.fiscal_line_ids
        ibscbs_lines = self._get_bpe_ibscbs_lines()
        ibscbs_total = None
        if ibscbs_lines:
            vibs = sum(ibscbs_lines.mapped("ibs_value"))
            vcbs = sum(ibscbs_lines.mapped("cbs_value"))
            zero = _money(0.0)
            ibscbs_total = Tibscbstot(
                vBCIBSCBS=_money(
                    sum(line.ibs_base or line.cbs_base for line in ibscbs_lines)
                ),
                gIBS=Tibscbstot.GIbs(
                    gIBSUF=Tibscbstot.GIbs.GIbsuf(
                        vDif=zero, vDevTrib=zero, vIBSUF=_money(vibs)
                    ),
                    # the municipal IBS rate is zero in 2026 and 2027 (LC 214/2025)
                    gIBSMun=Tibscbstot.GIbs.GIbsmun(
                        vDif=zero, vDevTrib=zero, vIBSMun=zero
                    ),
                    vIBS=_money(vibs),
                ),
                gCBS=Tibscbstot.GCbs(vDif=zero, vDevTrib=zero, vCBS=_money(vcbs)),
            )
        return TbpeTm.InfBpe.Total(
            qPass=str(int(sum(lines.mapped("quantity")))),
            vBP=_money(sum(lines.mapped("price_gross"))),
            ICMSTot=TbpeTm.InfBpe.Total.Icmstot(
                vBC=_money(sum(lines.mapped("icms_base"))),
                vICMS=_money(sum(lines.mapped("icms_value"))),
            ),
            IBSCBSTot=ibscbs_total,
            # NT BP-e 2026.004 v1.01: vBP in 2026, vBP plus IBS and CBS from 2027
            vTotDFe=_money(self.bpe10_vTotDFe),
        )

    def _bpe_tm_inf_adic(self):
        values = {}
        self._export_tag_bpe_10_infadic([], None, values)
        return values and TbpeTm.InfBpe.InfAdic(**values) or None

    def _bpe_tm_resp_tec(self):
        values = {}
        self._export_tag_bpe_10_infresptec([], None, values)
        return values and TrespTec(**values) or None

    def _bpe_binding(self):
        if not self._is_bpe_tm():
            return super()._bpe_binding()
        return BpeTm(
            infBPe=TbpeTm.InfBpe(
                versao=BPE_VERSION,
                Id=self.bpe10_Id,
                ide=self._bpe_tm_ide(),
                emit=self._bpe_tm_emit(),
                detBPeTM=self._bpe_tm_det_bpe_tm(),
                total=self._bpe_tm_total(),
                infAdic=self._bpe_tm_inf_adic(),
                infRespTec=self._bpe_tm_resp_tec(),
            )
        )

    def _bpe_schema_validation(self, xml_file):
        if not self._is_bpe_tm():
            return super()._bpe_schema_validation(xml_file)
        return BpeTm.schema_validation(xml_file, schema_path=BPE_TM_SCHEMA)

    ################################
    # Transmission and events
    ################################

    def _bpe_transmit(self, signed_xml):
        if not self._is_bpe_tm():
            return super()._bpe_transmit(signed_xml)
        return self._get_bpe_client().envia_bpe_tm(signed_xml)

    def _bpe_proc_tag(self):
        # procBPeTM_v1.00.xsd
        if self._is_bpe_tm():
            return "bpeTMProc"
        return super()._bpe_proc_tag()

    def _bpe_no_boarding(self, justification):
        # NT BP-e 2020.002 v1.01, rule I20a (rejection 703): the BP-e TM has
        # no no boarding, substitution or excess baggage event
        if self._is_bpe_tm():
            raise UserError(_("The BP-e TM has no no boarding event."))
        return super()._bpe_no_boarding(justification)

    ################################
    # Checks
    ################################

    def _check_bpe_required_fields(self):
        if not self._is_bpe_tm():
            return super()._check_bpe_required_fields()
        company = self.company_id
        checks = [
            (company.vat, _("Company CNPJ")),
            (company.state_id, _("Company State")),
            # NT BP-e 2020.002 v1.01, rule H18 (rejection 229)
            (self.bpe10_IE, _("Company State Registration (IE)")),
            (company.sudo().certificate, _("Digital Certificate")),
            (self.bpe_environment, _("BP-e Environment")),
            (self.bpe_tm_competence_date, _("BP-e TM Competence Date")),
            (self.bpe_tm_cfop_id, _("BP-e TM CFOP")),
            (self.fiscal_line_ids, _("Trips (fiscal lines)")),
        ]
        missing = [label for value, label in checks if not value]
        # NT BP-e 2020.002 v1.01, rule H26 (rejection 414)
        if self.bpe10_modal == "1" and not company.bpe_tm_tar:
            missing.append(_("Company BP-e TM TAR (road modal)"))
        if missing:
            raise UserError(
                _("Fill in the required BP-e TM fields:\n- %s") % "\n- ".join(missing)
            )
        errors = self._bpe_tm_check_trips()
        try:
            get_location(
                company.state_id.ibge_code,
                self.bpe_environment,
                Endpoint.RECEPCAO_TM,
                self._bpe_server_key(),
            )
        except ValueError:
            errors.append(
                _(
                    "The authorizer of %(state)s publishes no BPeRecepcaoTM "
                    "service on the Portal BP-e.",
                    state=company.state_id.code,
                )
            )
        if errors:
            raise UserError("\n".join(errors))

    def _bpe_tm_check_trips(self):
        """Trip rules of the NT BP-e 2020.002 v1.01 checked before sending."""
        errors = []
        if self.fiscal_line_ids.cfop_id - self.bpe_tm_cfop_id:
            errors.append(_("A BP-e TM has a single CFOP (ide/CFOP)."))
        equipments = self._bpe_tm_equipments()
        if len(equipments) > MAX_EQUIPMENTS:
            errors.append(
                _("A BP-e TM has up to %s counter equipments.", MAX_EQUIPMENTS)
            )
        for equipment, lines in equipments.items():
            if not 1 <= equipment <= MAX_TRIPS:
                errors.append(
                    _(
                        "The counter equipment must be a number from 1 to %s.",
                        MAX_TRIPS,
                    )
                )
            if len(lines) > MAX_TRIPS:
                errors.append(
                    _(
                        "Counter equipment %(equipment)s: up to %(max)s trips.",
                        equipment=equipment,
                        max=MAX_TRIPS,
                    )
                )
            if len({_plate(line.bpe_tm_plate) for line in lines}) > 1 or (
                len({line.bpe_tm_line_prefix for line in lines}) > 1
            ):
                errors.append(
                    _(
                        "Counter equipment %s: the trips must have the same "
                        "vehicle plate and line prefix (detBPeTM).",
                        equipment,
                    )
                )
            # rules H12 and H13 (rejections 693 and 694)
            start_states = {line.bpe_tm_start_city_id.state_id for line in lines}
            end_states = {
                line.bpe_tm_end_city_id.state_id
                for line in lines
                if line.bpe_tm_end_city_id
            }
            if len(start_states) > 1 or len(end_states) > 1:
                errors.append(
                    _(
                        "Counter equipment %s: the trips must start (and end) "
                        "in the same state (detBPeTM/UFIniViagem and UFFimViagem).",
                        equipment,
                    )
                )
            numbers = [line.bpe_tm_trip for line in lines if line.bpe_tm_trip]
            if len(numbers) != len(set(numbers)):
                errors.append(
                    _("Counter equipment %s: repeated trip number.", equipment)
                )
            for line in lines:
                errors += line._bpe_tm_check_trip()
        return errors
