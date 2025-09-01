# networkanalyser

Outils d'analyse réseau pour PTP et IEC 61850.

## Scripts

- `ptp_diag.py` : analyse des trames PTP via linuxptp.
- `iec61850_diag.py` : détection des trames IEC61850 (GOOSE, SV) et rapports MMS.

## Installation

```sh
sudo make install
```

## Configuration

Copiez le fichier `.env.example` vers `.env` puis définissez la clé API `OPENROUTER_API_KEY` :

```sh
cp .env.example .env
```

Éditez ensuite `.env` pour y renseigner votre clé :

```
OPENROUTER_API_KEY=votre_cle
```

Le fichier `.env` est utilisé par `cli_chat.py` et n'est pas commité dans le dépôt.

## Utilisation

```sh
sudo ptp-diag -i eth0
sudo iec61850-diag -i eth0
```
