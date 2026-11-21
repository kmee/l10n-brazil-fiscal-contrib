# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "NF-e Pickup Address (retirada)",
    "summary": "Pickup address of the NF-e from the warehouse of the deliveries",
    "version": "16.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/kmee/l10n-brazil-fiscal-contrib",
    "development_status": "Beta",
    "depends": [
        "l10n_br_nfe",
        "l10n_br_account",
        "stock_picking_invoice_link",
    ],
    "data": [
        "views/document_view.xml",
    ],
    "installable": True,
}
