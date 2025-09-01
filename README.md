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

## Intégration IA

### Installation des dépendances

```sh
pip install -r requirements.txt
pip install openai
```

### Configuration de l'environnement

1. Créer un fichier `.env` contenant votre clé :

   ```sh
   echo "OPENROUTER_API_KEY=\"votre_clé\"" > .env
   ```

2. Charger les variables dans votre session :

   ```sh
   export $(grep -v '^#' .env | xargs)
   ```

La clé ne doit jamais être committée dans le dépôt : le fichier `.env` est ignoré par Git.

### Exemples d'utilisation

```sh
run-diagnostic "analyse des horloges PTP"
logs
chat "Quels paquets GOOSE sont suspects?"
```
