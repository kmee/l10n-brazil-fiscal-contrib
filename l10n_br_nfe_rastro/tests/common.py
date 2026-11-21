# Copyright 2024 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import date, datetime

from lxml import etree

from odoo import Command
from odoo.tests import Form, TransactionCase, tagged

NFE_NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}


@tagged("post_install", "-at_install")
class NFeRastroCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=True, tz="America/Sao_Paulo")
        )
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls._load_chart_of_accounts(cls.company)
        cls.env.user.company_ids |= cls.company
        cls.env.user.company_id = cls.company
        cls.env.user.tz = "America/Sao_Paulo"
        cls.stock_location = cls.env.ref(
            "l10n_br_stock.wh_empresa_lucro_presumido_loc_stock_id"
        )
        cls.picking_type_out = cls.env.ref(
            "l10n_br_stock.wh_empresa_lucro_presumido_picking_type_out"
        )
        cls.partner = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_simples_remessa")
        cls.product = cls._copy_product(
            cls.env.ref("product.product_product_12"),
            {
                "name": "Traced Product",
                "default_code": "TRACED-1",
                "detailed_type": "product",
                "tracking": "lot",
                "use_expiration_date": True,
            },
        )

    @classmethod
    def _copy_product(cls, product, default):
        """Copy a demo product keeping its fiscal type: on 16.0 the company
        dependent fiscal fields are not copied, and without the fiscal type
        the item gets no ICMS."""
        product = product.with_company(cls.company)
        return product.copy(dict(default, fiscal_type=product.fiscal_type))

    @classmethod
    def _load_chart_of_accounts(cls, company):
        """The demo company has no chart of accounts unless a l10n_br_coa_*
        module is installed (in the CI, l10n_br_fiscal_contrib_setup_tests
        brings l10n_br_coa_generic): fall back to the generic chart of the
        core when it is available."""
        receivable = cls.env["account.account"].search_count(
            [
                ("company_id", "=", company.id),
                ("account_type", "=", "asset_receivable"),
            ]
        )
        if receivable:
            return
        chart = cls.env.ref(
            "l10n_generic_coa.configurable_chart_template", raise_if_not_found=False
        )
        if chart:
            chart.try_loading(company=company, install_demo=False)
            company.currency_id = cls.env.ref("base.BRL")

    @classmethod
    def _create_lot(cls, name, production_date, expiration_date, product=None):
        product = product or cls.product
        lot = cls.env["stock.lot"].create(
            {
                "name": name,
                "product_id": product.id,
                "company_id": cls.company.id,
                "production_date": production_date,
                "expiration_date": expiration_date,
            }
        )
        return lot

    @classmethod
    def _add_stock(cls, lot, quantity, product=None):
        product = product or cls.product
        cls.env["stock.quant"].with_company(cls.company)._update_available_quantity(
            product, cls.stock_location, quantity, lot_id=lot
        )

    def _ship(self, product, lot_quantities):
        """Create and validate a delivery of `product`, picking the given
        quantity of each lot, and return the picking."""
        with Form(self.env["stock.picking"].with_company(self.company)) as picking_form:
            picking_form.partner_id = self.partner
            picking_form.picking_type_id = self.picking_type_out
            picking_form.invoice_state = "2binvoiced"
            picking_form.fiscal_operation_id = self.fiscal_operation
            with picking_form.move_ids_without_package.new() as move_form:
                move_form.product_id = product
                move_form.product_uom_qty = sum(lot_quantities.values())
        picking = picking_form.save()
        picking.action_confirm()
        move = picking.move_ids
        move.move_line_ids.unlink()
        for lot, quantity in lot_quantities.items():
            self.env["stock.move.line"].create(
                {
                    "move_id": move.id,
                    "picking_id": picking.id,
                    "product_id": product.id,
                    "product_uom_id": move.product_uom.id,
                    "location_id": move.location_id.id,
                    "location_dest_id": move.location_dest_id.id,
                    "lot_id": lot.id,
                    "qty_done": quantity,
                }
            )
        # expired lots (product_expiry) would open a confirmation wizard
        picking.with_context(skip_expired=True).button_validate()
        self.assertEqual(picking.state, "done")
        return picking

    def _invoice(self, picking):
        wizard = (
            self.env["stock.invoice.onshipping"]
            .with_context(
                active_ids=picking.ids,
                active_model=picking._name,
                active_id=picking.id,
            )
            .create({})
        )
        wizard.onchange_group()
        wizard.fiscal_operation_journal = False
        wizard.action_generate()
        invoice = picking.invoice_ids
        self.assertEqual(len(invoice), 1)
        return invoice

    @staticmethod
    def _set_payment(invoice):
        """The 16.0 NF-e does not build the payment group (detPag) from the
        invoice: fill it so that the XML passes the schema validation."""
        document = invoice.fiscal_document_id
        document.nfe40_detPag = [
            Command.clear(),
            Command.create(
                {
                    "nfe40_indPag": "0",
                    "nfe40_tPag": "01",
                    "nfe40_vPag": document.amount_financial_total,
                }
            ),
        ]

    @staticmethod
    def _rastro_data(line):
        return sorted(
            (r.nfe40_nLote, r.nfe40_qLote, r.nfe40_dFab, r.nfe40_dVal)
            for r in line.nfe40_rastro
        )

    @staticmethod
    def _xml_det_prod(document):
        """The <prod> nodes of the NF-e XML generated at confirmation."""
        xml = base64.b64decode(document.authorization_event_id.file_request_id.datas)
        root = etree.fromstring(xml)
        return root.findall(".//nfe:det/nfe:prod", NFE_NS)

    @staticmethod
    def _datetime(day):
        """Noon in Brazil (15:00 UTC), so the date is the same in both."""
        return datetime.combine(day, datetime.min.time()).replace(hour=15)

    @staticmethod
    def _date(year, month, day):
        return date(year, month, day)
