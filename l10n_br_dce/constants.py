# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import os

from odoo.addons import l10n_br_dce_spec

MODELO_FISCAL_DCE = "99"

DCE_VERSION = "1.00"

# MOC DC-e, Visão Geral, item 5.2.5: 100 authorizes the DC-e
DCE_AUTHORIZED = ("100",)

# MOC DC-e, Visão Geral, item 5.5: 135 "Cancelamento homologado" and 155
# "Cancelamento homologado fora de prazo" (item 5.5.4)
DCE_EVENT_REGISTERED = ("135", "155")

DCE_CANCEL_EVENT = "110111"

# Ide/tpEmit (NT 2024.001 v1.30, field B08a) the module issues: the company
# issues its own DC-e, or the DC-e of a sender as a marketplace or a carrier
DCE_ISSUER_MARKETPLACE = "1"
DCE_ISSUER_OWN = "2"
DCE_ISSUER_CARRIER = "3"

DCE_ISSUER_TYPES = [
    (DCE_ISSUER_MARKETPLACE, "Marketplace"),
    (DCE_ISSUER_OWN, "Own Issuer"),
    (DCE_ISSUER_CARRIER, "Carrier"),
]

# NT 2024.001 v1.30, rules I06-10 and W16-10
DCE_MAX_ITEM_VALUE = 100000000.0
DCE_MAX_TOTAL_VALUE = 100000000.0

# MOC DC-e, Anexo I, rule E04-20
DCE_HOMOLOGATION_NAME = "DCE EMITIDA EM AMBIENTE DE HOMOLOGACAO"

# MOC DC-e, Anexo I, group ZA (fixed texts of xObs1 and xObs2)
DCE_DECLARATION_1 = (
    "É contribuinte de ICMS qualquer pessoa física ou jurídica, que realize, "
    "com habitualidade ou em volume que caracterize intuito comercial, "
    "operações de circulação de mercadoria ou prestações de serviços de "
    "transportes interestadual e intermunicipal e de comunicação, ainda que "
    "as operações e prestações de iniciem no exterior (Lei Complementar nº "
    "87/96, Art. 4º)"
)
DCE_DECLARATION_2 = (
    "Constitui crime contra a ordem tributária suprimir ou reduzir tributo, ou "
    "contribuição social e qualquer acessório: quando negar ou deixar de "
    "fornecer, quando obrigatório, nota fiscal ou documento equivalente, "
    "relativa a venda de mercadoria ou prestação de serviço, efetivamente "
    "realizada ou fornece-la em desacordo com a legislação. Sob pena de "
    "reclusão de 2 (dois) e 5 (cinco) anos, e multa (Lei 8.137/90, Art 1ª, V)"
)

_SCHEMAS_DIR = os.path.join(
    os.path.dirname(l10n_br_dce_spec.__file__), "schemas", "v1_0"
)

DCE_SCHEMAS = {
    "dce": os.path.join(_SCHEMAS_DIR, "dce_v1.00.xsd"),
    "evento": os.path.join(_SCHEMAS_DIR, "eventoDCe_v1.00.xsd"),
    "evCancDCe": os.path.join(_SCHEMAS_DIR, "evCancDCe_v1.00.xsd"),
}
