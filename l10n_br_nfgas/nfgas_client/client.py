# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Client of the NFGas 1.00 webservices, on top of brazil_fiscal_client.

Follows the bpe_client of l10n_br_bpe. Per the MOC NFGas 1.00g (Visão Geral,
items 3 and 4): synchronous services, SOAP 1.2, the request in nfgasDadosMsg,
the answer in nfgasResultMsg, no SOAP header, and only the NFGasRecepcao
message gzipped and base64 encoded.
"""

import base64
import gzip
import re

from brazil_fiscal_client.fiscal_client import FiscalClient

from odoo.addons.l10n_br_nfgas_spec.bindings.v1_0.cons_sit_nfgas_v1_00 import (
    ConsSitNfgas,
)
from odoo.addons.l10n_br_nfgas_spec.bindings.v1_0.cons_stat_serv_nfgas_v1_00 import (
    ConsStatServNfgas,
)
from odoo.addons.l10n_br_nfgas_spec.bindings.v1_0.evento_nfgas_v1_00 import (
    EventoNfgas,
)
from odoo.addons.l10n_br_nfgas_spec.bindings.v1_0.ret_cons_sit_nfgas_v1_00 import (
    RetConsSitNfgas,
)
from odoo.addons.l10n_br_nfgas_spec.bindings.v1_0.ret_cons_stat_serv_nfgas_v1_00 import (  # noqa: E501
    RetConsStatServNfgas,
)
from odoo.addons.l10n_br_nfgas_spec.bindings.v1_0.ret_evento_nfgas_v1_00 import (
    RetEventoNfgas,
)
from odoo.addons.l10n_br_nfgas_spec.bindings.v1_0.ret_nfgas_v1_00 import RetNfgas
from odoo.addons.l10n_br_nfgas_spec.bindings.v1_0.tipos_geral_nfgas_v1_00 import (
    Tamb,
)

from . import soap
from .servers import Endpoint, get_location

NFGAS_VERSION = "1.00"

ENDPOINTS = {
    soap.NfgasRecepcao: Endpoint.RECEPCAO,
    soap.NfgasRecepcaoEvento: Endpoint.RECEPCAO_EVENTO,
    soap.NfgasConsulta: Endpoint.CONSULTA,
    soap.NfgasStatusServico: Endpoint.STATUS_SERVICO,
}

RESULTS = {
    soap.NfgasRecepcao: RetNfgas,
    soap.NfgasRecepcaoEvento: RetEventoNfgas,
    soap.NfgasConsulta: RetConsSitNfgas,
    soap.NfgasStatusServico: RetConsStatServNfgas,
}

XML_DECLARATION = re.compile(r"^\s*<\?xml[^>]*\?>")


class NfgasClient(FiscalClient):
    """A facade for the NFGas 1.00 SOAP webservices."""

    def __init__(self, **kwargs):
        kwargs.setdefault("soap12_envelope", True)
        super().__init__(service="nfgas", versao=NFGAS_VERSION, **kwargs)

    def prepare_headers(self, headers):
        """SOAP 1.2 carries the action in the content type (no SOAPAction)."""
        return {
            **headers,
            "content-type": (
                "application/soap+xml; charset=utf-8; "
                f'action="{self.config.soap_action}"'
            ),
        }

    def send(self, action_class, dados_msg, **kwargs):
        response = super().send(
            action_class,
            get_location(self.ambiente, ENDPOINTS[action_class]),
            {"Body": {"nfgasDadosMsg": dados_msg}},
            **kwargs,
        )
        if self.wrap_response:
            response.resposta = self._result(action_class, response.resposta)
            return response
        return self._result(action_class, response)

    def _result(self, action_class, envelope):
        body = envelope.body
        if body.fault is not None or body.nfgasResultMsg is None:
            raise ValueError(
                f"SOAP fault from {action_class.__name__}: "
                f"{body.fault and body.fault.faultstring}"
            )
        result = body.nfgasResultMsg.content[0]
        expected = RESULTS[action_class]
        if not isinstance(result, expected):
            raise ValueError(
                f"Unexpected answer from {action_class.__name__}: {result!r}"
            )
        return result

    ######################################
    # Webservices
    ######################################

    def status_servico(self):
        """Service status query (MOC NFGas 1.00g, Visão Geral, item 4)."""
        payload = ConsStatServNfgas(tpAmb=Tamb(self.ambiente), versao=NFGAS_VERSION)
        return self.send(soap.NfgasStatusServico, {"content": [payload]})

    def consulta_nfgas(self, chave):
        """NFGas status query (MOC NFGas 1.00g, Visão Geral, item 4)."""
        if not (isinstance(chave, str) and len(chave) == 44):
            raise ValueError(f"Invalid NFGas access key: {chave}")
        payload = ConsSitNfgas(
            tpAmb=Tamb(self.ambiente), chNFGas=chave, versao=NFGAS_VERSION
        )
        return self.send(soap.NfgasConsulta, {"content": [payload]})

    def envia_nfgas(self, signed_xml):
        """NFGas reception: synchronous, gzip + base64."""
        if not signed_xml:
            raise ValueError("The signed NFGas XML is empty.")
        xml = XML_DECLARATION.sub("", signed_xml)
        value = base64.b64encode(gzip.compress(xml.encode("utf-8"))).decode()
        return self.send(soap.NfgasRecepcao, {"value": value})

    def envia_evento(self, signed_xml):
        """Event reception (MOC NFGas 1.00g, Visão Geral, item 5), with the
        signed eventoNFGas as is."""
        if not signed_xml:
            raise ValueError("The signed event XML is empty.")
        return self.send(
            soap.NfgasRecepcaoEvento,
            {"content": [EventoNfgas(versao=NFGAS_VERSION)]},
            placeholder_exp=r"<eventoNFGas[^>]*/>|<eventoNFGas.*?>.*?</eventoNFGas>",
            placeholder_content=XML_DECLARATION.sub("", signed_xml),
        )
