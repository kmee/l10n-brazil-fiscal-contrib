# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""DC-e authorizer, as listed at https://dfe-portal.svrs.rs.gov.br/DCE/Servicos

Every UF uses the same national environment of the DC-e (Ambiente Nacional da
DCe), hosted by the Paraná tax authority.
"""

from enum import Enum


class Endpoint(Enum):
    AUTORIZACAO = "DCeAutorizacao"
    RECEPCAO_EVENTO = "DCeRecepcaoEvento"
    CONSULTA = "DCeConsulta"
    STATUS_SERVICO = "DCeStatusServico"
    QRCODE = "QRCode"


SERVERS = {
    "1": {
        Endpoint.AUTORIZACAO: "https://dce.fazenda.pr.gov.br/dce/DCeAutorizacao",
        Endpoint.RECEPCAO_EVENTO: (
            "https://dce.fazenda.pr.gov.br/dce/DCeRecepcaoEvento"
        ),
        Endpoint.CONSULTA: "https://dce.fazenda.pr.gov.br/dce/DCeConsulta",
        Endpoint.STATUS_SERVICO: "https://dce.fazenda.pr.gov.br/dce/DCeStatusServico",
        Endpoint.QRCODE: "https://www.fazenda.pr.gov.br/dce/qrcode",
    },
    "2": {
        Endpoint.AUTORIZACAO: (
            "https://homologacao.dce.fazenda.pr.gov.br/dce/DCeAutorizacao"
        ),
        Endpoint.RECEPCAO_EVENTO: (
            "https://homologacao.dce.fazenda.pr.gov.br/dce/DCeRecepcaoEvento"
        ),
        Endpoint.CONSULTA: (
            "https://homologacao.dce.fazenda.pr.gov.br/dce/DCeConsulta"
        ),
        Endpoint.STATUS_SERVICO: (
            "https://homologacao.dce.fazenda.pr.gov.br/dce/DCeStatusServico"
        ),
        Endpoint.QRCODE: "https://www.fazenda.pr.gov.br/dce/qrcode",
    },
}


def get_location(environment, endpoint):
    """URL of a DC-e service ("1" production, "2" homologation)."""
    return SERVERS[environment][endpoint]
