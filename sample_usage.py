"""
Exemple d'utilisation du module d'exportation de plan de vol VFR
Projet MGA802 - Outil de planification de vol VFR

Ce script démontre comment utiliser le module flight_plan_export avec
votre structure de code existante.
"""

import datetime
import pandas as pd
from itinerary.itinerary import Itinerary
from flight_plan_export import FlightPlanExporter, export_flight_plan


def create_sample_flight():
    """
    Crée un vol d'exemple de Montréal (CYUL) à Québec (CYQB)
    avec un arrêt à Trois-Rivières (CYRQ).
    """
    # Créer un itinéraire
    flight = Itinerary()

    # Vous devrez avoir un DataFrame avec les données d'aéroports
    # Pour cet exemple, nous simulons les données
    airport_data = pd.DataFrame({
        'lat': [45.4706, 46.7911, 46.7918],
        'lon': [-73.7408, -71.3933, -72.6794]
    }, index=['CYUL', 'CYRQ', 'CYQB'])

    # Ajouter les aéroports au vol
    flight.add_airport('CYUL', airport_data, start=True)  # Montréal-Trudeau
    flight.add_airport('CYRQ', airport_data, start=False)  # Trois-Rivières
    flight.add_airport('CYQB', airport_data, start=False)  # Québec

    # Vous pouvez aussi ajouter des waypoints personnalisés
    # flight.add_waypoint(45.5, -73.0, "Custom Waypoint")

    return flight


def export_complete_flight_plan():
    """
    Exemple complet d'exportation d'un plan de vol.
    """
    print("=== Création du plan de vol VFR ===")

    # 1. Créer l'itinéraire
    flight = create_sample_flight()

    # 2. Configurer les informations de l'aéronef
    aircraft_info = {
        'aircraft_id': 'C-GXYZ',
        'aircraft_type': 'Cessna 172',
        'tas': 100,  # True Airspeed en noeuds
        'fuel_capacity': 56,  # Capacité totale en gallons
        'burn_rate': 6.7,  # Consommation en gallons/heure
        'equipment': 'GPS, Transponder Mode C'
    }

    # 3. Configurer les informations du vol
    flight_info = {
        'pilot_name': 'Jean Pilote',
        'departure_time': datetime.datetime(2025, 6, 20, 14, 0),  # 14h00 UTC
        'fuel_on_board': 45.0,  # Carburant à bord en gallons
        'passengers': 2,
        'alternate_airport': 'CYTR',
        'remarks': 'Vol de navigation VFR'
    }

    # 4. Créer l'exportateur et configurer
    exporter = FlightPlanExporter(flight)
    exporter.set_aircraft_info(**aircraft_info)
    exporter.set_flight_info(**flight_info)

    # 5. Exporter vers Excel
    filename = f"VFR_Flight_Plan_{datetime.date.today().strftime('%Y%m%d')}.xlsx"
    exporter.export_to_excel(filename)

    # 6. Obtenir un résumé en DataFrame
    summary = exporter.export_summary_dataframe()
    print("\n=== Résumé du plan de vol ===")
    print(summary)

    # 7. Afficher quelques statistiques
    total_distance = summary['Distance_NM'].sum()
    total_time = summary['Cumulative_Time'].iloc[-1]
    total_fuel = summary['Fuel_Used_gal'].sum()

    print(f"\n=== Statistiques du vol ===")
    print(f"Distance totale: {total_distance:.1f} NM")
    print(f"Temps total estimé: {total_time:.0f} minutes ({total_time / 60:.1f} heures)")
    print(f"Carburant total requis: {total_fuel:.1f} gallons")
    print(f"Carburant restant à l'arrivée: {flight_info['fuel_on_board'] - total_fuel:.1f} gallons")

    return exporter, summary


