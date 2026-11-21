# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""SOAP bindings of the DC-e webservices (MOC DC-e, Visão Geral, item 4.2.2).

Same shape as the classes xsdata generates from the WSDL for the other
documents in nfelib (nfelib/mdfe/soap): the WSDL of the DC-e is only served
to a client certificate, so these few classes are declared here. The request
goes in dceDadosMsg; the answer element is named after the WSDL operation
(dceAutorizacaoResult, for instance), and dceResultMsg is accepted as well.
"""

from dataclasses import field, make_dataclass

SOAP_ENV_NS = "http://schemas.xmlsoap.org/soap/envelope/"
WSDL_NS = "http://www.portalfiscal.inf.br/dce/wsdl/%s"

WILDCARD = {"type": "Wildcard", "namespace": "##any", "mixed": True}

RESULT_MSG = "dceResultMsg"


def _meta(name, namespace):
    return {"Meta": type("Meta", (), {"name": name, "namespace": namespace})}


def _envelope(service, direction, body_fields):
    body = make_dataclass(f"{service}{direction}Body", body_fields)
    return make_dataclass(
        f"{service}{direction}",
        [
            (
                "body",
                body | None,
                field(default=None, metadata={"name": "Body", "type": "Element"}),
            )
        ],
        namespace=_meta("Envelope", SOAP_ENV_NS),
    )


def _wildcard_message(name, namespace):
    return make_dataclass(
        name,
        [("content", list[object], field(default_factory=list, metadata=WILDCARD))],
        namespace=_meta(name, namespace),
    )


def _soap_action(service, method, result):
    namespace = WSDL_NS % service
    element = {"type": "Element", "namespace": namespace}
    dados_msg = _wildcard_message("dceDadosMsg", namespace)
    fault = make_dataclass(
        "Fault",
        [
            (
                name,
                str | None,
                field(default=None, metadata={"type": "Element", "namespace": ""}),
            )
            for name in ("faultcode", "faultstring", "faultactor", "detail")
        ],
    )
    soap_input = _envelope(
        service,
        "Input",
        [("dceDadosMsg", dados_msg | None, field(default=None, metadata=element))],
    )
    output_fields = [
        (
            result_name,
            _wildcard_message(result_name, namespace) | None,
            field(default=None, metadata=element),
        )
        for result_name in dict.fromkeys((result, RESULT_MSG))
    ]
    output_fields.append(
        (
            "fault",
            fault | None,
            field(default=None, metadata={"name": "Fault", "type": "Element"}),
        )
    )
    soap_output = _envelope(service, "Output", output_fields)
    soap_action = f"{namespace}/{method}"
    return type(
        service,
        (),
        {
            "style": "document",
            "location": "",
            "transport": "http://schemas.xmlsoap.org/soap/http",
            "soap_action": soap_action,
            # name read by brazil_fiscal_client to label the response
            "soapAction": soap_action,
            "result": result,
            "input": soap_input,
            "output": soap_output,
        },
    )


DceAutorizacao = _soap_action(
    "DCeAutorizacao", "dceAutorizacao", "dceAutorizacaoResult"
)
DceRecepcaoEvento = _soap_action(
    "DCeRecepcaoEvento", "dceRecepcaoEvento", "dceRecepcaoEventoResult"
)
DceConsulta = _soap_action("DCeConsulta", "dceConsulta", RESULT_MSG)
DceStatusServico = _soap_action(
    "DCeStatusServico", "dceStatusServico", "dceStatusServicoResult"
)
