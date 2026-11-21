# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "GTV-e",
    "summary": "Guia de Transporte de Valores Eletrônica (GTV-e, modelo 64)",
    "version": "16.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/kmee/l10n-brazil-fiscal-contrib",
    "development_status": "Alpha",
    "depends": [
        "l10n_br_cte",
    ],
    "data": [
        "data/l10n_br_fiscal_document_type.xml",
        "security/ir.model.access.csv",
        "views/document_view.xml",
    ],
    "installable": True,
}
