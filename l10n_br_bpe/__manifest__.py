# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "BP-e",
    "summary": "Bilhete de Passagem Eletronico (BP-e, modelo 63)",
    "version": "18.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/kmee/l10n-brazil-fiscal-contrib",
    "development_status": "Alpha",
    "depends": [
        "l10n_br_fiscal_edi",
        "l10n_br_fiscal_certificate",
        "l10n_br_bpe_spec",
        "spec_driven_model",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizards/bpe_no_boarding_wizard_view.xml",
        "views/document_view.xml",
        "views/res_company_view.xml",
    ],
    "installable": True,
}
