This module fills the transport subgroups of the NF-e (group X, `transp`)
that the localization leaves empty: the vehicle (`veicTransp`), the
trailers (`reboque`) and the ICMS retention of the transport
(`retTransp`). The freight modality (`modFrete`), the carrier
(`transporta`) and the volumes (`vol`) stay with `l10n_br_delivery_nfe`.

Vehicle and trailers come from the carrier vehicles of
`l10n_br_delivery` (plate, state and ANTT code), that until now never
reached the NF-e. On the fiscal document (*Delivery* tab):

- vehicle: by default the vehicle of the carrier, when it has only one;
  it can be changed;
- trailers: up to 5 vehicles (layout limit).

Each one becomes a `veicTransp` or `reboque` group with the plate (upper
case, without separators), the state and the ANTT code (RNTC, up to 20
characters). They are left out of the XML in interstate operations (rule
X02-20, rejection 868, NT 2017.002), in the NFC-e and in the NF-e with
the simplified DANFE (rules X18-10 and X22-10, rejections 756 and 757).

The ICMS retention of the transport is used when the issuer retains the
ICMS of a freight service (for instance one hired from an independent
carrier): service value, retention base (by default the service value),
rate, ICMS retained (base times rate), freight CFOP and city of the
taxable event (by default the city of the company). It is refused in the
NFC-e and in the NF-e with the simplified DANFE (rule X11-10, rejection
755).

Before the NF-e is confirmed the module refuses a plate that does not
match the layout pattern and an ICMS retention without CFOP or city.
