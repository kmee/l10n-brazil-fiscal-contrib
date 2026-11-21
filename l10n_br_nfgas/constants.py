# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_br_nfgas_spec.models.v1_0.nfgas_tipos_basico_v1_00 import (
    ICMS00_CST,
    ICMS20_CST,
    ICMS40_CST,
    ICMS90_CST,
)

MODELO_FISCAL_NFGAS = "76"

NFGAS_VERSION = "1.00"

NFGAS_ENVIRONMENTS = [("1", "Produção"), ("2", "Homologação")]
NFGAS_ENVIRONMENT_DEFAULT = "2"

# MOC NFGas 1.00g, Visão Geral, status query service: 100 (authorized) and 150
# (authorized out of time)
NFGAS_AUTHORIZED = ("100", "150")

# MOC NFGas 1.00g, Visão Geral, item 5 (end of the event processing): 135
# registered and linked, 134 registered with an alert
NFGAS_EVENT_REGISTERED = ("134", "135")

NFGAS_CANCEL_EVENT = "110111"
NFGAS_EVENT_VERSION = "1.00"

# NT 2026.004 v1.01, item 4 (rule 365): vTotDFe adds IBS and CBS from 2027 on
NFGAS_IBSCBS_IN_TOTAL_YEAR = 2027

# MOC NFGas 1.00g, Anexo I, item 2.5 (rule G66a)
NFGAS_CFOPS = (
    "5352",
    "5353",
    "5651",
    "5652",
    "5653",
    "5654",
    "5655",
    "5656",
)

# Item classification table of the NFGas portal (cClass)
# (https://dfe-portal.svrs.rs.gov.br/NFGAS/tabelacclass, rule G57). Only the
# codes of the normal billing (tpFat 1) that add to the total: the deductions
# (group 500) and the aggregator invoice (group 060) are not supported yet.
NFGAS_CCLASS = [
    ("0100101", "Gas natural"),
    ("0100102", "Gas natural - termo fixo"),
    ("0100103", "Gas natural - demanda"),
    ("0100104", "Gas natural - sobre demanda (PGU)"),
    ("0100105", "Gas natural - subvenção Tarifária"),
    ("0100106", "Gas natural - consumo mínimo"),
    ("0100199", "Gas natural - demais"),
    ("0110101", "Biometano"),
    ("0110102", "Biometano - termo fixo"),
    ("0110103", "Biometano - demanda"),
    ("0110104", "Biometano - sobre demanda (PGU)"),
    ("0110105", "Biometano - Subvenção Tarifária"),
    ("0110106", "Biometano - consumo mínimo"),
    ("0110199", "Biometano - demais"),
    ("0200101", "Uso do Sistema de Distribuição / Movimentação (TUSD | TMOV)"),
    (
        "0200102",
        "Uso do Sistema de Distribuição / Movimentação (TUSD | TMOV) - sobre demanda",
    ),
    ("0200103", "Reserva de capacidade"),
    ("0200104", "Compromisso Mínimo de Capacidade"),
    ("0200199", "Demais serviços de distribuição"),
    ("0210101", "Serviços correlatos"),
    ("0210102", "Serviços acessórios"),
    ("0210103", "Serviços atípicos"),
    ("0210104", "Comissionamento de rede interna"),
    ("0210105", "Participação financeira"),
    ("0210199", "Demais serviços"),
    ("0300101", "Quantidade mínima não retirada (Take or pay)"),
    ("0300102", "Compromisso mínimo de capacidade (Ship or pay)"),
    ("0300103", "Penalidade por desvio de programação a maior"),
    ("0300104", "Penalidade por desvio de programação a menor"),
    ("0300199", "Demais penalidades"),
    ("0700101", "Segunda via de fatura"),
    ("0700102", "Ajuste de conta positivo"),
    ("0700199", "Demais Cobranças"),
    ("0710101", "Cobrança de Multa de Mora"),
    ("0710102", "Cobrança de Juros de Mora"),
    ("0710103", "Correção Monetária"),
    ("0720101", "Juros sobre parcelamento"),
    ("0720102", "Multa parcelamento"),
    ("0720103", "Correção Monetária parcelamento"),
    ("0730101", "Parcelamento valor principal"),
]

# Quantity origins that need the gMedicao group (annotation of gMedicao in
# nfgasTiposBasico_v1.00.xsd, NT 2026.004 RTC v1.01 package)
NFGAS_MEASURED_ORIGINS = ("2", "5")

# ICMS group of the item (imposto) by CST, from the choice of the XSD. The
# groups with ICMS ST or deferral (ICMS10, ICMS51, ICMS60 and ICMS70) are not
# supported yet.
NFGAS_ICMS_GROUP_BY_CST = {
    cst: group
    for group, selection in (
        ("ICMS00", ICMS00_CST),
        ("ICMS20", ICMS20_CST),
        ("ICMS40", ICMS40_CST),
        ("ICMS90", ICMS90_CST),
    )
    for cst, _label in selection
}
