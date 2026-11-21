# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "NF3e",
    "summary": "Nota Fiscal de Energia Elétrica Eletrônica (NF3e, modelo 66)",
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
        "l10n_br_nf3e_spec",
        "spec_driven_model",
    ],
    "data": [
        "security/nf3e_security.xml",
        "security/ir.model.access.csv",
        "views/document_view.xml",
        "views/res_company_view.xml",
    ],
    "installable": True,
}
