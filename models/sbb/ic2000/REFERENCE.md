# SBB IC2000 double-deck coaches and Bt control car: reference

341 coaches built 1997–2004 by FIAT-SIG/Schindler, hauled or pushed by the Re 460 (Bt remote
control also works with the BLS Re 465). Typical formation (fr.wikipedia): Bt-B-B-B-B-WRB-A-A-A-AD
+ Re 460. Modernised 2019–2025 as "IC2020" (new interior, LED lighting, new paint; colours of the
new paint not found).

## Data (de.wikipedia "IC2000", fr.wikipedia "Voiture IC 2000 et IC 2020", retrieved 2026-11-22)
| Type | Number | Seats | Modelled as |
|---|---|---|---|
| A | 70 (+16 converted to AS) | 86, 1st | `ic2000_a` |
| AD | 40 | 61, 1st + luggage | `ic2000_ad` |
| B | 149 | 126 (fr: 128), 2nd | `ic2000_b` |
| WRB / BR | 26 (16 WRB + 10 BR) | not given | not modelled |
| Bt | 40 | 98, 2nd | `ic2000_bt` |

Fleet values (fr infobox): 26.80 m over buffers, 2.825 m wide, 4.595 m high, bogie wheelbase
2.835 m, tare 45–50 t, 200 km/h. Per-type lengths and masses are not given; all are modelled at
26.8 m (compressed to 25.6 m = 8/8), 48 t (Bt 50 t, **assumed**).

## Photos used (Wikimedia Commons, Category:SBB IC2000)
| Ref | File | Author | Licence |
|---|---|---|---|
| ref01 | [FFS B 50 85 26-94 068-1 Chur 280615.jpg](https://commons.wikimedia.org/wiki/File:FFS_B_50_85_26-94_068-1_Chur_280615.jpg) | NAC | CC BY-SA 4.0 |
| ref02 | [2021-02-05 IC2000 Kiesen.jpg](https://commons.wikimedia.org/wiki/File:2021-02-05_IC2000_Kiesen.jpg) (1st-class yellow line) | Uschoen | CC BY-SA 4.0 |
| ref03 | [Rotkreuz Bt IC 2000 3399.JPG](https://commons.wikimedia.org/wiki/File:Rotkreuz_Bt_IC_2000_3399.JPG) | Lord Koxinga | CC BY-SA 3.0 |
| ref04 | [S02 692 Bf Bern Hbf, IC2000-Bt.jpg](https://commons.wikimedia.org/wiki/File:S02_692_Bf_Bern_Hbf,_IC2000-Bt.jpg) | Falk2 | CC BY-SA 4.0 |

## Measurements (z ≈ 12.2 per m, roof z 56, deck heights as the FV-Dosto; ref01, oblique)
| Feature | z |
|---|---|
| Anthracite lower band (lower-deck windows straddle its top) | below 21 |
| Lower-deck windows | 15–27 |
| Anthracite mid band (yellow line above it on 1st class) | 31–35 |
| Upper-deck windows | 38–49 |
| Red door panels (door leaves 6–33, upper window inside) | 6–50 |
| Grey roof | from 50 |

Doors at both ends of the lower deck, lower deck between the bogies, small windows over the
intermediate levels (layout **approximate**). Bt (ref03/ref04): single-level cab section ≈5.6 m
with a Re 460-style raked front: red lower front, anthracite windscreen band (running back
along the cab section) and a red band above it, grey roof cap with a grille and the top lamp.

## Livery
de.wikipedia "Design": anthracite stripes top and bottom, a two-part grey-white middle band,
coral-red vertical stripes at the doors and blue accents. Modelled: white body (CC2), anthracite
bands (fixed), red door panels and Bt front (CC1), blue class strips, grey roof.

Builder: `parts/kiss.py`, `style="ic2000"`, `coach=True` (`ic2000_coach`, `ic2000_bt`).
