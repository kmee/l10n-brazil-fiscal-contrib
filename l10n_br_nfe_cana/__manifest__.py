# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "NF-e Sugarcane Acquisition (cana)",
    "summary": "Report the sugarcane acquisition register in the NF-e (cana group)",
    "version": "16.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/kmee/l10n-brazil-fiscal-contrib",
    "development_status": "Beta",
    "maintainers": ["mileo"],
    "depends": [
        "l10n_br_nfe",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/nfe_cana_view.xml",
        "views/document_view.xml",
    ],
    "installable": True,
}
