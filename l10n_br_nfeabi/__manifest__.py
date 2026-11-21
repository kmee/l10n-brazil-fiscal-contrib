# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "NF-e ABI",
    "summary": "Emissão da Nota Fiscal Eletrônica de Alienação de Bens Imóveis "
    "(NF-e ABI, modelo 77)",
    "version": "16.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/kmee/l10n-brazil-fiscal-contrib",
    "development_status": "Alpha",
    "external_dependencies": {
        "python": [
            "nfelib",
        ],
    },
    "depends": [
        "l10n_br_fiscal_edi",
        "l10n_br_fiscal_certificate",
        "l10n_br_nfeabi_spec",
        "spec_driven_model",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/l10n_br_fiscal_document_type_data.xml",
        "views/property_view.xml",
        "views/document_view.xml",
        "views/res_company_view.xml",
    ],
    "installable": True,
}
