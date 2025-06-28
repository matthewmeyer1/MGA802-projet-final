# VFR Planner - Outil de planification de vol VFR

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)

Outil complet de planification de vol VFR avec calculs automatiques de navigation, intégration météorologique et génération de plans de vol professionnels.

**Projet de session MGA802** - École de technologie supérieure  
**Équipe**: Antoine Gingras, Matthew Meyer, Richard Nguekam, Gabriel Wong-Lapierre

## Fonctionnalités

### Planification de vol complète
- **Base de données d'aéroports**: Plus de 50,000 aéroports mondiaux
- **Calculs de navigation précis**: Distance, cap, temps de vol avec correction de vent
- **Intégration météorologique**: API Tomorrow.io pour données météo en temps réel
- **Optimisation de carburant**: Calculs automatiques avec gestion des réserves

### Interface intuitive
- **Recherche d'aéroports intelligente**: Par code ICAO, IATA, nom ou localisation
- **Planification interactive**: Ajout/modification de waypoints par glisser-déposer
- **Cartes dynamiques**: Visualisation de l'itinéraire avec Folium
- **Filtres avancés**: Par pays, type d'aéroport, équipements

### Export professionnel
- **Plans Excel**: Formats conformes aux standards aéronautiques
- **Documents PDF**: Plans de vol prêts à imprimer
- **Cartes interactives**: Export HTML pour navigation
- **Sauvegarde projet**: Format JSON pour reprendre le travail

### Calculs avancés
- **Navigation orthodromique**: Calculs de grand cercle précis
- **Correction de vent**: Angles et vitesses sol automatiques
- **Déclinaison magnétique**: Conversion cap vrai/magnétique
- **Analyse de carburant**: Vérification autonomie et réserves

## Structure du projet

```
vfr_planner/
│
├── main.py                      # Point d'entrée principal
├── requirements.txt             # Dépendances Python
├── README.md                    # Documentation (ce fichier)
├── airports.csv                 # Base de données d'aéroports
├── LICENSE.md                   # Licence MIT
│
└── vfr_planner/                # Package principal
    ├── __init__.py             # Initialisation du package
    │
    ├── models/                 # Modèles de données
    │   ├── __init__.py
    │   ├── aircraft.py         # Modèle aéronef
    │   ├── waypoint.py         # Modèle waypoint
    │   ├── leg.py              # Modèle segment de vol
    │   └── itinerary.py        # Modèle itinéraire complet
    │
    ├── calculations/           # Moteur de calculs
    │   ├── __init__.py
    │   ├── navigation.py       # Calculs de navigation
    │   ├── weather.py          # Service météorologique
    │   └── aeroport_refuel.py  # Gestion arrêts carburant
    │
    ├── data/                   # Gestion des données
    │   ├── __init__.py
    │   ├── airport_db.py       # Base de données d'aéroports
    │   └── extraction/         # Extraction de données CFS
    │       ├── __init__.py
    │       └── extraction.py
    │
    ├── gui/                    # Interface graphique
    │   ├── __init__.py
    │   ├── main_window.py      # Fenêtre principale
    │   ├── tabs.py             # Onglets de l'interface
    │   └── widgets.py          # Widgets personnalisés
    │
    ├── export/                 # Modules d'export
    │   ├── __init__.py
    │   ├── excel_export.py     # Export Excel
    │   └── pdf_export.py       # Export PDF
    │
    └── utils/                  # Utilitaires
        ├── __init__.py
        └── constants.py        # Constantes de l'application
```

## Installation

### Prérequis
- Python 3.8 ou supérieur
- L'API météo Tomorrow.io est préconfigurée

### Installation automatique

```bash
# Cloner le projet
git clone https://github.com/matthewmeyer1/MGA802-projet-final.git
cd MGA802-projet-final

# Installer le package
pip install -i https://test.pypi.org/simple/ VFR-flight-planner

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
python main.py
```

