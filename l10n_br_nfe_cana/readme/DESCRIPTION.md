This module reports the sugarcane acquisition register of the NF-e
(group ZC, `cana`): harvest, reference month, daily supplies (`forDia`),
month, previous and grand totals, deductions (`deduc`), supplies, total
deductions and net supplies amounts.

The group is typed on the fiscal document, *Sugarcane* tab. The month
total is the sum of the daily supplies, the grand total is the month
total plus the previous total, the total deductions is the sum of the
deductions and the net supplies amount is the supplies amount minus the
deductions; all of them can be changed by hand.

The layout is checked as the data is typed: harvest with 4 to 9
characters, reference month as MM/YYYY, days from 1 to 31 with a single
supply per day. Before the NF-e is issued, the module also refuses an
NFC-e with the group (rule ZC01-10 of the MOC), a group without daily
supplies or with more than 31, and more than 10 deductions.
