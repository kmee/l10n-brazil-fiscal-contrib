This module reports the RECOPI number of the immune paper items of the
NF-e (group LB, `nRECOPI`, created by NT 2013/005).

RECOPI is the system that controls the sale of paper used to print
books, newspapers and periodicals, which is immune from taxes. Each
operation registered in it gets a number that the NF-e items of immune
paper must carry.

The number is typed once on the fiscal document (*RECOPI Number*) and
copied to the lines whose product is marked as immune paper. It can be
changed on each line (*Extra Info* tab).

Before the NF-e is confirmed the module refuses the data the SEFAZ
would reject:

- rule LB01-30 (rejection 350): the number must follow the
  `aaaammddHHMMSSffffDD` format of the MOC 7.0 (Visao Geral, section
  8.5): a valid date and time from 2013 to today, followed by two
  modulo 11 check digits;
- rule LB01-10 (rejection 348): the NFC-e does not accept the number.