### Installation manuelle des dépendances

```bash
# Interface graphique
pip install tkinter-dnd2

# Manipulation de données
pip install pandas numpy

# Calculs géographiques
pip install geopy geomag pytz

# API météo
pip install requests

# Export de fichiers
pip install openpyxl xlsxwriter reportlab

# Cartes interactives
pip install folium

# Traitement PDF (optionnel)
pip install PyPDF2

# Tests (développement)
pip install pytest pytest-cov
```

## Utilisation

### Démarrage rapide

1. **Lancez l'application**:
   ```bash
   python main.py
   ```

2. **Configurez votre aéronef** (Onglet Aéronef):
   - Sélectionnez un modèle prédéfini (C172, PA28, etc.)
   - Ou saisissez vos paramètres personnalisés
   - Remplissez les informations de vol

3. **Sélectionnez vos aéroports** (Onglet Aéroports):
   - Utilisez les filtres pour affiner la recherche
   - Recherchez par code ICAO/IATA ou nom
   - Définissez départ et arrivée

4. **Planifiez votre itinéraire** (Onglet Itinéraire):
   - Ajoutez des waypoints intermédiaires
   - Modifiez l'ordre si nécessaire
   - Vérifiez les détails de chaque point

5. **Générez votre plan** (Onglet Plan de vol):
   - L'API météo est préconfigurée
   - Calculez l'itinéraire avec données météo
   - Exportez en Excel ou PDF

### Raccourcis clavier

| Raccourci | Action |
|-----------|--------|
| Ctrl+N | Nouveau projet |
| Ctrl+O | Ouvrir projet |
| Ctrl+S | Sauvegarder |
| Ctrl+Shift+S | Sauvegarder sous |
| F5 | Calculer itinéraire |
| F9 | Carte interactive |
| Ctrl+Q | Quitter |

## Exemples d'utilisation

### Exemple 1: Vol Montréal → Québec

```python
from vfr_planner import VFRPlannerGUI
from vfr_planner.models import Aircraft, Waypoint, Itinerary

# Configuration d'un C172
aircraft = Aircraft(
    registration="C-FXYZ",
    aircraft_type="Cessna 172",
    cruise_speed=110,
    fuel_burn=7.5,
    fuel_capacity=40
)

# Points de navigation
departure = Waypoint(45.458, -73.749, "CYUL")  # Montréal
destination = Waypoint(46.791, -71.393, "CYQB")  # Québec

# Création de l'itinéraire
itinerary = Itinerary(aircraft)
itinerary.add_waypoint(departure)
itinerary.add_waypoint(destination)
itinerary.set_start_time("2025-06-17", "14:00")

# Calcul avec météo (API préconfigurée)
itinerary.create_legs()

# Export
flight_data, legs_data = itinerary.get_flight_plan_data()
```

### Exemple 2: Utilisation programmée

```python
from vfr_planner.data import search_airports
from vfr_planner.calculations import calculate_distance, calculate_bearing

# Recherche d'aéroports
airports = search_airports("CYUL")
print(f"Trouvé: {airports[0]['name']}")

# Calculs de navigation
distance = calculate_distance(45.458, -73.749, 46.791, -71.393)
bearing = calculate_bearing(45.458, -73.749, 46.791, -71.393)

print(f"Distance: {distance:.1f} NM")
print(f"Cap: {bearing:.0f}°")
```

## Tests

```bash
# Lancer tous les tests
pytest

# Tests avec couverture
pytest --cov=vfr_planner

# Tests d'un module spécifique
pytest tests/test_navigation.py
```

## Documentation technique

### Architecture modulaire

Le projet suit une architecture modulaire claire:

- **Models**: Classes de données (Aircraft, Waypoint, Leg, Itinerary)
- **Calculations**: Moteur de calculs (navigation, météo)
- **Data**: Gestion des bases de données (aéroports)
- **GUI**: Interface utilisateur (fenêtres, onglets, widgets)
- **Export**: Génération de documents (Excel, PDF)
- **Utils**: Constantes et utilitaires

