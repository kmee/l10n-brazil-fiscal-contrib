# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Client of the NFAg 1.00 webservices, on top of brazil_fiscal_client.

Follows the BP-e client of l10n_br_bpe and the CT-e and MDF-e clients of
nfelib. Per the MOC NFAg 1.00l (Visão Geral, item 3): SOAP 1.2, the request
in nfagDadosMsg, the answer in nfagResultMsg, no SOAP header, and only the
NFAgRecepcao message gzipped and base64 encoded.
"""

import base64
import gzip
import re

from brazil_fiscal_client.fiscal_client import FiscalClient

from odoo.addons.l10n_br_nfag_spec.bindings.v1_0 import (
    ConsSitNfag,
    ConsStatServNfag,
    EventoNfag,
    RetConsSitNfag,
    RetConsStatServNfag,
    RetEventoNfag,
    RetNfag,
    Tamb,
)

from . import soap
from .servers import Endpoint, get_location

NFAG_VERSION = "1.00"

ENDPOINTS = {
    soap.NfagRecepcao: Endpoint.RECEPCAO,
    soap.NfagRecepcaoEvento: Endpoint.RECEPCAO_EVENTO,
    soap.NfagConsulta: Endpoint.CONSULTA,
    soap.NfagStatusServico: Endpoint.STATUS_SERVICO,
}

RESULTS = {
    soap.NfagRecepcao: RetNfag,
    soap.NfagRecepcaoEvento: RetEventoNfag,
    soap.NfagConsulta: RetConsSitNfag,
    soap.NfagStatusServico: RetConsStatServNfag,
}

XML_DECLARATION = re.compile(r"^\s*<\?xml[^>]*\?>")


class NfagClient(FiscalClient):
    """A facade for the NFAg 1.00 SOAP webservices."""

    def __init__(self, **kwargs):
        kwargs.setdefault("soap12_envelope", True)
        super().__init__(service="nfag", versao=NFAG_VERSION, **kwargs)

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
            {"Body": {"nfagDadosMsg": dados_msg}},
            **kwargs,
        )
        if self.wrap_response:
            response.resposta = self._result(action_class, response.resposta)
            return response
        return self._result(action_class, response)

    def _result(self, action_class, envelope):
        body = envelope.body
        if body.fault is not None or body.nfagResultMsg is None:
            raise ValueError(
                f"SOAP fault from {action_class.__name__}: "
                f"{body.fault and body.fault.faultstring}"
            )
        result = body.nfagResultMsg.content[0]
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
        """Service status query (Consulta Status do Serviço)."""
        payload = ConsStatServNfag(tpAmb=Tamb(self.ambiente), versao=NFAG_VERSION)
        return self.send(soap.NfagStatusServico, {"content": [payload]})

    def consulta_nfag(self, chave):
        """NFAg situation query (Consulta Situação da NFAg)."""
        if not (isinstance(chave, str) and len(chave) == 44):
            raise ValueError(f"Invalid NFAg access key: {chave}")
        payload = ConsSitNfag(
            tpAmb=Tamb(self.ambiente), chNFAg=chave, versao=NFAG_VERSION
        )
        return self.send(soap.NfagConsulta, {"content": [payload]})

    def envia_nfag(self, signed_xml):
        """NFAg reception (Recepção da NFAg): synchronous, gzip + base64."""
        if not signed_xml:
            raise ValueError("The signed NFAg XML is empty.")
        xml = XML_DECLARATION.sub("", signed_xml)
        value = base64.b64encode(gzip.compress(xml.encode("utf-8"))).decode()
        return self.send(soap.NfagRecepcao, {"value": value})

    def envia_evento(self, signed_xml):
        """Event reception (Recepção de Evento), with the signed eventoNFAg as is."""
        if not signed_xml:
            raise ValueError("The signed event XML is empty.")
        return self.send(
            soap.NfagRecepcaoEvento,
            {"content": [EventoNfag(versao=NFAG_VERSION)]},
            placeholder_exp=r"<eventoNFAg[^>]*/>|<eventoNFAg.*?>.*?</eventoNFAg>",
            placeholder_content=XML_DECLARATION.sub("", signed_xml),
        )
