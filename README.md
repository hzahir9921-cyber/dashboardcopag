# COPAG — Dashboard logistique

Application Streamlit en français pour analyser les expéditions et les opérations de transport de COPAG au Maroc.

## Contenu du ZIP

```text
copag_dashboard/
├── app.py
├── requirements.txt
└── README.md
```

**Aucun fichier de données n'est fourni dans cette archive.** Le dashboard vous demande d'importer votre propre fichier CSV depuis l'interface.

## Lancement

Python 3.10 ou plus récent est recommandé.

```bash
python -m venv .venv
```

Activation de l'environnement :

```bash
# Windows
.venv\\Scripts\\activate

# macOS / Linux
source .venv/bin/activate
```

Installation des dépendances :

```bash
pip install -r requirements.txt
```

Démarrage :

```bash
streamlit run app.py
```

## Connexion de démonstration

- **Utilisateur :** `hajar`
- **Mot de passe :** `ha2707`

Ces identifiants sont prévus pour une démonstration locale uniquement. Ne déployez pas cette configuration telle quelle sur Internet. Pour un déploiement public, remplacez les identifiants par des secrets sécurisés.

## Importer le dataset

Après le lancement, connectez-vous puis importez votre fichier CSV depuis le champ **Importer les données**.

Le CSV doit contenir au minimum les colonnes suivantes :

- `shipment_id`, `date`
- `origin_hub`, `destination_city`, `destination_region`
- `distance_km`, `planned_duration_min`, `actual_duration_min`, `delay_min`, `on_time`
- `mode`, `product_category`
- `fuel_liters`, `co2_kg`, `cost_mad`
- `lat`, `lon`, `o_lat`, `o_lon`, `d_lat`, `d_lon`

Le dashboard vérifie les colonnes nécessaires et signale celles qui manquent.

## Fonctionnalités

- Filtres par période, région, mode, catégorie de produit, hub et ville.
- KPI : expéditions, ponctualité, coût moyen, carburant moyen, CO₂ moyen et vitesse moyenne.
- Graphiques de performance quotidienne, routes principales, retards, corrélations, coûts et répartition des produits.
- Analyses de distance, carburant et vitesse.
- Carte des positions de flotte et carte des flux hub-destination.
- Tableau détaillé et export CSV des expéditions filtrées.

## Calcul de la vitesse

Le dataset source ne comporte pas nécessairement une colonne de vitesse. Le dashboard estime donc la vitesse moyenne à partir de la distance et de la durée réelle :

`vitesse (km/h) = distance_km / (actual_duration_min / 60)`

Cette valeur est une estimation par trajet et non une vitesse GPS instantanée.

## À propos des cartes

Les positions et les flux affichés sont basés sur les coordonnées présentes dans le CSV. Ils ne représentent pas un suivi GPS en temps réel.
