from . import res_partner
from . import res_company
from . import real_estate_property
from . import participant
from . import document

# the schema marker covers only the models of this package, which all inject
# NF-e ABI spec mixins (the fiscal document line is extended outside of it)
spec_schema = "nfeabi"
spec_version = "10"
