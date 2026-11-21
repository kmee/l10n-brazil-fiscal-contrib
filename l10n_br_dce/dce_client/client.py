# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Client of the DC-e 1.00 webservices, on top of brazil_fiscal_client.

Follows the CT-e and MDF-e clients of nfelib (nfelib/<doc>/client), which has
no DC-e yet. Per the MOC DC-e, Visão Geral (items 4.2.2 and 5): SOAP 1.2,
document/literal, the request in dceDadosMsg, no SOAP header, synchronous
services. The DCeAutorizacao message is sent without compression: the
compressed method (dceAutorizacaoZip) is optional for the authorizer.
"""

import re

from brazil_fiscal_client.fiscal_client import FiscalClient

from odoo.addons.l10n_br_dce_spec.bindings.v1_0.cons_sit_dce_v1_00 import ConsSitDce
from odoo.addons.l10n_br_dce_spec.bindings.v1_0.cons_stat_serv_dce_v1_00 import (
    ConsStatServDce,
)
from odoo.addons.l10n_br_dce_spec.bindings.v1_0.dce_v1_00 import Dce
from odoo.addons.l10n_br_dce_spec.bindings.v1_0.evento_dce_v1_00 import EventoDce
from odoo.addons.l10n_br_dce_spec.bindings.v1_0.ret_cons_sit_dce_v1_00 import (
    RetConsSitDce,
)
from odoo.addons.l10n_br_dce_spec.bindings.v1_0.ret_cons_stat_serv_dce_v1_00 import (
    RetConsStatServDce,
)
from odoo.addons.l10n_br_dce_spec.bindings.v1_0.ret_dce_v1_00 import RetDce
from odoo.addons.l10n_br_dce_spec.bindings.v1_0.ret_evento_dce_v1_00 import (
    RetEventoDce,
)

from ..constants import DCE_VERSION
from . import soap
from .servers import Endpoint, get_location

ENDPOINTS = {
    soap.DceAutorizacao: Endpoint.AUTORIZACAO,
    soap.DceRecepcaoEvento: Endpoint.RECEPCAO_EVENTO,
    soap.DceConsulta: Endpoint.CONSULTA,
    soap.DceStatusServico: Endpoint.STATUS_SERVICO,
}

RESULTS = {
    soap.DceAutorizacao: RetDce,
    soap.DceRecepcaoEvento: RetEventoDce,
    soap.DceConsulta: RetConsSitDce,
    soap.DceStatusServico: RetConsStatServDce,
}

XML_DECLARATION = re.compile(r"^\s*<\?xml[^>]*\?>")


class DceClient(FiscalClient):
    """A facade for the DC-e 1.00 SOAP webservices."""

    def __init__(self, **kwargs):
        kwargs.setdefault("soap12_envelope", True)
        super().__init__(service="dce", versao=DCE_VERSION, **kwargs)

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
            {"Body": {"dceDadosMsg": dados_msg}},
            **kwargs,
        )
        if self.wrap_response:
            response.resposta = self._result(action_class, response.resposta)
            return response
        return self._result(action_class, response)

    def _result(self, action_class, envelope):
        body = envelope.body
        message = getattr(body, action_class.result, None) or getattr(
            body, soap.RESULT_MSG, None
        )
        if body.fault is not None or message is None or not message.content:
            raise ValueError(
                f"SOAP fault from {action_class.__name__}: "
                f"{body.fault and body.fault.faultstring}"
            )
        result = message.content[0]
        expected = RESULTS[action_class]
        if not isinstance(result, expected):
            raise ValueError(
                f"Unexpected answer from {action_class.__name__}: {result!r}"
            )
        return result

    def _send_signed(self, action_class, root_tag, signed_xml):
        """Send a signed document as is, so the signature is not touched."""
        if not signed_xml:
            raise ValueError(f"The signed {root_tag} XML is empty.")
        placeholder = {"DCe": Dce(), "eventoDCe": EventoDce(versao=DCE_VERSION)}
        return self.send(
            action_class,
            {"content": [placeholder[root_tag]]},
            placeholder_exp=rf"<{root_tag}[^>]*/>|<{root_tag}[ >].*?</{root_tag}>",
            placeholder_content=XML_DECLARATION.sub("", signed_xml),
        )

    ######################################
    # Webservices
    ######################################

    def status_servico(self):
        """Consulta Status do Servico (MOC DC-e, Visão Geral, item 5.3)."""
        payload = ConsStatServDce(tpAmb=self.ambiente, cUF=self.uf, versao=DCE_VERSION)
        return self.send(soap.DceStatusServico, {"content": [payload]})

    def consulta_dce(self, chave):
        """Consulta Situacao da DC-e (MOC DC-e, Visão Geral, item 5.2)."""
        if not (isinstance(chave, str) and len(chave) == 44):
            raise ValueError(f"Invalid DC-e access key: {chave}")
        payload = ConsSitDce(tpAmb=self.ambiente, chDCe=chave, versao=DCE_VERSION)
        return self.send(soap.DceConsulta, {"content": [payload]})

    def envia_dce(self, signed_xml):
        """Autorizacao da DC-e (MOC DC-e, Visão Geral, item 5.1): synchronous."""
        return self._send_signed(soap.DceAutorizacao, "DCe", signed_xml)

    def envia_evento(self, signed_xml):
        """Recepcao de Evento (MOC DC-e, Visão Geral, item 5.4)."""
        return self._send_signed(soap.DceRecepcaoEvento, "eventoDCe", signed_xml)
