# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Client of the BP-e 1.00 webservices, on top of brazil_fiscal_client.

Follows the CT-e and MDF-e clients of nfelib (nfelib/<doc>/client), which have
no BP-e counterpart yet. Per the MOC BP-e 1.00b (item 3.3): SOAP 1.2, the
request in bpeDadosMsg, the answer in bpeResultMsg, no SOAP header, and only
the BPeRecepcao message gzipped and base64 encoded (item 3.4).
"""

import base64
import gzip
import logging
import re

from brazil_fiscal_client.fiscal_client import FiscalClient
from nfelib.bpe.bindings.v1_0.cons_sit_bpe_v1_00 import ConsSitBpe
from nfelib.bpe.bindings.v1_0.cons_stat_serv_bpe_v1_00 import ConsStatServBpe
from nfelib.bpe.bindings.v1_0.evento_bpe_v1_00 import EventoBpe
from nfelib.bpe.bindings.v1_0.ret_bpe_v1_00 import RetBpe
from nfelib.bpe.bindings.v1_0.ret_cons_sit_bpe_v1_00 import RetConsSitBpe
from nfelib.bpe.bindings.v1_0.ret_cons_stat_serv_bpe_v1_00 import RetConsStatServBpe
from nfelib.bpe.bindings.v1_0.ret_evento_bpe_v1_00 import RetEventoBpe
from nfelib.bpe.bindings.v1_0.tipos_geral_bpe_v1_00 import Tamb as BpeTamb

from . import soap
from .servers import Endpoint, get_location

_logger = logging.getLogger(__name__)

BPE_VERSION = "1.00"

ENDPOINTS = {
    soap.BpeRecepcao: Endpoint.RECEPCAO,
    soap.BpeRecepcaoEvento: Endpoint.RECEPCAO_EVENTO,
    soap.BpeConsulta: Endpoint.CONSULTA,
    soap.BpeStatusServico: Endpoint.STATUS_SERVICO,
}

RESULTS = {
    soap.BpeRecepcao: RetBpe,
    soap.BpeRecepcaoEvento: RetEventoBpe,
    soap.BpeConsulta: RetConsSitBpe,
    soap.BpeStatusServico: RetConsStatServBpe,
}

XML_DECLARATION = re.compile(r"^\s*<\?xml[^>]*\?>")


class BpeClient(FiscalClient):
    """A facade for the BP-e 1.00 SOAP webservices."""

    def __init__(self, **kwargs):
        kwargs.setdefault("soap12_envelope", True)
        super().__init__(service="bpe", versao=BPE_VERSION, **kwargs)

    def _get_location(self, endpoint):
        return get_location(self.uf, self.ambiente, endpoint)

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
            self._get_location(ENDPOINTS[action_class]),
            {"Body": {"bpeDadosMsg": dados_msg}},
            **kwargs,
        )
        if self.wrap_response:
            response.resposta = self._result(action_class, response.resposta)
            return response
        return self._result(action_class, response)

    def _result(self, action_class, envelope):
        body = envelope.body
        if body.fault is not None or body.bpeResultMsg is None:
            raise ValueError(
                f"SOAP fault from {action_class.__name__}: "
                f"{body.fault and body.fault.faultstring}"
            )
        result = body.bpeResultMsg.content[0]
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
        """Consulta Status do Servico (MOC item 4.3)."""
        payload = ConsStatServBpe(tpAmb=BpeTamb(self.ambiente), versao=BPE_VERSION)
        return self.send(soap.BpeStatusServico, {"content": [payload]})

    def consulta_bpe(self, chave):
        """Consulta Situacao do BP-e (MOC item 4.2)."""
        if not (isinstance(chave, str) and len(chave) == 44):
            raise ValueError(f"Invalid BP-e access key: {chave}")
        payload = ConsSitBpe(
            tpAmb=BpeTamb(self.ambiente), chBPe=chave, versao=BPE_VERSION
        )
        return self.send(soap.BpeConsulta, {"content": [payload]})

    def envia_bpe(self, signed_xml):
        """Recepcao do BP-e (MOC item 4.1): synchronous, gzip + base64."""
        if not signed_xml:
            raise ValueError("The signed BP-e XML is empty.")
        xml = XML_DECLARATION.sub("", signed_xml)
        value = base64.b64encode(gzip.compress(xml.encode("utf-8"))).decode()
        return self.send(soap.BpeRecepcao, {"value": value})

    def envia_evento(self, signed_xml):
        """Recepcao de Evento (MOC item 6), with the signed eventoBPe as is."""
        if not signed_xml:
            raise ValueError("The signed event XML is empty.")
        return self.send(
            soap.BpeRecepcaoEvento,
            {"content": [EventoBpe(versao=BPE_VERSION)]},
            placeholder_exp=r"<eventoBPe[^>]*/>|<eventoBPe.*?>.*?</eventoBPe>",
            placeholder_content=XML_DECLARATION.sub("", signed_xml),
        )
