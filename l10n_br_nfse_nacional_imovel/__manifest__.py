# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "NFS-e Nacional Real Estate (imovel)",
    "summary": "Grupo de bens imóveis (IBSCBS/imovel) da DPS da NFS-e Nacional",
    "version": "18.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/kmee/l10n-brazil-fiscal-contrib",
    "development_status": "Alpha",
    "depends": [
        "l10n_br_nfse_nacional",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/document_view.xml",
    ],
    "installable": True,
}