### Points d'extension

1. **Nouveaux formats d'export**: Ajoutez des modules dans `export/`
2. **Sources météo supplémentaires**: Étendez `calculations/weather.py`
3. **Bases de données**: Ajoutez des sources dans `data/`
4. **Types d'aéronefs**: Étendez `models/aircraft.py`

### API publique

```python
# Import principal
from vfr_planner import VFRPlannerGUI

# Modèles de données
from vfr_planner.models import Aircraft, Waypoint, Leg, Itinerary

# Calculs
from vfr_planner.calculations import calculate_distance, calculate_bearing

# Base de données
from vfr_planner.data import search_airports, get_airport_by_code

# Export
from vfr_planner.export import export_to_excel, export_to_pdf
```

## Dépannage

### Problèmes courants

**Erreur "Module non trouvé"**
```bash
pip install -r requirements.txt
```

**Problèmes d'API météo**
- L'API Tomorrow.io est préconfigurée et devrait fonctionner automatiquement
- Testez votre connexion internet
- Utilisez le bouton "Test API météo" dans l'interface

**Base de données d'aéroports vide**
- Vérifiez la présence d'`airports.csv`
- Téléchargez la base depuis [OurAirports](https://ourairports.com/data/)

**Erreurs d'export PDF**
```bash
pip install reportlab
```

### Logs et debug

Activez le mode debug en définissant la variable d'environnement:
```bash
export VFR_DEBUG=1
python main.py
```

## Contribution

### Développement

1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/amazing-feature`)
3. Commitez vos changements (`git commit -m 'Add amazing feature'`)
4. Push vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrez une Pull Request

### Standards de code

- Suivez PEP 8
- Documentez vos fonctions (docstrings)
- Ajoutez des tests pour les nouvelles fonctionnalités
- Utilisez des noms de variables explicites

### Structure des commits

```
type(scope): description

body (optionnel)

footer (optionnel)
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Fonctionnalités avancées

### Gestion automatique des arrêts carburant

Le système analyse automatiquement l'autonomie de l'aéronef et propose des arrêts de ravitaillement si nécessaire:

```python
# Le système vérifie automatiquement
if leg.fuel_left - reserve_fuel < 0:
    # Recherche du meilleur aéroport de ravitaillement
    refuel_airport = find_nearest_refuel_airport(current_position, aircraft)
```

### Correction météo en temps réel

Les calculs de vent utilisent la météo prédite au moment exact de passage:

- Récupération météo au milieu de chaque segment
- Interpolation temporelle précise
- Correction automatique des caps et vitesses sol

### Export professionnel

Les documents générés respectent les standards aéronautiques:

- Plans de vol conformes OACI
- Calculs de carburant détaillés
- Informations de sécurité incluses
- Formats prêts pour l'impression

## Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE.md](LICENSE.md) pour plus de détails.

## Équipe de développement

- **Antoine Gingras**
- **Matthew Meyer**
- **Richard Nguekam**
- **Gabriel Wong-Lapierre**

## Remerciements

- **École de technologie supérieure** - Cadre académique
- **NAV CANADA** - Documentation CFS
- **Tomorrow.io** - API météorologique
- **OurAirports** - Base de données d'aéroports
- **OpenSource Community** - Bibliothèques utilisées

## Support

Pour des questions ou problèmes:

1. Consultez la documentation dans `/docs`
2. Vérifiez les [Issues GitHub](../../issues)
3. Contactez l'équipe via le forum du cours

---

**Note**: Ce projet est développé dans un cadre éducatif. Utilisez-le avec discernement pour la planification de vols réels et vérifiez toujours vos calculs avec des sources officielles.

**Version**: 1.0.0  
**Dernière mise à jour**: Juin 2025
