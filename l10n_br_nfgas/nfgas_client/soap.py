# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""SOAP bindings of the NFGas webservices (MOC NFGas 1.00g, Visão Geral,
item 3, "Padrão de Mensagens dos Web Services", and item 4).

Same shape as the classes xsdata generates from the WSDL for the other
documents in nfelib (nfelib/mdfe/soap) and as the bpe_client of l10n_br_bpe:
the WSDL of the NFGas is only served to a client certificate, so these few
classes are declared here from the namespace and method names of the MOC.
"""

from dataclasses import field, make_dataclass

SOAP_ENV_NS = "http://schemas.xmlsoap.org/soap/envelope/"
WSDL_NS = "http://www.portalfiscal.inf.br/NFGas/wsdl/%s"

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
        # NFGasRecepcao: the NFGas goes gzipped and base64 encoded as text
        dados_field = ("value", str, field(default="", metadata={"required": True}))
    else:
        dados_field = (
            "content",
            list[object],
            field(default_factory=list, metadata=WILDCARD),
        )
    dados_msg = make_dataclass(
        "NfgasDadosMsg", [dados_field], namespace=_meta("nfgasDadosMsg", namespace)
    )
    result_msg = make_dataclass(
        "NfgasResultMsg",
        [("content", list[object], field(default_factory=list, metadata=WILDCARD))],
        namespace=_meta("nfgasResultMsg", namespace),
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
        [("nfgasDadosMsg", dados_msg | None, field(default=None, metadata=element))],
    )
    soap_output = _envelope(
        service,
        "Output",
        [
            (
                "nfgasResultMsg",
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


NfgasRecepcao = _soap_action("NFGasRecepcao", "NFGasRecepcao", compressed=True)
NfgasRecepcaoEvento = _soap_action("NFGasRecepcaoEvento", "NFGasRecepcaoEvento")
NfgasConsulta = _soap_action("NFGasConsulta", "NFGasConsultaNF")
NfgasStatusServico = _soap_action("NFGasStatusServico", "NFGasStatusServicoNF")
