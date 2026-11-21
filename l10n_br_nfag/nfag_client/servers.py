# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""NFAg authorizer, as listed at https://dfe-portal.svrs.rs.gov.br/NFAG/Servicos

The NFAg is authorized only by SVRS (MOC NFAg 1.00l, Visão Geral, item 12).
"""

from enum import Enum


class Endpoint(Enum):
    RECEPCAO = "NFAgRecepcao"
    RECEPCAO_EVENTO = "NFAgRecepcaoEvento"
    CONSULTA = "NFAgConsulta"
    STATUS_SERVICO = "NFAgStatusServico"


SERVERS = {
    "prod": "https://nfag.svrs.rs.gov.br/WS/{service}/{service}.asmx",
    "dev": "https://nfag-homologacao.svrs.rs.gov.br/WS/{service}/{service}.asmx",
}


def get_location(ambiente, endpoint):
    environment = "prod" if ambiente == "1" else "dev"
    return SERVERS[environment].format(service=endpoint.value)
