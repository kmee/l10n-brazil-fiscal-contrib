# Como contribuir

Contribuições são bem-vindas. O repositório segue as
[diretrizes de contribuição da OCA](https://github.com/OCA/odoo-community.org/blob/master/website/Contribution/CONTRIBUTING.rst),
porque vai ser levado para a organização da OCA. Leia antes o
[ARQUITETURA.md](ARQUITETURA.md): ele explica o que pertence a este repositório e o que
pertence ao [OCA/l10n-brazil](https://github.com/OCA/l10n-brazil).

## Antes de começar

1. Procure no OCA/l10n-brazil um módulo ou um pull request aberto sobre o mesmo grupo ou
   documento. Se houver, contribua lá.
2. Procure nas issues e nos pull requests deste repositório.
3. Encontre a fonte oficial da regra que você vai implementar: o manual de orientação
   (MOC), as notas técnicas (NT) e o XSD publicados pelo fisco. Regra fiscal nunca é
   suposta: o que não puder ser confirmado vai para o roadmap do módulo.

## Pull requests

- Um módulo por pull request. Um documento que precisa de um módulo de spec e de um
  módulo de documento leva dois pull requests, o segundo empilhado sobre o primeiro.
- Nome da branch: `<série>-add-<módulo>` para módulo novo, `<série>-mig-<módulo>` para
  porte, `<série>-fix-<módulo>-<assunto>` para correção.
- Título do pull request: `[<série>][ADD|FIX|IMP|MIG] <módulo>: <resumo>`.
- Mensagem de commit no padrão da OCA: `[ADD] <módulo>: <resumo>`, sem a série. Não suba
  a versão de um módulo existente.
- Módulo novo começa na versão `<série>.1.0.0`, licença AGPL-3 e autor
  `<Sua empresa>, Odoo Community Association (OCA)`.
- Biblioteca Python importada em tempo de execução vai em `external_dependencies` no
  manifest, só pelo nome; o hook do pre-commit regera o `requirements.txt`.

## Código e testes

- Rode `pre-commit run --all-files` até passar. Ele gera o `README.rst` e o
  `static/description/index.html` a partir dos fragmentos em `readme/`: edite os
  fragmentos, nunca os arquivos gerados. Os fragmentos são escritos em português.
- Nunca edite à mão os arquivos gerados dos módulos de spec. Regere como descrito no
  readme do módulo de spec.
- Testes pequenos e rápidos: monte o documento, serialize o XML, valide contra o XSD e
  confira os grupos e as regras que você implementou. Teste nunca chama webservice real.
- Dado de demonstração não gera fatura. Teste que precisa de fatura cria a própria
  empresa com plano de contas, ou conta com o `l10n_br_fiscal_contrib_setup_tests`.
- Nunca use dados reais de contribuinte. CNPJ e CPF de teste não podem colidir com os
  dados de demonstração do OCA/l10n-brazil.

## Porte para a 16.0

Os módulos entram primeiro na `18.0`. O porte para a `16.0` faz cherry-pick dos commits
do módulo na `18.0`, mantendo a autoria, e acrescenta um commit
`[MIG] <módulo>: backport to 16.0` com as adaptações (views com `attrs`, `tree` no lugar
de `list`, `name_get` e assim por diante).

## Assistência de IA

Siga a
[política da OCA sobre contribuições com IA](https://odoo-community.org/blog/news-updates-1/new-ai-policy-248):
quem contribui responde pela mudança e a revisa antes de enviar, commit feito com
assistência de IA leva o trailer `Assisted-by:`, e ferramenta de IA nunca aparece como
coautora. O [AGENTS.md](../AGENTS.md) descreve o repositório para agentes de código.

## Depois do merge

A tabela de módulos do `README.md` da raiz é gerada pelo `oca-gen-addons-table`, do
[OCA/maintainer-tools](https://github.com/OCA/maintainer-tools). Rode quando um pull
request acrescentar ou retirar módulo.

## Licença e CLA

As contribuições são licenciadas sob AGPL-3. Como o repositório vai para a OCA, pedimos
que quem contribui assine o
[Contributor License Agreement da OCA](https://odoo-community.org/page/cla).
