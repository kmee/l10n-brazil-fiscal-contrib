# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

MODELO_FISCAL_NFEABI = "77"

NFEABI_VERSION = "1.00"
NFEABI_EVENT_VERSION = "1.00"

NFEABI_ENVIRONMENTS = [("1", "Production"), ("2", "Homologation")]
NFEABI_ENVIRONMENT_DEFAULT = "2"

# NT 2026.001 v1.00, rule C04-10
NFEABI_HOMOLOGATION_NAME = (
    "NF-E ABI EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL"
)

# NT 2026.001 v1.00, chapter 3 (list of events)
NFEABI_CANCEL_EVENT = "110111"
NFEABI_UNDO_EVENT = "112320"

# MOC NF-e ABI 1.00a, Anexo I, B08 and NT 2026.001, B08 (2, transition, is not
# supported yet)
NFEABI_DOCUMENT_TYPES = [("0", "Simplified"), ("1", "Complete")]

# Tabela de Códigos NF-e ABI v1.01, sheets modOper, natOper and gModNat
MODE_GENERAL = "01"
MODE_AUCTION = "02"
MODE_ASSIGNMENT = "03"
MODE_EXCHANGE = "04"

NFEABI_MODES = [
    (MODE_GENERAL, "01 - General alienation"),
    (MODE_AUCTION, "02 - Judicial auction, adjudication or redemption"),
    (MODE_ASSIGNMENT, "03 - Assignment or transfer of rights"),
    (MODE_EXCHANGE, "04 - Exchange"),
]

NFEABI_NATURES = [
    ("01", "01 - Purchase and sale"),
    ("02", "02 - Payment in kind"),
    ("03", "03 - Operations of the secured creditor or consortium group"),
    ("04", "04 - Corporate acts"),
    ("05", "05 - Donations or free transfers"),
    ("06", "06 - Judicial auction"),
    ("07", "07 - Adjudication"),
    ("08", "08 - Redemption"),
    ("09", "09 - Assignment of rights over the property"),
    ("10", "10 - Emphyteusis or surface right"),
    ("11", "11 - Use or usufruct"),
    ("12", "12 - Other real rights"),
    ("13", "13 - Exchange of real estate only"),
    (
        "14",
        "14 - Paid purchase with debt acknowledgment and promise of payment in "
        "kind (LC 214/2025, article 252, paragraph 6)",
    ),
    ("15", "15 - Other exchange"),
]

# natOper allowed by modOper (sheet gModNat)
NFEABI_NATURES_BY_MODE = {
    MODE_GENERAL: ("01", "02", "03", "04", "05"),
    MODE_AUCTION: ("06", "07", "08"),
    MODE_ASSIGNMENT: ("09", "10", "11", "12"),
    MODE_EXCHANGE: ("13", "14", "15"),
}

# exchange natures that only tax the balance (torna), rules U14-50 and U12-60
EXCHANGE_BALANCE_NATURES = ("13", "14")

