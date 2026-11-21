# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_br_nf3e_spec.models.v1_0.nf3e_tipos_basico_v1_00 import (
    ICMS00_CST,
    ICMS10_CST,
    ICMS20_CST,
    ICMS40_CST,
    ICMS51_CST,
    ICMS60_CST,
    ICMS90_CST,
)

MODELO_FISCAL_NF3E = "66"

NF3E_VERSION = "1.00"

NF3E_ENVIRONMENTS = [("1", "Produção"), ("2", "Homologação")]
NF3E_ENVIRONMENT_DEFAULT = "2"

# MOC NF3e 1.00a, Visão Geral, item 9.2 and the services page of the NF3e
# portal (dfe-portal.svrs.rs.gov.br/Nf3e/Servicos)
NF3E_QRCODE_URL_DEFAULT = "https://dfe-portal.svrs.rs.gov.br/nf3e/qrCode"

NF3E_CANCEL_EVENT = "110111"
NF3E_EVENT_VERSION = "1.00"

# ICMS group of the item (imposto) by CST, from the choice of the XSD
NF3E_ICMS_GROUP_BY_CST = {
    cst: group
    for group, selection in (
        ("ICMS00", ICMS00_CST),
        ("ICMS10", ICMS10_CST),
        ("ICMS20", ICMS20_CST),
        ("ICMS40", ICMS40_CST),
        ("ICMS51", ICMS51_CST),
        ("ICMS60", ICMS60_CST),
        ("ICMS90", ICMS90_CST),
    )
    for cst, _label in selection
}
