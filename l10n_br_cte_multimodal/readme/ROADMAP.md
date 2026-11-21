- The CT-e of a service linked to a multimodal transport (`tpServ` 4)
  must reference the multimodal CT-e issued by the operator
  (`infCTeNorm/infServVinc/infCTeMultimodal/chCTeMultimodal`, MOC 4.00
  Annex I rules G057, G058 and G070 to G075). That group is not filled
  yet.
- The event of registration of the multimodal transport
  (`evRegMultimodal`) is not implemented.
- The DACTE does not print the multimodal group.
- Importing a CT-e XML with modal `06` does not read the `multimodal`
  group back.
- The insurance company is typed as text: it could be a partner, with
  the CNPJ taken from it.
