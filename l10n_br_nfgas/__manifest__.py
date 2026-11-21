# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "NFGas",
    "summary": "Nota Fiscal Eletrônica do Gás (NFGas, modelo 76)",
    "version": "18.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/kmee/l10n-brazil-fiscal-contrib",
    "development_status": "Alpha",
    "external_dependencies": {
        "python": [
            "nfelib",
            "brazil_fiscal_client",
        ],
    },
    "depends": [
        "l10n_br_fiscal_edi",
        "l10n_br_fiscal_certificate",
        "l10n_br_nfgas_spec",
        "spec_driven_model",
    ],
    "data": [
        "data/l10n_br_fiscal_document_type.xml",
        "security/ir.model.access.csv",
        "views/document_view.xml",
        "views/res_company_view.xml",
    ],
    "installable": True,
}
