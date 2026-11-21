Technical module for the CI of this repository. It is not meant for production
databases.

The CI installs only the modules of this repository and their dependencies. Without
a Brazilian chart of accounts module, the `l10n_br_account` post-init hook points the
`empresa_lucro_presumido` demo company to the `br_oca_generic` chart, which is never
loaded, and any module that pulls `sale` fails while the test database is created.
Depending on `l10n_br_coa_generic` loads that chart on the demo companies, as in the
OCA/l10n-brazil CI.
