# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import re
from unicodedata import normalize

from erpbrasil.base.fiscal.edoc import ChaveEdoc
from erpbrasil.base.misc import punctuation_rm
from nfelib.bpe.bindings.v1_0.bpe_tipos_basico_v1_00 import Tbpe, Timp
from nfelib.bpe.bindings.v1_0.bpe_v1_00 import Bpe
from nfelib.bpe.bindings.v1_0.ev_canc_bpe_v1_00 import (
    EvCancBpe,
    EvCancBpeDescEvento,
)
from nfelib.bpe.bindings.v1_0.ev_nao_emb_bpe_v1_00 import (
    EvNaoEmbBpe,
    EvNaoEmbBpeDescEvento,
)
from nfelib.bpe.bindings.v1_0.evento_bpe_v1_00 import EventoBpe
from nfelib.bpe.bindings.v1_0.tipos_geral_bpe_v1_00 import Tamb, TcorgaoIbge

from odoo import _, api, fields
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_FISCAL_CANCELADO,
)
from odoo.addons.l10n_br_fiscal_edi.tools import tax_authority_date_to_utc
from odoo.addons.spec_driven_model.models import spec_models

from ...bpe_client.client import BPE_VERSION, BpeClient
from ...bpe_client.servers import Endpoint, get_location
from ...constants import (
    BPE_AUTHORIZED,
    BPE_CANCEL_EVENT,
    BPE_EVENT_REGISTERED,
    BPE_IBSCBS_IN_TOTAL_DATE,
    BPE_NO_BOARDING_EVENT,
    BPE_SCHEMAS,
    MODELO_FISCAL_BPE,
)

ICMS_GROUP_BY_CST = {
    "00": "ICMS00",
    "20": "ICMS20",
    "40": "ICMS45",
    "41": "ICMS45",
    "51": "ICMS45",
    "90": "ICMS90",
}


def filtered_processador_edoc_bpe(record):
    return (
        record.processador_edoc == PROCESSADOR_OCA
        and record.document_type_id.code == MODELO_FISCAL_BPE
    )


def _clean_text(text):
    return (
        normalize("NFKD", text)
        .encode("ASCII", "ignore")
        .decode("ASCII")
        .replace("\n", " ")
        .replace("\r", "")
        .strip()
    )


def _phone(value):
    """DDD and number only (fone of the BP-e: [0-9]{7,12})."""
    digits = re.sub(r"\D", "", value or "")
    if len(digits) > 11 and digits.startswith("55"):
        digits = digits[2:]
    return digits or False


def _money(value):
    return f"{value or 0.0:.2f}"


def _rate(value):
    return f"{value or 0.0:.4f}"