NFEABI_OPERATION_DETAILS = [
    ("01", "01 - Promise of purchase and sale"),
    ("02", "02 - Final purchase and sale"),
    ("03", "03 - Promise of payment in kind"),
    ("04", "04 - Final payment in kind"),
    ("05", "05 - Ownership consolidation by the secured creditor"),
    ("06", "06 - Ownership consolidation by the consortium group"),
    ("07", "07 - Alienation by the secured creditor"),
    ("08", "08 - Alienation by the consortium group"),
    ("09", "09 - Capital contribution"),
    ("10", "10 - Corporate merger"),
    ("11", "11 - Amalgamation"),
    ("12", "12 - Total or partial spin-off"),
    ("13", "13 - Company dissolution"),
    ("14", "14 - Property withdrawal by capital reduction"),
    ("15", "15 - Donation without consideration to the donor"),
    ("16", "16 - Donation with consideration to the donor"),
    ("17", "17 - Onerous assignment of the rights of a purchase promise"),
    ("18", "18 - Onerous assignment of inheritance rights"),
    ("19", "19 - Onerous assignment of rights over a fiduciary sold property"),
    ("20", "20 - Assignment of the rights of the auction buyer"),
    ("21", "21 - Assignment of the rights of the adjudicatee"),
    ("22", "22 - Emphyteusis of federal properties"),
    ("23", "23 - Onerous transfer of the emphyteusis"),
    ("24", "24 - Onerous grant of the surface right"),
    ("25", "25 - Onerous assignment of the surface right"),
    ("26", "26 - Onerous grant of use or usufruct"),
    ("27", "27 - Onerous transfer of use or usufruct"),
    ("28", "28 - Onerous grant of special housing use"),
    ("29", "29 - Onerous transfer of special housing use"),
    ("30", "30 - Onerous grant of the real right of use"),
    ("31", "31 - Onerous transfer of the real right of use"),
    ("32", "32 - Onerous grant of the slab right"),
    ("33", "33 - Onerous assignment of the slab right"),
    ("34", "34 - Onerous assignment of provisional possession rights"),
]

# detOper allowed by natOper (sheet gModNat)
NFEABI_DETAILS_BY_NATURE = {
    "01": ("01", "02"),
    "02": ("03", "04"),
    "03": ("05", "06", "07", "08"),
    "04": ("09", "10", "11", "12", "13", "14"),
    "05": ("15", "16"),
    "09": ("17", "18", "19", "20", "21"),
    "10": ("22", "23", "24", "25"),
    "11": ("26", "27"),
    "12": ("28", "29", "30", "31", "32", "33", "34"),
}

# sheet espImovel
NFEABI_PROPERTY_KINDS = [
    ("01", "01 - Land"),
    ("02", "02 - House"),
    ("03", "03 - Apartment"),
    ("04", "04 - Parking space"),
    ("05", "05 - Slab"),
    ("06", "06 - Office room"),
    ("07", "07 - Set of office rooms"),
    ("08", "08 - Shop"),
    ("09", "09 - Mezzanine shop"),
    ("10", "10 - Parking lot"),
    ("11", "11 - Shack"),
    ("12", "12 - Warehouse"),
    ("99", "99 - Other"),
]

# sheet enquadramento
PROPERTY_NEW_RESIDENTIAL = "01"
PROPERTY_RESIDENTIAL_LOT = "03"
NFEABI_PROPERTY_CLASSES = [
    (PROPERTY_NEW_RESIDENTIAL, "01 - New residential property"),
    ("02", "02 - Used residential property"),
    (PROPERTY_RESIDENTIAL_LOT, "03 - Residential lot"),
    ("04", "04 - Non residential"),
]

# sheet tpInstrumento
NFEABI_INSTRUMENTS = [
    ("01", "01 - Private contract or instrument"),
    ("02", "02 - Private contract with a financial institution"),
    ("03", "03 - Public deed"),
    ("04", "04 - Auction record"),
    ("05", "05 - Adjudication record"),
    ("06", "06 - Court decision"),
    ("07", "07 - Registration of the ownership consolidation"),
    ("08", "08 - Articles of association"),
    ("09", "09 - Amendment of the articles"),
    ("10", "10 - General meeting minutes"),
    ("11", "11 - Company dissolution agreement"),
    ("99", "99 - Other"),
]

# sheet tpDesfaz
NFEABI_UNDO_TYPES = [
    ("01", "01 - Rescission agreement"),
    ("02", "02 - Out of court termination"),
    ("03", "03 - Court decision"),
    ("04", "04 - Arbitral award"),
    ("05", "05 - Reversal of the ownership consolidation"),
    ("99", "99 - Other"),
]

# MOC NF-e ABI 1.00a, Anexo I, E19 and F19
NFEABI_CONTRIBUTOR = [
    ("0", "0 - Not an IBS/CBS taxpayer"),
    ("1", "1 - IBS/CBS regular regime taxpayer"),
    ("2", "2 - Simples Nacional"),
]
