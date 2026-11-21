# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""SOAP bindings of the BP-e webservices (MOC BP-e 1.00b, items 3.3 and 3.4).

Same shape as the classes xsdata generates from the WSDL for the other
documents in nfelib (nfelib/mdfe/soap): the WSDL of the BP-e is only served
to a client certificate, so these few classes are declared here.
"""

from dataclasses import field, make_dataclass

SOAP_ENV_NS = "http://schemas.xmlsoap.org/soap/envelope/"
WSDL_NS = "http://www.portalfiscal.inf.br/bpe/wsdl/%s"

WILDCARD = {"type": "Wildcard", "namespace": "##any", "mixed": True}


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


def _soap_action(service, method, compressed=False):
    namespace = WSDL_NS % service
    if compressed:
        # BPeRecepcao: the BP-e goes gzipped and base64 encoded as text
        dados_field = ("value", str, field(default="", metadata={"required": True}))
    else:
        dados_field = (
            "content",
            list[object],
            field(default_factory=list, metadata=WILDCARD),
        )
    dados_msg = make_dataclass(
        "BpeDadosMsg", [dados_field], namespace=_meta("bpeDadosMsg", namespace)
    )
    result_msg = make_dataclass(
        "BpeResultMsg",
        [("content", list[object], field(default_factory=list, metadata=WILDCARD))],
        namespace=_meta("bpeResultMsg", namespace),
    )
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
    element = {"type": "Element", "namespace": namespace}
    soap_input = _envelope(
        service,
        "Input",
        [("bpeDadosMsg", dados_msg | None, field(default=None, metadata=element))],
    )
    soap_output = _envelope(
        service,
        "Output",
        [
            (
                "bpeResultMsg",
                result_msg | None,
                field(default=None, metadata=element),
            ),
            (
                "fault",
                fault | None,
                field(default=None, metadata={"name": "Fault", "type": "Element"}),
            ),
        ],
    )
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
            "input": soap_input,
            "output": soap_output,
        },
    )


BpeRecepcao = _soap_action("BPeRecepcao", "bpeRecepcao", compressed=True)
BpeRecepcaoEvento = _soap_action("BPeRecepcaoEvento", "bpeRecepcaoEvento")
BpeConsulta = _soap_action("BPeConsulta", "bpeConsultaBP")
BpeStatusServico = _soap_action("BPeStatusServico", "bpeStatusServicoBP")
