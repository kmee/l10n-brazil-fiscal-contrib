# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "CT-e Multimodal",
    "summary": "Grupo do transporte multimodal (infModal, modal 06) do CT-e 4.00",
    "version": "18.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/kmee/l10n-brazil-fiscal-contrib",
    "development_status": "Beta",
    "depends": [
        "l10n_br_cte",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/document_view.xml",
    ],
    "installable": True,
}