def export_using_utility_function():
    """
    Exemple d'utilisation de la fonction utilitaire simplifiée.
    """
    print("\n=== Utilisation de la fonction utilitaire ===")

    # Créer l'itinéraire
    flight = create_sample_flight()

    # Utiliser la fonction utilitaire
    summary = export_flight_plan(
        itinerary=flight,
        filename="VFR_Plan_Utility.xlsx",
        aircraft_info={
            'aircraft_id': 'C-GABCD',
            'aircraft_type': 'Piper Cherokee',
            'tas': 95,
            'fuel_capacity': 50,
            'burn_rate': 7.2
        },
        flight_info={
            'pilot_name': 'Marie Aviatrice',
            'departure_time': datetime.datetime(2025, 6, 22, 10, 30),
            'fuel_on_board': 42.0,
            'passengers': 1
        }
    )

    print("Plan de vol exporté avec succès!")
    print(summary[['From', 'To', 'Distance_NM', 'ETE_minutes', 'Fuel_Used_gal']])


def integrate_with_existing_code():
    """
    Montre comment intégrer avec votre code existant.
    """
    print("\n=== Intégration avec le code existant ===")

    # Utiliser votre classe Itinerary existante
    flight = Itinerary()

    # Supposons que vous avez déjà chargé des waypoints
    # flight.load_waypoints("my_waypoints.csv")

    # Ou ajouté manuellement des waypoints
    flight.add_waypoint(45.4706, -73.7408, "CYUL Montreal")
    flight.add_waypoint(46.7911, -71.3933, "CYQB Quebec")

    # Votre code existant pour calculer les legs
    flight.create_legs()

    # Utiliser le nouvel exportateur
    exporter = FlightPlanExporter(flight)

    # Configuration minimale
    exporter.set_aircraft_info(
        aircraft_id="C-TEST",
        aircraft_type="Test Aircraft",
        tas=100,
        fuel_capacity=50,
        burn_rate=6.5
    )

    exporter.set_flight_info(
        pilot_name="Pilote Test",
        departure_time=datetime.datetime.now(),
        fuel_on_board=40.0,
        passengers=1
    )

    # Exporter
    exporter.export_to_excel("Test_Flight_Plan.xlsx")
    print("Plan de vol de test exporté!")


if __name__ == "__main__":
    """
    Point d'entrée principal - exécute tous les exemples.
    """
    try:
        # Exemple complet
        exporter, summary = export_complete_flight_plan()

        # Exemple avec fonction utilitaire
        export_using_utility_function()

        # Exemple d'intégration
        integrate_with_existing_code()

        print("\n=== Tous les exemples terminés avec succès! ===")
        print("Vérifiez les fichiers Excel générés dans le répertoire courant.")

    except Exception as e:
        print(f"Erreur lors de l'exécution: {e}")
        print("Assurez-vous d'avoir installé les dépendances: pip install pandas openpyxl")

# Instructions d'installation et d'utilisation
INSTALLATION_INSTRUCTIONS = """
=== Instructions d'installation ===

1. Installer les dépendances requises:
   pip install pandas openpyxl

2. Placer le fichier flight_plan_export.py dans votre projet

3. Importer et utiliser:
   from flight_plan_export import FlightPlanExporter

=== Structure des fichiers recommandée ===
votre_projet/
├── itinerary/
│   ├── __init__.py
│   ├── itinerary.py
│   ├── legs.py
│   ├── waypoints.py
│   └── data_retrieval.py
├── flight_plan_export.py      # Nouveau module
├── example_usage.py           # Ce fichier d'exemple
└── main.py                    # Votre programme principal

=== Fonctionnalités du module ===

✓ Export Excel au format VFR Navigation Log standard
✓ Calculs automatiques de navigation (TC, TH, MH, GS, ETE)
✓ Gestion du carburant et temps cumulatifs
✓ Section d'informations météorologiques
✓ Formatage professionnel avec bordures et couleurs
✓ Compatible avec votre structure de code existante
✓ Fonction utilitaire pour usage simplifié
"""

if __name__ == "__main__":
    print(INSTALLATION_INSTRUCTIONS)