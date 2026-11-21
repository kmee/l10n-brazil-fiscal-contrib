# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""BP-e authorizers, as listed at https://dfe-portal.svrs.rs.gov.br/BPe/Servicos"""

from enum import Enum


class Endpoint(Enum):
    RECEPCAO = "BPeRecepcao"
    RECEPCAO_EVENTO = "BPeRecepcaoEvento"
    CONSULTA = "BPeConsulta"
    STATUS_SERVICO = "BPeStatusServico"
    QRCODE = "QRCode"


# UFs with their own authorizer; every other UF uses SVRS
UF_AUTHORIZER = {
    "31": "MG",
    "50": "MS",
    "51": "MT",
    "41": "PR",
    "35": "SP",
}

# Paraiba is authorized by SVRS but has its own QR Code address
QRCODE_BY_UF = {
    "25": {
        "prod": "http://www.receita.pb.gov.br/bpe/qrCode",
        "dev": "http://www.receita.pb.gov.br/bpe/qrCode",
    },
}

SERVERS = {
    "MG": {
        "prod": {
            Endpoint.RECEPCAO: "https://bpe.fazenda.mg.gov.br/bpe/services/BPeRecepcao",
            Endpoint.RECEPCAO_EVENTO: (
                "https://bpe.fazenda.mg.gov.br/bpe/services/BPeRecepcaoEvento"
            ),
            Endpoint.CONSULTA: "https://bpe.fazenda.mg.gov.br/bpe/services/BPeConsulta",
            Endpoint.STATUS_SERVICO: (
                "https://bpe.fazenda.mg.gov.br/bpe/services/BPeStatusServico"
            ),
            Endpoint.QRCODE: (
                "https://portalbpe.fazenda.mg.gov.br/portalbpe/sistema/qrcode.xhtml"
            ),
        },
        "dev": {
            Endpoint.RECEPCAO: "https://hbpe.fazenda.mg.gov.br/bpe/services/BPeRecepcao",
            Endpoint.RECEPCAO_EVENTO: (
                "https://hbpe.fazenda.mg.gov.br/bpe/services/BPeRecepcaoEvento"
            ),
            Endpoint.CONSULTA: "https://bpe.fazenda.mg.gov.br/bpe/services/BPeConsulta",
            Endpoint.STATUS_SERVICO: (
                "https://hbpe.fazenda.mg.gov.br/bpe/services/BPeConsulta"
            ),
            Endpoint.QRCODE: (
                "https://portalbpe.fazenda.mg.gov.br/portalbpe/sistema/qrcode.xhtml"
            ),
        },
    },
    "MS": {
        "prod": {
            Endpoint.RECEPCAO: "https://bpe.fazenda.ms.gov.br/ws/BPeRecepcao",
            Endpoint.RECEPCAO_EVENTO: "https://bpe.fazenda.ms.gov.br/ws/BPeRecepcaoEvento",
            Endpoint.CONSULTA: "https://bpe.fazenda.ms.gov.br/ws/BPeConsulta",
            Endpoint.STATUS_SERVICO: "https://bpe.fazenda.ms.gov.br/ws/BPeStatusServico",
            Endpoint.QRCODE: "http://www.dfe.ms.gov.br/bpe/qrcode",
        },
        "dev": {
            Endpoint.RECEPCAO: "https://homologacao.bpe.ms.gov.br/ws/BPeRecepcao",
            Endpoint.RECEPCAO_EVENTO: (
                "https://homologacao.bpe.ms.gov.br/ws/BPeRecepcaoEvento"
            ),
            Endpoint.CONSULTA: "https://bpe.fazenda.mg.gov.br/bpe/services/BPeConsulta",
            Endpoint.STATUS_SERVICO: (
                "https://homologacao.bpe.ms.gov.br/ws/BPeStatusServico"
            ),
            Endpoint.QRCODE: "http://www.dfe.ms.gov.br/bpe/qrcode",
        },
    },
    "MT": {
        "prod": {
            Endpoint.RECEPCAO: "https://www.sefaz.mt.gov.br/bpe-ws/services/BPeRecepcao",
            Endpoint.RECEPCAO_EVENTO: (
                "https://www.sefaz.mt.gov.br/bpe-ws/services/BPeRecepcaoEvento"
            ),
            Endpoint.CONSULTA: "https://www.sefaz.mt.gov.br/bpe-ws/services/BPeConsulta",
            Endpoint.STATUS_SERVICO: (
                "https://www.sefaz.mt.gov.br/bpe-ws/services/BPeStatusServico"
            ),
            Endpoint.QRCODE: "https://www.sefaz.mt.gov.br/BPe/qrcode",
        },
        "dev": {
            Endpoint.RECEPCAO: (
                "https://homologacao.sefaz.mt.gov.br/bpe-ws/services/BPeRecepcao"
            ),
            Endpoint.RECEPCAO_EVENTO: (
                "https://homologacao.sefaz.mt.gov.br/bpe-ws/services/BPeRecepcaoEvento"
            ),
            Endpoint.CONSULTA: (
                "https://homologacao.sefaz.mt.gov.br/bpe-ws/services/BPeConsulta"
            ),
            Endpoint.STATUS_SERVICO: (
                "https://homologacao.sefaz.mt.gov.br/bpe-ws/services/BPeStatusServico"
            ),
            Endpoint.QRCODE: "https://homologacao.sefaz.mt.gov.br/BPe/qrcode",
        },
    },
    "PR": {
        "prod": {
            Endpoint.RECEPCAO: "https://bpe.fazenda.pr.gov.br/bpe/BPeRecepcao",
            Endpoint.RECEPCAO_EVENTO: (
                "https://bpe.fazenda.pr.gov.br/bpe/BPeRecepcaoEvento"
            ),
            Endpoint.CONSULTA: "https://bpe.fazenda.pr.gov.br/bpe/BPeConsulta",
            Endpoint.STATUS_SERVICO: "https://bpe.fazenda.pr.gov.br/bpe/BPeStatusServico",
            Endpoint.QRCODE: "https://www.fazenda.pr.gov.br/bpe/qrcode",
        },
        "dev": {
            Endpoint.RECEPCAO: (
                "https://homologacao.bpe.fazenda.pr.gov.br/bpe/BPeRecepcao"
            ),
            Endpoint.RECEPCAO_EVENTO: (
                "https://homologacao.bpe.fazenda.pr.gov.br/bpe/BPeRecepcaoEvento"
            ),
            Endpoint.CONSULTA: (
                "https://homologacao.bpe.fazenda.pr.gov.br/bpe/BPeConsulta"
            ),
            Endpoint.STATUS_SERVICO: (
                "https://homologacao.bpe.fazenda.pr.gov.br/bpe/BPeStatusServico"
            ),
            Endpoint.QRCODE: "https://www.fazenda.pr.gov.br/bpe/qrcode",
        },
    },
    "SP": {
        "prod": {
            Endpoint.RECEPCAO: (
                "https://bpe.fazenda.sp.gov.br/BPeWeb/services/BPeRecepcao.asmx"
            ),
            Endpoint.RECEPCAO_EVENTO: (
                "https://bpe.fazenda.sp.gov.br/BPeWeb/services/BPeRecepcaoEvento.asmx"
            ),
            Endpoint.CONSULTA: (
                "https://bpe.fazenda.sp.gov.br/BPeWeb/services/BPeConsulta.asmx"
            ),
            Endpoint.STATUS_SERVICO: (
                "https://bpe.fazenda.sp.gov.br/BPeWeb/services/BPeStatusServico.asmx"
            ),
            Endpoint.QRCODE: "https://bpe.fazenda.sp.gov.br/BPe/qrcode",
        },
        "dev": {
            Endpoint.RECEPCAO: (
                "https://homologacao.bpe.fazenda.sp.gov.br"
                "/BPeWeb/services/BPeRecepcao.asmx"
            ),
            Endpoint.RECEPCAO_EVENTO: (
                "https://homologacao.bpe.fazenda.sp.gov.br"
                "/BPeWeb/services/BPeRecepcaoEvento.asmx"
            ),
            Endpoint.CONSULTA: (
                "https://homologacao.bpe.fazenda.sp.gov.br"
                "/BPeWeb/services/BPeConsulta.asmx"
            ),
            Endpoint.STATUS_SERVICO: (
                "https://homologacao.bpe.fazenda.sp.gov.br"
                "/BPeWeb/services/BPeStatusServico.asmx"
            ),
            Endpoint.QRCODE: "https://homologacao.bpe.fazenda.sp.gov.br/BPe/qrcode",
        },
    },
    "SVRS": {
        "prod": {
            Endpoint.RECEPCAO: (
                "https://bpe.svrs.rs.gov.br/ws/bpeRecepcao/bpeRecepcao.asmx"
            ),
            Endpoint.RECEPCAO_EVENTO: (
                "https://bpe.svrs.rs.gov.br/ws/bpeRecepcaoEvento/bpeRecepcaoEvento.asmx"
            ),
            Endpoint.CONSULTA: (
                "https://bpe.svrs.rs.gov.br/ws/bpeConsulta/bpeConsulta.asmx"
            ),
            Endpoint.STATUS_SERVICO: (
                "https://bpe.svrs.rs.gov.br/ws/bpeStatusServico/bpeStatusServico.asmx"
            ),
            Endpoint.QRCODE: "https://dfe-portal.svrs.rs.gov.br/bpe/qrCode",
        },
        "dev": {
            Endpoint.RECEPCAO: (
                "https://bpe-homologacao.svrs.rs.gov.br/ws/bpeRecepcao/bpeRecepcao.asmx"
            ),
            Endpoint.RECEPCAO_EVENTO: (
                "https://bpe-homologacao.svrs.rs.gov.br"
                "/ws/bpeRecepcaoEvento/bpeRecepcaoEvento.asmx"
            ),
            Endpoint.CONSULTA: (
                "https://bpe-homologacao.svrs.rs.gov.br/ws/bpeConsulta/bpeConsulta.asmx"
            ),
            Endpoint.STATUS_SERVICO: (
                "https://bpe-homologacao.svrs.rs.gov.br"
                "/ws/bpeStatusServico/bpeStatusServico.asmx"
            ),
            Endpoint.QRCODE: "https://dfe-portal.svrs.rs.gov.br/bpe/qrCode",
        },
    },
}


def get_server_key(uf_ibge_code):
    return UF_AUTHORIZER.get(uf_ibge_code, "SVRS")


def get_location(uf_ibge_code, ambiente, endpoint):
    environment = "prod" if ambiente == "1" else "dev"
    if endpoint == Endpoint.QRCODE and uf_ibge_code in QRCODE_BY_UF:
        return QRCODE_BY_UF[uf_ibge_code][environment]
    return SERVERS[get_server_key(uf_ibge_code)][environment][endpoint]
