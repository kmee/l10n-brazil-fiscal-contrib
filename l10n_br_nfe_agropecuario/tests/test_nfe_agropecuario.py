# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

NFE_NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}
CPF = "52998224725"


@tagged("post_install", "-at_install")
class TestNFeAgropecuario(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.document = cls.env.ref("l10n_br_nfe.demo_nfe_natural_icms_7_resale")
        cls.document.ind_final = "1"
        cls.line = cls.document.fiscal_line_ids[:1]
        ncm = cls.env["l10n_br_fiscal.ncm"]
        cls.line.ncm_id = ncm.search(
            [("code_unmasked", "=", "38089220")], limit=1
        ) or ncm.create({"code": "3808.92.20", "name": "Fungicidas"})

    def _prescription(self):
        return self.env["nfe.40.agropecuario"].create(
            {
                "nfe40_defensivo": [
                    Command.create(
                        {"nfe40_nReceituario": "REC-2026-1", "nfe40_CPFRespTec": CPF}
                    )
                ]
            }
        )

    def _cattle_permit(self):
        guia = self.env["nfe.40.guiatransito"].create(
            {"nfe40_tpGuia": "1", "nfe40_UFGuia": "MT", "nfe40_nGuia": "123456"}
        )
        return self.env["nfe.40.agropecuario"].create({"nfe40_guiaTransito": guia.id})

    def test_nfe_xml_has_defensivo(self):
        document = self.document
        document.nfe40_agropecuario = self._prescription()
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
        document.action_document_confirm()
        self.assertFalse(document.xml_error_message)
        xml = base64.b64decode(document.authorization_event_id.file_request_id.datas)
        defensivo = etree.fromstring(xml).find(
            ".//nfe:infNFe/nfe:agropecuario/nfe:defensivo", NFE_NS
        )
        self.assertEqual(
            (
                defensivo.findtext("nfe:nReceituario", namespaces=NFE_NS),
                defensivo.findtext("nfe:CPFRespTec", namespaces=NFE_NS),
            ),
            ("REC-2026-1", CPF),
        )

    def test_validation_rules(self):
        document = self.document
        errors = document._nfe40_agropecuario_errors()
        self.assertTrue(any("ZF02-10" in error for error in errors))
        self.line.cfop_id = self.env["l10n_br_fiscal.cfop"].search(
            [("code", "=", "6922")], limit=1
        )
        self.assertFalse(document._nfe40_agropecuario_errors())
        document.nfe40_agropecuario = self._cattle_permit()
        self.assertTrue(
            any("ZF05-14" in error for error in document._nfe40_agropecuario_errors())
        )
        document.nfe40_agropecuario.nfe40_defensivo = (
            self._prescription().nfe40_defensivo
        )
        self.assertTrue(
            any("not both" in error for error in document._nfe40_agropecuario_errors())
        )

    def test_layout_constraints(self):
        with self.assertRaises(ValidationError):
            self.env["nfe.40.defensivo"].create(
                {"nfe40_nReceituario": "REC", "nfe40_CPFRespTec": "12345678900"}
            )
        with self.assertRaises(ValidationError):
            self.env["nfe.40.guiatransito"].create(
                {"nfe40_tpGuia": "1", "nfe40_UFGuia": "MT", "nfe40_nGuia": "12A"}
            )
