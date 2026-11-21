This module reports the free observations of the NF-e items, group VA
`obsItem` created by NT 2021.004 v1.20: one observation of the taxpayer
(`obsCont`) and one of the tax authority (`obsFisco`) per item, each
with a field name (`xCampo`) and a text (`xTexto`).

The observations are set once on the product and copied to the fiscal
document lines of that product. They can be changed on each line, and
the lines of an incoming NF-e keep the observations of the supplier XML.

The field name must have 1 to 20 characters and the text 1 to 60, as
the layout requires.
