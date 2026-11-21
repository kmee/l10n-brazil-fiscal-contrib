# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import os
from datetime import date

import nfelib

MODELO_FISCAL_BPE = "63"

# MOC BP-e 1.00b, item 8.2: 100 and 150 authorize the BP-e
BPE_AUTHORIZED = ("100", "150")

# MOC BP-e 1.00b, item 8.2: event registered (with alert) and linked
BPE_EVENT_REGISTERED = ("134", "135")

BPE_CANCEL_EVENT = "110111"
BPE_NO_BOARDING_EVENT = "110115"

# NT BP-e 2026.004 v1.01: from 2027 on vTotDFe adds IBS and CBS to vBP
BPE_IBSCBS_IN_TOTAL_DATE = date(2027, 1, 1)

_SCHEMAS_DIR = os.path.join(os.path.dirname(nfelib.__file__), "bpe", "schemas", "v1_0")

BPE_SCHEMAS = {
    "bpe": os.path.join(_SCHEMAS_DIR, "bpe_v1.00.xsd"),
    "evento": os.path.join(_SCHEMAS_DIR, "eventoBPe_v1.00.xsd"),
    "evCancBPe": os.path.join(_SCHEMAS_DIR, "evCancBPe_v1.00.xsd"),
    "evNaoEmbBPe": os.path.join(_SCHEMAS_DIR, "evNaoEmbBPe_v1.00.xsd"),
}
