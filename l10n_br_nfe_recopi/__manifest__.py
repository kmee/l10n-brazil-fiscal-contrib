# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "NF-e Immune Paper (RECOPI)",
    "summary": "RECOPI number of the immune paper items of the NF-e",
    "version": "16.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/kmee/l10n-brazil-fiscal-contrib",
    "development_status": "Beta",
    "depends": [
        "l10n_br_nfe",
    ],
    "data": [
        "views/product_template_view.xml",
        "views/document_view.xml",
        "views/document_line_view.xml",
    ],
    "installable": True,
}
