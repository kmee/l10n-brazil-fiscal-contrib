# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "BP-e TM",
    "summary": "BP-e do transporte metropolitano e semiurbano (BP-e TM, modelo 63)",
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
        ],
    },
    "depends": [
        "l10n_br_bpe",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/document_view.xml",
        "views/document_line_view.xml",
        "views/res_company_view.xml",
    ],
    "installable": True,
}
