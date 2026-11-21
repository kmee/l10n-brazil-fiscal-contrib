# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "NF-e Purchase Information (compra)",
    "summary": "Nota de empenho, pedido de compra e contrato na NF-e",
    "version": "18.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/kmee/l10n-brazil-fiscal-contrib",
    "development_status": "Beta",
    "depends": [
        "l10n_br_nfe",
        "l10n_br_account",
    ],
    "data": [
        "views/document_view.xml",
    ],
    "installable": True,
}
