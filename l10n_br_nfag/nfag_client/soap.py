# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""SOAP bindings of the NFAg webservices (MOC NFAg 1.00l, Visão Geral).

Same shape as the classes xsdata generates from the WSDL for the other
documents in nfelib (nfelib/mdfe/soap): the WSDL of the NFAg is only served
to a client certificate, so the namespaces and the methods follow the MOC
(nfagDadosMsg and nfagResultMsg in the namespace
http://www.portalfiscal.inf.br/NFAg/wsdl/<service>).
"""

from dataclasses import field, make_dataclass

SOAP_ENV_NS = "http://schemas.xmlsoap.org/soap/envelope/"
WSDL_NS = "http://www.portalfiscal.inf.br/NFAg/wsdl/%s"

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
        # NFAgRecepcao: the NFAg goes gzipped and base64 encoded as text
        dados_field = ("value", str, field(default="", metadata={"required": True}))
    else:
        dados_field = (
            "content",
            list[object],
            field(default_factory=list, metadata=WILDCARD),
        )
    dados_msg = make_dataclass(
        "NfagDadosMsg", [dados_field], namespace=_meta("nfagDadosMsg", namespace)
    )
    result_msg = make_dataclass(
        "NfagResultMsg",
        [("content", list[object], field(default_factory=list, metadata=WILDCARD))],
        namespace=_meta("nfagResultMsg", namespace),
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
        [("nfagDadosMsg", dados_msg | None, field(default=None, metadata=element))],
    )
    soap_output = _envelope(
        service,
        "Output",
        [
            (
                "nfagResultMsg",
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


NfagRecepcao = _soap_action("NFAgRecepcao", "NFAgRecepcao", compressed=True)
NfagRecepcaoEvento = _soap_action("NFAgRecepcaoEvento", "NFAgRecepcaoEvento")
NfagConsulta = _soap_action("NFAgConsulta", "NFAgConsultaNF")
NfagStatusServico = _soap_action("NFAgStatusServico", "NFAgStatusServicoNF")
