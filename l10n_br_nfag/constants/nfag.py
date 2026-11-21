# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tools.misc import file_path

from odoo.addons.l10n_br_nfag_spec.models.v1_0.nfag_tipos_basico_v1_00 import (
    COFINS_CST,
    PIS_CST,
)

MODELO_FISCAL_NFAG = "75"

NFAG_VERSION = "1.00"

# Id of infNFAg: pattern NFAG[0-9]{6}[A-Z0-9]{12}[0-9]{26} of the XSD
NFAG_ID_PREFIX = "NFAG"

NFAG_ENVIRONMENTS = [("1", "Production"), ("2", "Homologation")]
NFAG_ENVIRONMENT_DEFAULT = "2"

# Services page of the NFAg portal (dfe-portal.svrs.rs.gov.br/NFAG/Servicos)
NFAG_QRCODE_URL_DEFAULT = "https://dfe-portal.svrs.rs.gov.br/nfag/qrCode"

# MOC NFAg 1.00l, Visão Geral: 100 and 150 authorize the NFAg
NFAG_AUTHORIZED = ("100", "150")

# MOC NFAg 1.00l, Visão Geral (Recepção de Evento): event registered and
# linked to the NFAg (136 registers it without the link)
NFAG_EVENT_REGISTERED = ("134", "135")

NFAG_CANCEL_EVENT = "110111"
NFAG_EVENT_SEQUENCE = "001"

NFAG_PIS_CST = [code for code, _label in PIS_CST]
NFAG_COFINS_CST = [code for code, _label in COFINS_CST]


def nfag_schema(name):
    return file_path(f"l10n_br_nfag_spec/schemas/v1_0/{name}_v1.00.xsd")
