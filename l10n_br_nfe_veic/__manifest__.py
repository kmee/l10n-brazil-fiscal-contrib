# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "NF-e New Vehicles (veicProd)",
    "summary": "Grupo de veículo novo dos itens da NF-e a partir dos números de série",
    "version": "16.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/kmee/l10n-brazil-fiscal-contrib",
    "development_status": "Beta",
    "depends": [
        "l10n_br_nfe",
        "l10n_br_stock_account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/nfe_veicprod_view.xml",
        "views/product_template_view.xml",
        "views/stock_lot_view.xml",
        "views/document_line_view.xml",
        "views/account_move_view.xml",
    ],
    "installable": True,
}
