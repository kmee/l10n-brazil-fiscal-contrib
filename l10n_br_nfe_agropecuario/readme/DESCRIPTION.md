This module reports the agricultural, livestock and forest products
group of the NF-e (group ZF, `agropecuario`), created by NT 2024.003:
either the pesticide prescriptions (`defensivo`, up to 20, with the
prescription number and the CPF of the responsible technician) or the
transit permit (`guiaTransito`: type, state, series and number of the
GTA, TTA, DTA, ATV, PTV, GTV or forest permit).

The group is typed on the fiscal document, *Agricultural Products* tab,
because the prescription and the permit belong to each operation.

The layout is checked as the data is typed (prescription number with 1
to 30 characters, permit number with 1 to 9 digits, series with up to 9
characters) and the CPF of the technician must be valid (rule ZF03a-10,
rejection 308). Before the NF-e (model 55) is issued, the module refuses
what the validation rules of NT 2024.003 v1.10 reject:

- ZF02-10 (rejection 835): an item with a pesticide NCM sold to the
  final consumer in a normal NF-e without the prescription, except for
  return CFOP, transfers (X.151, X.152, X.155, X.156), future delivery
  (5.922, 6.922) and the biological and sanitizing NCM of exception 4.
- ZF02-20 (rejection 309): a prescription when no item has a pesticide
  NCM.
- ZF05-10 (rejection 836): cattle (NCM 0102) in a normal NF-e of a
  company of BA, GO, MA or MT (table 4.1 of the NT) without an animal
  transit permit, except for the CFOP listed by the rule.
- ZF05-14 (rejection 310) and ZF05-24 (rejection 312): an animal or a
  vegetable transit permit when no item is a live animal (NCM 01 and
  0301) or a vegetable product (NCM 06, 07, 08 and 12).
- The group with both the prescriptions and the permit, or with
  neither, which the layout does not accept.
