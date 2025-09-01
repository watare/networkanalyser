# networkanalyser

Outils d'analyse réseau pour PTP et IEC 61850.

## Scripts

- `ptp_diag.py` : analyse des trames PTP via linuxptp.
- `iec61850_diag.py` : détection des trames IEC61850 (GOOSE, SV) et rapports MMS.

## Installation

```sh
sudo make install
```

## Utilisation

```sh
sudo ptp-diag -i eth0
sudo iec61850-diag -i eth0
```
