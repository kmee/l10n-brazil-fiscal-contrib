# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""NFGas authorizer, as listed at https://dfe-portal.svrs.rs.gov.br/NFGAS/Servicos

SVRS is the only authorizer published (production and homologation).
"""

from enum import Enum


class Endpoint(Enum):
    RECEPCAO = "NFGasRecepcao"
    RECEPCAO_EVENTO = "NFGasRecepcaoEvento"
    CONSULTA = "NFGasConsulta"
    STATUS_SERVICO = "NFGasStatusServico"
    QRCODE = "QRCode"


SERVERS = {
    "prod": {
        Endpoint.RECEPCAO: (
            "https://nfgas.svrs.rs.gov.br/WS/NFGasRecepcao/NFGasRecepcao.asmx"
        ),
        Endpoint.RECEPCAO_EVENTO: (
            "https://nfgas.svrs.rs.gov.br"
            "/WS/NFGasRecepcaoEvento/NFGasRecepcaoEvento.asmx"
        ),
        Endpoint.CONSULTA: (
            "https://nfgas.svrs.rs.gov.br/WS/NFGasConsulta/NFGasConsulta.asmx"
        ),
        Endpoint.STATUS_SERVICO: (
            "https://nfgas.svrs.rs.gov.br/WS/NFGasStatusServico/NFGasStatusServico.asmx"
        ),
        Endpoint.QRCODE: "https://dfe-portal.svrs.rs.gov.br/nfgas/qrCode",
    },
    "dev": {
        Endpoint.RECEPCAO: (
            "https://nfgas-homologacao.svrs.rs.gov.br"
            "/WS/NFGasRecepcao/NFGasRecepcao.asmx"
        ),
        Endpoint.RECEPCAO_EVENTO: (
            "https://nfgas-homologacao.svrs.rs.gov.br"
            "/WS/NFGasRecepcaoEvento/NFGasRecepcaoEvento.asmx"
        ),
        Endpoint.CONSULTA: (
            "https://nfgas-homologacao.svrs.rs.gov.br"
            "/WS/NFGasConsulta/NFGasConsulta.asmx"
        ),
        Endpoint.STATUS_SERVICO: (
            "https://nfgas-homologacao.svrs.rs.gov.br"
            "/WS/NFGasStatusServico/NFGasStatusServico.asmx"
        ),
        Endpoint.QRCODE: "https://dfe-portal.svrs.rs.gov.br/nfgas/qrCode",
    },
}


def get_location(ambiente, endpoint):
    return SERVERS["prod" if ambiente == "1" else "dev"][endpoint]