class BPe(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document"
    _inherit = ["l10n_br_fiscal.document", "bpe.10.tbpe_infbpe"]

    _bpe10_odoo_module = (
        "odoo.addons.l10n_br_bpe_spec.models.v1_0.bpe_tipos_basico_v1_00"
    )
    _bpe10_stacking_mixin = "bpe.10.tbpe_infbpe"
    # pgtoVinc (NT BP-e 2026.001) is not stacked: it is optional and an
    # empty stacked group would be exported as an invalid <pgtoVinc/>
    _bpe10_stacking_skip_paths = ["bpe10_pgtoVinc"]
    _bpe_search_keys = ["bpe10_Id"]

    # When dynamic stacking is applied the BP-e structure is:
    # (+ stacked in the document / - many2one / = one2many)
    INFBPE_TREE = """
+ <infBPe>
    + <ide>
    + <emit>
        + <enderEmit>
    - <comp> (partner_id)
    + <infPassagem>
        - <infPassageiro>
    = <infViagem>
    + <infValorBPe>
        = <Comp> (fiscal lines)
    + <imp>
        + <ICMS> (fiscal lines)
        - <IBSCBS> (fiscal lines)
    = <pag>
    - <infAdic>
    - <infRespTec>"""

    def _register_hook(self):
        """Build the concrete BP-e spec models whatever the MRO resolves to.

        The hook of spec_driven_model takes the schema from the MRO: with
        another spec driven module extending the fiscal document after this
        one (NF3e, NFCom...), it resolves to that schema and the BP-e models
        (infPassageiro, infViagem, pag...) would get no table.
        """
        res = super()._register_hook()
        self.with_context(
            spec_schema="bpe", spec_version="10"
        )._register_remaining_schema_models_hook()
        return res

    bpe_environment = fields.Selection(
        selection=[("1", "Production"), ("2", "Homologation")],
        string="BP-e Environment",
        copy=False,
        default=lambda self: self.env.company.bpe_environment,
    )

    bpe_origin_city_id = fields.Many2one(
        comodel_name="res.city",
        string="Origin City",
        domain=[("country_id.code", "=", "BR")],
    )

    bpe_destination_city_id = fields.Many2one(
        comodel_name="res.city",
        string="Destination City",
        domain=[("country_id.code", "=", "BR")],
    )

    ##########################
    # BP-e tag: infBPe
    ##########################

    bpe10_versao = fields.Char(compute="_compute_bpe10_versao")

    bpe10_Id = fields.Char(compute="_compute_bpe10_id_tag")

    def _compute_bpe10_versao(self):
        self.bpe10_versao = BPE_VERSION

    @api.depends("document_type_id", "document_key")
    def _compute_bpe10_id_tag(self):
        for record in self:
            record.bpe10_Id = False
            if record.document_type_id.prefix and record.document_key:
                record.bpe10_Id = (
                    f"{record.document_type_id.prefix}{record.document_key}"
                )

    ##########################
    # BP-e tag: ide
    ##########################

    bpe10_cUF = fields.Selection(compute="_compute_bpe10_ide")

    bpe10_tpAmb = fields.Selection(related="bpe_environment")

    bpe10_mod = fields.Selection(compute="_compute_bpe10_ide")

    bpe10_serie = fields.Char(related="document_serie")

    bpe10_nBP = fields.Char(related="document_number")

    bpe10_cBP = fields.Char(related="key_random_code")

    bpe10_cDV = fields.Char(related="key_check_digit")

    bpe10_modal = fields.Selection(default="1")

    bpe10_dhEmi = fields.Datetime(related="document_date")

    bpe10_tpEmis = fields.Selection(default="1")

    bpe10_verProc = fields.Char(
        default=lambda self: self.env["ir.config_parameter"]
        .sudo()
        .get_param("l10n_br_bpe.version.name", default="Odoo Brasil OCA v16")
    )

    bpe10_tpBPe = fields.Selection(default="0")

    bpe10_indPres = fields.Selection(default="1")

    bpe10_UFIni = fields.Selection(compute="_compute_bpe10_ide")

    bpe10_cMunIni = fields.Char(compute="_compute_bpe10_ide")

    bpe10_UFFim = fields.Selection(compute="_compute_bpe10_ide")

    bpe10_cMunFim = fields.Char(compute="_compute_bpe10_ide")

    @api.depends(
        "company_id",
        "document_type_id",
        "bpe_origin_city_id",
        "bpe_destination_city_id",
    )
    def _compute_bpe10_ide(self):
        for record in self:
            origin = record.bpe_origin_city_id
            destination = record.bpe_destination_city_id
            record.bpe10_cUF = record.company_id.state_id.ibge_code or False
            record.bpe10_mod = (
                record.document_type_id.code
                if record.document_type_id.code == MODELO_FISCAL_BPE
                else False
            )
            record.bpe10_UFIni = origin.state_id.code or False
            record.bpe10_cMunIni = origin.ibge_code or False
            record.bpe10_UFFim = destination.state_id.code or False
            record.bpe10_cMunFim = destination.ibge_code or False

    ##########################
    # BP-e tag: emit and enderEmit
    ##########################

    bpe10_CNPJ = fields.Char(compute="_compute_bpe10_emit")
    bpe10_IE = fields.Char(compute="_compute_bpe10_emit")
    bpe10_xNome = fields.Char(compute="_compute_bpe10_emit")
    bpe10_xFant = fields.Char(compute="_compute_bpe10_emit")
    bpe10_IM = fields.Char(compute="_compute_bpe10_emit")
    bpe10_CNAE = fields.Char(compute="_compute_bpe10_emit")
    bpe10_CRT = fields.Selection(compute="_compute_bpe10_emit")
    bpe10_xLgr = fields.Char(compute="_compute_bpe10_emit")
    bpe10_nro = fields.Char(compute="_compute_bpe10_emit")
    bpe10_xCpl = fields.Char(compute="_compute_bpe10_emit")
    bpe10_xBairro = fields.Char(compute="_compute_bpe10_emit")
    bpe10_cMun = fields.Char(compute="_compute_bpe10_emit")
    bpe10_xMun = fields.Char(compute="_compute_bpe10_emit")
    bpe10_CEP = fields.Char(compute="_compute_bpe10_emit")
    bpe10_UF = fields.Selection(compute="_compute_bpe10_emit")
    bpe10_fone = fields.Char(compute="_compute_bpe10_emit")
    bpe10_email = fields.Char(compute="_compute_bpe10_emit")

    @api.depends("company_id")
    def _compute_bpe10_emit(self):
        for record in self:
            company = record.company_id
            partner = company.partner_id
            record.bpe10_CNPJ = punctuation_rm(company.vat or "") or False
            record.bpe10_IE = punctuation_rm(partner.l10n_br_ie_code or "") or False
            record.bpe10_xNome = company.legal_name or company.name
            record.bpe10_xFant = company.name
            record.bpe10_IM = punctuation_rm(partner.l10n_br_im_code or "") or False
            # IM and CNAE go together in the schema (sequence IM, CNAE)
            record.bpe10_CNAE = (
                record.bpe10_IM
                and punctuation_rm(company.cnae_main_id.code or "")
                or False
            )
            record.bpe10_CRT = (
                company.tax_framework
                if company.tax_framework in ("1", "2", "3")
                else False
            )
            record.bpe10_xLgr = company.street_name or company.street or False
            record.bpe10_nro = company.street_number or "SN"
            record.bpe10_xCpl = company.street2 or False
            record.bpe10_xBairro = company.district or False
            record.bpe10_cMun = company.city_id.ibge_code or False
            record.bpe10_xMun = company.city_id.name or False
            record.bpe10_CEP = punctuation_rm(company.zip or "") or False
            record.bpe10_UF = company.state_id.code or False
            record.bpe10_fone = _phone(company.phone)
            record.bpe10_email = company.email or False

    ##########################
    # BP-e tag: infPassagem
    ##########################

    bpe10_cLocOrig = fields.Char(
        compute="_compute_bpe10_locations", store=True, readonly=False
    )
    bpe10_xLocOrig = fields.Char(
        compute="_compute_bpe10_locations", store=True, readonly=False
    )
    bpe10_cLocDest = fields.Char(
        compute="_compute_bpe10_locations", store=True, readonly=False
    )
    bpe10_xLocDest = fields.Char(
        compute="_compute_bpe10_locations", store=True, readonly=False
    )

    @api.depends("bpe_origin_city_id", "bpe_destination_city_id")
    def _compute_bpe10_locations(self):
        """Origin and destination default to the cities; a terminal code
        can be informed instead (MOC BP-e, infPassagem)."""
        for record in self:
            record.bpe10_cLocOrig = record.bpe_origin_city_id.ibge_code or False
            record.bpe10_xLocOrig = record.bpe_origin_city_id.name or False
            record.bpe10_cLocDest = record.bpe_destination_city_id.ibge_code or False
            record.bpe10_xLocDest = record.bpe_destination_city_id.name or False

    ##########################
    # BP-e tag: infValorBPe
    ##########################

    bpe10_vBP = fields.Monetary(
        compute="_compute_bpe10_values", currency_field="brl_currency_id"
    )
    bpe10_vDesconto = fields.Monetary(
        compute="_compute_bpe10_values", currency_field="brl_currency_id"
    )
    bpe10_vPgto = fields.Monetary(
        compute="_compute_bpe10_values", currency_field="brl_currency_id"
    )

    @api.depends("fiscal_line_ids.price_gross", "fiscal_line_ids.discount_value")
    def _compute_bpe10_values(self):
        """vPgto = vBP - vDesconto (MOC BP-e 1.00b, rule F68)."""
        for record in self:
            lines = record.fiscal_line_ids
            record.bpe10_vBP = sum(lines.mapped("price_gross"))
            record.bpe10_vDesconto = sum(lines.mapped("discount_value"))
            record.bpe10_vPgto = record.bpe10_vBP - record.bpe10_vDesconto

    def _export_fields_bpe_10_tbpe_infvalorbpe(
        self, xsd_fields, class_obj, export_dict
    ):
        """One Comp per fiscal line: the sum of vComp is vBP (rule F59)."""
        if "bpe10_Comp" in xsd_fields:
            xsd_fields.remove("bpe10_Comp")
        export_dict["comp"] = [
            Tbpe.InfBpe.InfValorBpe.Comp(
                tpComp=line.bpe_component_type, vComp=_money(line.price_gross)
            )
            for line in self.fiscal_line_ids
        ]

    ##########################
    # BP-e tag: imp
    ##########################

    bpe10_vTotTrib = fields.Monetary(
        related="amount_estimate_tax", currency_field="brl_currency_id"
    )

    bpe10_vTotDFe = fields.Monetary(
        compute="_compute_bpe10_vtotdfe", currency_field="brl_currency_id"
    )

    def _get_bpe_reference_date(self):
        """Local issue date, the same day the exported dhEmi shows."""
        self.ensure_one()
        if self.document_date:
            return fields.Datetime.context_timestamp(self, self.document_date).date()
        return fields.Date.context_today(self)

    @api.depends(
        "document_date",
        "fiscal_line_ids.price_gross",
        "fiscal_line_ids.ibs_value",
        "fiscal_line_ids.cbs_value",
    )
    @api.depends_context("tz")
    def _compute_bpe10_vtotdfe(self):
        """NT BP-e 2026.004 v1.01: vTotDFe is vBP in 2026 and, from 2027 on
        (by the issue date), vBP plus IBS and CBS."""
        for record in self:
            lines = record.fiscal_line_ids
            total = sum(lines.mapped("price_gross"))
            if record._get_bpe_reference_date() >= BPE_IBSCBS_IN_TOTAL_DATE:
                total += sum(lines.mapped("ibs_value")) + sum(lines.mapped("cbs_value"))
            record.bpe10_vTotDFe = total

    def _export_fields_bpe_10_timp(self, xsd_fields, class_obj, export_dict):
        """ICMS group of the ticket, from the ICMS of the fiscal lines."""
        lines = self.fiscal_line_ids
        if self.company_id.tax_framework == "1":
            export_dict["ICMSSN"] = Timp.Icmssn(CST="90", indSN="1")
            return
        cst = lines[:1].icms_cst_id.code
        group = ICMS_GROUP_BY_CST.get(cst)
        if not group:
            raise UserError(
                _("ICMS CST %(cst)s is not supported in the BP-e.", cst=cst)
            )
        base = sum(lines.mapped("icms_base"))
        value = sum(lines.mapped("icms_value"))
        percent = lines[:1].icms_percent
        reduction = lines[:1].icms_reduction
        binding = getattr(Timp, group.replace("ICMS", "Icms"))
        if group == "ICMS00":
            vals = {
                "vBC": _money(base),
                "pICMS": f"{percent:.2f}",
                "vICMS": _money(value),
            }
        elif group == "ICMS20":
            vals = {
                "pRedBC": f"{reduction:.2f}",
                "vBC": _money(base),
                "pICMS": f"{percent:.2f}",
                "vICMS": _money(value),
            }
        elif group == "ICMS90":
            vals = {
                "vBC": _money(base),
                "pICMS": f"{percent:.2f}",
                "vICMS": _money(value),
            }
            if reduction:
                vals["pRedBC"] = f"{reduction:.2f}"
        else:
            vals = {}
        export_dict[group] = binding(CST=cst, **vals)

    ##########################
    # BP-e tag: IBSCBS (NT BP-e 2025.001 RTC)
    ##########################

    def _get_bpe_ibscbs_lines(self):
        return self.fiscal_line_ids.filtered(
            lambda line: line.tax_classification_id
            and (line.ibs_tax_id or line.cbs_tax_id)
        )

    def _export_tag_bpe_10_ibscbs(self, xsd_fields, class_obj, export_dict):
        lines = self._get_bpe_ibscbs_lines()
        if not lines:
            return
        line = lines[:1]
        export_dict["CST"] = (line.ibs_cst_id or line.cbs_cst_id).code
        export_dict["cClassTrib"] = line.tax_classification_id.code
        for tag in ("bpe10_gEstornoCred",):
            if tag in xsd_fields:
                xsd_fields.remove(tag)

    def _export_tag_bpe_10_gibscbs(self, xsd_fields, class_obj, export_dict):
        lines = self._get_bpe_ibscbs_lines()
        if not lines:
            return
        export_dict["vBC"] = _money(
            sum(line.ibs_base or line.cbs_base for line in lines)
        )
        export_dict["vIBS"] = _money(sum(lines.mapped("ibs_value")))

    def _export_tag_bpe_10_gibsuf(self, xsd_fields, class_obj, export_dict):
        lines = self._get_bpe_ibscbs_lines()
        export_dict["pIBSUF"] = _rate(lines[:1].ibs_percent)
        export_dict["vIBSUF"] = _money(sum(lines.mapped("ibs_value")))

    def _export_tag_bpe_10_gibsuf_gred(self, xsd_fields, class_obj, export_dict):
        line = self._get_bpe_ibscbs_lines()[:1]
        if line.ibs_reduction:
            export_dict["pRedAliq"] = _rate(line.ibs_reduction)
            export_dict["pAliqEfet"] = _rate(
                line.ibs_percent * (1 - line.ibs_reduction / 100)
            )

    def _export_tag_bpe_10_gibsmun(self, xsd_fields, class_obj, export_dict):
        # the municipal IBS rate is zero in 2026 and 2027 (LC 214/2025)
        export_dict["pIBSMun"] = _rate(0.0)
        export_dict["vIBSMun"] = _money(0.0)

    def _export_tag_bpe_10_gcbs(self, xsd_fields, class_obj, export_dict):
        lines = self._get_bpe_ibscbs_lines()
        export_dict["pCBS"] = _rate(lines[:1].cbs_percent)
        export_dict["vCBS"] = _money(sum(lines.mapped("cbs_value")))

    def _export_tag_bpe_10_gcbs_gred(self, xsd_fields, class_obj, export_dict):
        line = self._get_bpe_ibscbs_lines()[:1]
        if line.cbs_reduction:
            export_dict["pRedAliq"] = _rate(line.cbs_reduction)
            export_dict["pAliqEfet"] = _rate(
                line.cbs_percent * (1 - line.cbs_reduction / 100)
            )

    ##########################
    # BP-e tag: comp (buyer), infAdic and infRespTec
    ##########################

    def _export_tag_bpe_10_comp(self, xsd_fields, class_obj, export_dict):
        partner = self.partner_id
        if not partner:
            return
        export_dict["xNome"] = partner.legal_name or partner.name
        vat = punctuation_rm(partner.vat or "")
        if partner.is_company and vat:
            export_dict["CNPJ"] = vat
            if partner.l10n_br_ie_code:
                export_dict["IE"] = punctuation_rm(partner.l10n_br_ie_code)
        elif vat:
            export_dict["CPF"] = vat
        else:
            export_dict["idEstrangeiro"] = ""

    def _export_tag_bpe_10_endercomp(self, xsd_fields, class_obj, export_dict):
        partner = self.partner_id
        if not partner:
            return
        export_dict.update(
            {
                "xLgr": partner.street_name or partner.street,
                "nro": partner.street_number or "SN",
                "xCpl": partner.street2 or None,
                "xBairro": partner.district,
                "cMun": partner.city_id.ibge_code,
                "xMun": partner.city_id.name,
                "CEP": punctuation_rm(partner.zip or "") or None,
                "UF": partner.state_id.code,
            }
        )

    def _export_tag_bpe_10_infadic(self, xsd_fields, class_obj, export_dict):
        if self.fiscal_additional_data:
            export_dict["infAdFisco"] = _clean_text(self.fiscal_additional_data)
        if self.customer_additional_data:
            export_dict["infCpl"] = _clean_text(self.customer_additional_data)

    def _export_tag_bpe_10_infresptec(self, xsd_fields, class_obj, export_dict):
        tech = self.company_id.technical_support_id
        if not (tech and tech.vat and tech.email and tech.phone):
            return
        export_dict.update(
            {
                "CNPJ": punctuation_rm(tech.vat),
                "xContato": tech.name,
                "email": tech.email,
                "fone": _phone(tech.phone),
            }
        )

    ################################
    # Business Model Methods
    ################################

    def _get_bpe_qrcode(self):
        """QR Code of the DABPE (MOC BP-e 1.00b, item 10.2)."""
        self.ensure_one()
        if self.bpe10_tpEmis != "1":
            raise UserError(
                _("The QR Code of a BP-e issued in contingency is not supported yet.")
            )
        url = get_location(
            self.company_id.state_id.ibge_code, self.bpe_environment, Endpoint.QRCODE
        )
        return f"{url}?chBPe={self.document_key}&tpAmb={self.bpe_environment}"

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filtered_processador_edoc_bpe):
            inf_bpe = record._build_binding("bpe", "10")
            edocs.append(
                Bpe(
                    infBPe=inf_bpe,
                    infBPeSupl=Tbpe.InfBpeSupl(qrCodBPe=record._get_bpe_qrcode()),
                )
            )
        return edocs

    def _get_bpe_certificate(self):
        """PKCS#12 data (the base64 value of the Binary field, as nfelib and
        brazil_fiscal_client take it) and password of the company certificate.
        The certificate compute raises when the company has none."""
        certificate = self.company_id.sudo().certificate
        return (
            certificate.with_context(bin_size=False).file,
            certificate.password,
        )

    def _bpe_sign(self, binding, doc_id):
        pkcs12_data, pkcs12_password = self._get_bpe_certificate()
        return binding.to_xml(
            pkcs12_data=pkcs12_data,
            pkcs12_password=pkcs12_password,
            doc_id=doc_id,
        )

    def _bpe_event_environment(self):
        return EVENT_ENV_PROD if self.bpe_environment == "1" else EVENT_ENV_HML

    def _document_export(self, pretty_print=True):
        result = super()._document_export()
        for record in self.filtered(filtered_processador_edoc_bpe):
            edoc = record.serialize()[0]
            signed_xml = record._bpe_sign(edoc, edoc.infBPe.Id)
            if (
                record.authorization_event_id
                and record.authorization_event_id.state == "draft"
            ):
                record.sudo().authorization_event_id.unlink()
            record.authorization_event_id = record.event_ids.create_event_save_xml(
                company_id=record.company_id,
                environment=record._bpe_event_environment(),
                event_type="0",
                xml_file=signed_xml,
                document_id=record,
            )
            record._validate_xml(signed_xml)
        return result

    def _validate_xml(self, xml_file):
        self.ensure_one()
        if not filtered_processador_edoc_bpe(self):
            return super()._validate_xml(xml_file)
        errors = Bpe.schema_validation(xml_file)
        self.write({"xml_error_message": "\n".join(errors) or False})

    def _get_bpe_client(self):
        self.ensure_one()
        pkcs12_data, pkcs12_password = self._get_bpe_certificate()
        return BpeClient(
            ambiente=self.bpe_environment,
            uf=self.company_id.state_id.ibge_code,
            pkcs12_data=pkcs12_data,
            pkcs12_password=pkcs12_password,
        )

    def _eletronic_document_send(self):
        bpe_documents = self.filtered(filtered_processador_edoc_bpe)
        result = super(BPe, self - bpe_documents)._eletronic_document_send()
        for record in bpe_documents:
            if record.xml_error_message:
                continue
            signed_xml = base64.b64decode(
                record.authorization_event_id.file_request_id.datas
            ).decode("utf-8")
            response = record._get_bpe_client().envia_bpe(signed_xml)
            record._bpe_process_response(response, signed_xml)
        return result

    def _bpe_process_response(self, response, signed_xml):
        """Authorization answer of the synchronous BPeRecepcao (MOC item 4.1)."""
        self.ensure_one()
        status = response.cStat
        reason = response.xMotivo
        inf_prot = response.protBPe and response.protBPe.infProt
        if inf_prot:
            status = inf_prot.cStat
            reason = inf_prot.xMotivo
        self.write({"status_code": status, "status_name": reason})
        if status in BPE_AUTHORIZED and inf_prot:
            self.authorization_event_id.set_done(
                status_code=status,
                response=reason,
                protocol_date=tax_authority_date_to_utc(inf_prot.dhRecbto),
                protocol_number=inf_prot.nProt,
                file_response_xml=self._bpe_proc_xml(signed_xml, response),
            )
            self._change_state(SITUACAO_EDOC_AUTORIZADA)
        else:
            self._change_state(SITUACAO_EDOC_REJEITADA)

    def _bpe_proc_xml(self, signed_xml, response):
        """bpeProc: the signed BP-e with the authorization protocol."""
        prot_xml = response.protBPe.to_xml(ns_map={None: Bpe.Meta.namespace})
        prot_xml = re.sub(r"^\s*<\?xml[^>]*\?>", "", prot_xml).strip()
        bpe_xml = re.sub(r"^\s*<\?xml[^>]*\?>", "", signed_xml).strip()
        return (
            f'<bpeProc xmlns="{Bpe.Meta.namespace}" versao="{BPE_VERSION}">'
            f"{bpe_xml}{prot_xml}</bpeProc>"
        )

    ################################
    # Events (MOC BP-e 1.00b, items 6 and 7)
    ################################

    def _bpe_build_event(self, event_type, detail, sequence=1):
        self.ensure_one()
        if not self.authorization_protocol:
            raise UserError(_("Authorization Protocol Not Found!"))
        now = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        return EventoBpe(
            versao=BPE_VERSION,
            infEvento=EventoBpe.InfEvento(
                Id=f"ID{event_type}{self.document_key}{sequence:02d}",
                cOrgao=TcorgaoIbge(self.company_id.state_id.ibge_code),
                tpAmb=Tamb(self.bpe_environment),
                CNPJ=punctuation_rm(self.company_id.vat),
                chBPe=self.document_key,
                dhEvento=now.replace(microsecond=0).isoformat("T"),
                tpEvento=event_type,
                nSeqEvento=str(sequence),
                detEvento=EventoBpe.InfEvento.DetEvento(
                    versaoEvento=BPE_VERSION, any_element=detail
                ),
            ),
        )

    def _bpe_send_event(self, event_type, detail, odoo_event_type, justification):
        """Sign, validate and send an event; return the Odoo event and the
        answer. A refusal is returned, not raised, so the event is kept."""
        self.ensure_one()
        evento = self._bpe_build_event(event_type, detail)
        signed_xml = self._bpe_sign(evento, evento.infEvento.Id)
        errors = EventoBpe.schema_validation(
            signed_xml, schema_path=BPE_SCHEMAS["evento"]
        )
        if errors:
            raise ValidationError("\n".join(errors))
        event = self.event_ids.create_event_save_xml(
            company_id=self.company_id,
            environment=self._bpe_event_environment(),
            event_type=odoo_event_type,
            xml_file=signed_xml,
            document_id=self,
            sequence="1",
            justification=justification,
        )
        response = self._get_bpe_client().envia_evento(signed_xml).infEvento
        event.write({"status_code": response.cStat, "response": response.xMotivo})
        if response.cStat in BPE_EVENT_REGISTERED:
            event.set_done(
                status_code=response.cStat,
                response=response.xMotivo,
                protocol_date=tax_authority_date_to_utc(response.dhRegEvento),
                protocol_number=response.nProt,
                file_response_xml=False,
            )
        return event, response

    def _document_cancel(self, justificative=None):
        bpe_documents = self.filtered(filtered_processador_edoc_bpe)
        result = None
        if self - bpe_documents:
            result = super(BPe, self - bpe_documents)._document_cancel(justificative)
        for record in bpe_documents:
            record.cancel_reason = justificative
            detail = EvCancBpe(
                descEvento=EvCancBpeDescEvento.CANCELAMENTO,
                nProt=record.authorization_protocol,
                xJust=_clean_text(justificative or ""),
            )
            event, response = record._bpe_send_event(
                BPE_CANCEL_EVENT, detail, "2", justificative
            )
            record.cancel_event_id = event
            if response.cStat not in BPE_EVENT_REGISTERED:
                record.message_post(
                    body=_(
                        "BP-e cancellation refused: %(code)s - %(reason)s",
                        code=response.cStat,
                        reason=response.xMotivo,
                    )
                )
                continue
            record.state_fiscal = SITUACAO_FISCAL_CANCELADO
            super(BPe, record)._document_cancel(justificative)
        return result

    def _bpe_no_boarding(self, justification):
        """Evento de Nao Embarque (110115, MOC BP-e 1.00b, item 7.2)."""
        self.ensure_one()
        detail = EvNaoEmbBpe(
            descEvento=EvNaoEmbBpeDescEvento.N_O_EMBARQUE,
            nProt=self.authorization_protocol,
            xJust=_clean_text(justification),
        )
        event, response = self._bpe_send_event(
            BPE_NO_BOARDING_EVENT, detail, "9", justification
        )
        if response.cStat not in BPE_EVENT_REGISTERED:
            self.message_post(
                body=_(
                    "BP-e no boarding event refused: %(code)s - %(reason)s",
                    code=response.cStat,
                    reason=response.xMotivo,
                )
            )
        return event

    ################################
    # Key, number and checks
    ################################

    def _generate_key(self):
        bpe_documents = self.filtered(
            lambda doc: doc.document_type_id.code == MODELO_FISCAL_BPE
        )
        result = None
        if self - bpe_documents:
            result = super(BPe, self - bpe_documents)._generate_key()
        for record in bpe_documents:
            if not (record.company_id.vat and record.company_id.state_id):
                raise ValidationError(
                    _(
                        "To generate the BP-e key, fill the CNPJ and the State "
                        "of the company %s.",
                        record.company_id.display_name,
                    )
                )
            date = fields.Datetime.context_timestamp(record, record.document_date)
            chave_edoc = ChaveEdoc(
                ano_mes=date.strftime("%y%m").zfill(4),
                cnpj_cpf_emitente=punctuation_rm(record.company_id.vat),
                codigo_uf=record.company_id.state_id.ibge_code,
                forma_emissao=int(record.bpe10_tpEmis or 1),
                modelo_documento=MODELO_FISCAL_BPE,
                numero_documento=record.document_number,
                numero_serie=record.document_serie,
                validar=False,
            )
            record.key_random_code = chave_edoc.codigo_aleatorio
            record.key_check_digit = chave_edoc.digito_verificador
            record.document_key = chave_edoc.chave
        return result

    def _document_number(self):
        if (
            self.document_type_id.code == MODELO_FISCAL_BPE
            and self.issuer == DOCUMENT_ISSUER_COMPANY
            and not self.document_serie_id
        ):
            serie = self.document_type_id.get_document_serie(
                self.company_id, self.fiscal_operation_id
            )
            if serie:
                self.document_serie_id = serie
        return super()._document_number()

    def _document_check(self):
        result = super()._document_check()
        for record in self.filtered(filtered_processador_edoc_bpe):
            record._check_bpe_required_fields()
        return result

    def _check_bpe_required_fields(self):
        self.ensure_one()
        checks = [
            (self.company_id.vat, _("Company CNPJ")),
            (self.company_id.state_id, _("Company State")),
            (
                self.company_id.sudo().certificate_nfe_id
                or self.company_id.sudo().certificate_ecnpj_id,
                _("Digital Certificate"),
            ),
            (self.bpe_environment, _("BP-e Environment")),
            (self.bpe10_cLocOrig and self.bpe_origin_city_id, _("Origin City")),
            (
                self.bpe10_cLocDest and self.bpe_destination_city_id,
                _("Destination City"),
            ),
            (self.bpe10_dhEmb, _("Boarding Date")),
            (self.bpe10_dhValidade, _("Ticket Validity Date")),
            (self.bpe10_infViagem, _("Trip Information")),
            (self.bpe10_pag, _("Payment Information")),
            (self.fiscal_line_ids, _("Value Components (fiscal lines)")),
        ]
        missing = [label for value, label in checks if not value]
        # MOC BP-e 1.00b, rejection 211: the passenger is identified in the
        # interstate transport
        if self.bpe10_UFIni != self.bpe10_UFFim and not self.bpe10_infPassageiro:
            missing.append(_("Passenger (interstate trip)"))
        if missing:
            raise UserError(
                _("Fill in the required BP-e fields:\n- %s") % "\n- ".join(missing)
            )
