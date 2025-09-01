# networkanalyser

Outils d'analyse réseau pour PTP et IEC 61850.

## Scripts

- `ptp_diag.py` : analyse des trames PTP via linuxptp.
- `iec61850_diag.py` : détection des trames IEC61850 (GOOSE, SV) et rapports MMS.

## Installation

```sh
sudo make install
```

Cette commande installe `ptp-diag`, `iec61850-diag` ainsi que les utilitaires
`ptp-logs` et `ptp-chat` qui utilisent le même environnement virtuel.

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
ptp-logs
ptp-chat
```

## Intégration IA

### Installation des dépendances

```sh
pip install -r requirements.txt
```

Seules les bibliothèques listées dans `requirements.txt` sont nécessaires au
fonctionnement de `cli_chat.py` ; le paquet `openai` n'est pas requis.

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
ptp-diag -i eth0
ptp-logs
ptp-chat
```

#### Exemple complet

```sh
# 1. Lancer un diagnostic PTP et générer les logs
ptp-diag -i eth0 -t 30

# 2. Afficher les logs
ptp-logs

# 3. Ouvrir une conversation avec le modèle
ptp-chat
> Quels paquets GOOSE sont suspects ?
```
