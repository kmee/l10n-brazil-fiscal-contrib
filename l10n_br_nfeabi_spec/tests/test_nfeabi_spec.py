# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from pathlib import Path

from odoo import fields
from odoo.tests import TransactionCase, tagged

from ..bindings import v1_0 as bindings
from ..models.v1_0 import nfe_abi_v1_00, nfeabi_tipos_basico_v1_00

SCHEMAS = Path(__file__).parents[1] / "schemas" / "v1_0"

# the list of access keys of gPagAntecipado is mapped to a single field
SKIPPED_TAGS = {("nfeabi.10.tgpagantecipado", "chNFePagAnt")}


@tagged("post_install", "-at_install")
class TestNfeAbiSpec(TransactionCase):
    def test_spec_models_cover_bindings(self):
        """Every tag of the bindings has its nfeabi10_ field."""
        checked = 0
        for spec_module in (nfe_abi_v1_00, nfeabi_tipos_basico_v1_00):
            for spec_class in vars(spec_module).values():
                binding_type = getattr(spec_class, "_binding_type", None)
                if not isinstance(spec_class, type) or not binding_type:
                    continue
                binding_class = bindings
                for attr in binding_type.split("."):
                    binding_class = getattr(binding_class, attr)
                odoo_fields = {
                    name
                    for name, value in vars(spec_class).items()
                    if isinstance(value, fields.Field)
                }
                for fname, fspec in binding_class.__dataclass_fields__.items():
                    tag = fspec.metadata.get("name", fname)
                    if fname == "signature" or (spec_class._name, tag) in SKIPPED_TAGS:
                        continue
                    self.assertIn(
                        f"nfeabi10_{tag}",
                        odoo_fields,
                        f"{spec_class._name} misses the {tag} tag",
                    )
                self.assertIn(spec_class._name, self.env)
                checked += 1
        self.assertGreater(checked, 40)

    def test_ibscbs_groups(self):
        self.assertEqual(
            self.env["nfeabi.10.tginftrib"]._fields["nfeabi10_IBSCBS"].comodel_name,
            "nfeabi.10.tibscbs",
        )
        self.assertEqual(
            self.env["nfeabi.10.ttotal"]._fields["nfeabi10_tribTot"].comodel_name,
            "nfeabi.10.ttribtot",
        )

    def test_binding_schema_validation(self):
        """A binding built by hand serializes to a XML the official XSD
        accepts (NT 2026.001, schema package 1.06)."""
        address = bindings.Tendereco(
            xLgr="Rua das Palmeiras",
            nro="100",
            cMun="3550308",
            xMun="Sao Paulo",
            UF="SP",
        )
        tribtot = bindings.TtribTot(
            vRedAjusteIndiv="0.00",
            vRedSocialIndiv="0.00",
            vBC="500000.00",
            vIBSUF="500.00",
            vIBSMun="0.00",
            vCBS="4500.00",
        )
        group = bindings.Tgibscbs(
            vOperacIndiv="500000.00",
            vBC="500000.00",
            gIBSUF=bindings.Tgibsuf(
                pIBSUF="0.1000",
                gRed=bindings.Tgred(pRedAliq="0.0000", pAliqEfet="0.1000"),
                vIBSUF="500.00",
            ),
            gIBSMun=bindings.Tgibsmun(
                pIBSMun="0.0000",
                gRed=bindings.Tgred(pRedAliq="0.0000", pAliqEfet="0.0000"),
                vIBSMun="0.00",
            ),
            gCBS=bindings.Tgcbs(
                pCBS="0.9000",
                gRed=bindings.Tgred(pRedAliq="0.0000", pAliqEfet="0.9000"),
                vCBS="4500.00",
            ),
        )
        key = "35261199999999000191770010000000011000000015"
        inf = bindings.TinfNfeAbi(
            ide=bindings.Tide(
                cUF=bindings.TcodUfIbge("35"),
                cNF="0000001",
                mod=bindings.TmodNfeAbi("77"),
                serie="1",
                nNF="1",
                dhEmi="2026-11-20T12:00:00-03:00",
                tpNF="0",
                tpImp="1",
                gModNat=bindings.TgmodNat(modOper="01", natOper="01"),
                tpEmis="1",
                nSiteAutoriz="0",
                cDV=key[-1],
                tpAmb=bindings.Tamb("2"),
                finNFe="1",
                procEmi="0",
                verProc="test",
            ),
            emit=bindings.Temit(
                CNPJ=key[6:20], xNome="Alienante", enderEmit=address, tpEmit="01"
            ),
            transmit=[
                bindings.Ttransmit(CNPJ=key[6:20], xNome="Alienante", nTransmit="1")
            ],
            adquirente=[
                bindings.Tadquirente(
                    CPF="11144477735",
                    xNome="Adquirente",
                    enderAdquirente=address,
                    nAdquir="1",
                )
            ],
            imovel=bindings.Timovel(
                tipo="1",
                cadastro=bindings.TcadastroImovel(indIPTU="1", nIPTU="0001"),
                espImovel="01",
                enquadramento="02",
                enderImovel=address,
            ),
            infOper=bindings.TinfOper(
                vTotalOperacao="500000.00",
                instrumento=bindings.Tinstrumento(
                    tpInstrumento="01", dtInstrumento="2026-11-20"
                ),
            ),
            gInfTrib=bindings.TginfTrib(
                IBSCBS=bindings.Tibscbs(CST="000", cClassTrib="000001", gIBSCBS=group)
            ),
            total=bindings.Ttotal(
                vTotalOperacao="500000.00",
                vOperacIndiv="500000.00",
                tribTot=tribtot,
                vNF="505000.00",
            ),
            infRespTec=bindings.TinfRespTec(
                CNPJ=key[6:20],
                xContato="Contato",
                email="contato@example.com",
                fone="1133334444",
            ),
            versao="1.00",
            Id=f"NFeABI{key}",
        )
        xml = bindings.NfeAbi(
            infNFeABI=inf,
            infNFeSupl=bindings.TinfNfeSupl(
                qrCode="https://www.example.com.br/nfeabi/qrcode?"
                f"chNFeABI={key}&tpAmb=2",
                urlChave="https://www.example.com.br/nfeabi/consulta",
            ),
        ).to_xml()
        errors = bindings.NfeAbi.schema_validation(
            xml, str(SCHEMAS / "NFeABI_v1.00.xsd")
        )
        # only the signature is missing: it is added when the XML is signed
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("Signature", errors[0])
