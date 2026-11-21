1. Create a fiscal document with document type 66, the customer, the fiscal
   operation and the NF3e series.
2. In the NF3e tab, fill in the consumer unit (acessante), the invoice data
   (competence period, due date, next reading, payment line and automatic
   debit or bank and branch), the meters and the billing history (1 to 5
   quantities, each with the 13 months that the layout requires).
3. On each item, enter the electricity CFOP and, in the NF3e tab of the line,
   the item classification code, the unit of measure and the origin of the
   billed quantity. For IBS and CBS, enter the tax classification
   (`cClassTrib`): the fiscal engine computes the values.
4. Confirm the document: the XML is generated, signed and validated, and is
   kept in the authorization event. Schema errors appear in the XML error
   message.
