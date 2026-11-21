# Arquitetura

Este repositório estende a localização brasileira do Odoo mantida pela OCA em
[OCA/l10n-brazil](https://github.com/OCA/l10n-brazil). Ele nunca altera os módulos do
OCA/l10n-brazil: todos os módulos daqui dependem deles, instalados pelo PyPI, e os
estendem por herança e pelos hooks do `spec_driven_model`.

## Por que um repositório separado

O OCA/l10n-brazil já tem mais de 60 módulos, e o CI dele instala e testa o repositório
inteiro a cada pull request. Cada módulo novo ali deixa mais lento todo pull request da
localização, inclusive os que não têm nada a ver com ele. A maior parte dos módulos
daqui atende a um único segmento (distribuição de combustíveis, concessionárias,
transporte de passageiros, energia e saneamento, telecomunicações, mercado imobiliário),
então eles moram num repositório próprio:

- o núcleo fica enxuto e o CI dele continua rápido;
- os módulos de nicho têm revisão e ritmo de publicação próprios;
- quem não precisa deles não instala nem testa.

O repositório é uma incubadora, no mesmo espírito do
[OCA/mis-builder-contrib](https://github.com/OCA/mis-builder-contrib): segue o template
de addons, as licenças e as convenções da OCA desde o primeiro commit, para poder ser
levado inteiro para a organização da OCA.

## O que vem para cá e o que vai para o OCA/l10n-brazil

| Mudança                                                                                                                | Onde                                              |
| ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| Grupo do leiaute usado por um segmento, num documento que o OCA/l10n-brazil já emite (NF-e, NFC-e, NFS-e, CT-e, MDF-e) | aqui, um módulo por grupo                         |
| Documento fiscal inteiro que o OCA/l10n-brazil não emite                                                               | aqui, um módulo `*_spec` e um módulo do documento |
| Correção pequena ou grupo que qualquer emitente pode precisar, dentro de um módulo existente da OCA                    | OCA/l10n-brazil                                   |
| Trabalho que já tem pull request aberto no OCA/l10n-brazil                                                             | continua nesse pull request                       |

## Camadas

### Módulos de spec (`l10n_br_<documento>_spec`)

Modelos abstratos do Odoo gerados pelo
[xsdata-odoo](https://github.com/akretion/xsdata-odoo) a partir do XSD do documento, com
um prefixo de campo por documento e versão (por exemplo `bpe10_`, `nf3e10_`,
`nfcom10_`). Seguem os módulos `l10n_br_*_spec` do OCA/l10n-brazil. Arquivo gerado nunca
é editado à mão: o readme de cada módulo de spec registra como regerá-lo e os contornos
necessários no gerador.

Os bindings Python vêm do [nfelib](https://github.com/akretion/nfelib) quando ele tem o
documento. Quando não tem, o módulo de spec traz bindings gerados com o xsdata em
`bindings/` até que sejam levados ao nfelib.

### Módulos de documento (`l10n_br_<documento>`)

Emitem um documento a partir do `l10n_br_fiscal.document`, com o tipo de documento do
modelo (63 para o BP-e, 66 para a NF3e, 62 para a NFCom, 64 para a GTV-e e assim por
diante), do mesmo jeito que o `l10n_br_mdfe` e o `l10n_br_cte`:

- os grupos do leiaute são empilhados no documento fiscal e nas linhas (`StackedModel`);
- os tributos, inclusive IBS e CBS, vêm do motor fiscal do `l10n_br_fiscal`;
- o XML é assinado com o certificado da empresa e validado contra o XSD antes de sair do
  Odoo;
- a transmissão usa um cliente sobre o
  [brazil-fiscal-client](https://pypi.org/project/brazil-fiscal-client/), no padrão dos
  clientes de NF-e, CT-e e MDF-e do nfelib. Onde as definições dos webservices ainda não
  são públicas, a transmissão está no roadmap do módulo e o envio é recusado com uma
  mensagem clara.

### Módulos de grupo (`l10n_br_<documento>_<grupo>`)

Preenchem um grupo específico de um documento que o OCA/l10n-brazil já emite, por
exemplo `l10n_br_nfe_comb` (combustíveis), `l10n_br_nfe_veic` (veículos novos),
`l10n_br_nfse_nacional_obra` (construção civil) ou `l10n_br_cte_multimodal`. Um módulo
de grupo normalmente:

- acrescenta o cadastro de que precisa (produto, lote, parceiro, empresa ou código de
  tributação municipal);
- calcula o grupo no documento fiscal ou na linha a partir desse cadastro, editável pelo
  usuário;
- grava o grupo pelos hooks de exportação do `spec_driven_model`
  (`_export_tag_<schema>_<grupo>` ou `_export_fields_<schema>_<grupo>`) quando o núcleo
  não o empilha;
- barra a confirmação com as regras de validação do manual de orientação (MOC) e das
  notas técnicas (NT) que valem para o grupo, citando o código da regra.

## Séries

A `18.0` é a série principal. Os módulos são portados para a `16.0`, a série que a
maioria das empresas brasileiras usa em produção, depois de mesclados na `18.0`.

## CI

O CI é o da OCA (imagens `oca-ci`). Ele instala só este repositório e as dependências
dele pelo PyPI, o que traz consequências que o repositório principal não tem:

- o `test-requirements.txt` fixa bibliotecas que os pacotes publicados da OCA usam sem
  declarar, ou que quebram a imagem (o `cryptography` mais novo);
- o `l10n_br_fiscal_contrib_setup_tests` é um módulo só de CI que carrega o plano de
  contas brasileiro nas empresas demo, que o OCA/l10n-brazil recebe dos próprios módulos
  de plano de contas;
- dado de demonstração nunca gera fatura, e os testes trabalham no nível do documento
  fiscal quando isso basta;
- parceiros de teste usam CNPJs que não colidem com os dados de demonstração do
  OCA/l10n-brazil.

## Ida para a OCA

Quando o repositório for para a OCA, o `copier update` troca o slug da organização e o
site do template, o repositório é transferido e entra nos projetos da localização no
[OCA/repo-maintainer-conf](https://github.com/OCA/repo-maintainer-conf).

## Repositórios irmãos

O mesmo modelo de separação vale para outras áreas da localização. O
[kmee/l10n-brazil-hr](https://github.com/kmee/l10n-brazil-hr) reúne os módulos de
recursos humanos (folha, eSocial, SST, ponto e recrutamento).
