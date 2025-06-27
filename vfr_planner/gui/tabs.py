"""
Onglets de l'interface graphique
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import folium
import webbrowser
import os
from typing import Dict, List, Any, Optional
import json

from .widgets import AirportSearchWidget, CustomWaypointDialog, add_tooltip

try:
    from .widgets import FilterPanel
except ImportError:
    # Fallback si FilterPanel n'est pas disponible
    print("Attention: FilterPanel non disponible")
    FilterPanel = None

from ..models.aircraft import Aircraft, AIRCRAFT_PRESETS
from ..models.itinerary import create_itinerary_from_gui
from ..calculations.navigation import calculate_distance, calculate_bearing

# Clé API météo intégrée
WEATHER_API_KEY = "CmIKizbzjlLBf8XngqoIAU271bBYNZbk"


class AircraftTab(ttk.Frame):
    """Onglet pour les informations d'aéronef"""

    def __init__(self, parent, main_window):
        """
        Initialise l'onglet AircraftTab.

        :param parent: Le widget parent.
        :param main_window: Référence à la fenêtre principale de l'application.
        """
        super().__init__(parent)
        self.main_window = main_window
        self.aircraft_entries = {}
        self.flight_entries = {}

        self.create_widgets()
        self.setup_defaults()

    def create_widgets(self):
        """
        Créer les widgets de l'onglet.

        Configure les différentes sections :
        - Sélection d'aéronef prédéfini
        - Informations de l'aéronef
        - Informations du vol
        - Boutons de gestion (sauvegarder, charger, réinitialiser)
        """
        # Frame principal avec scroll
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Sélection d'aéronef prédéfini
        preset_frame = ttk.LabelFrame(scrollable_frame, text="Aéronefs prédéfinis", padding=10)
        preset_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(preset_frame, text="Sélectionner un aéronef:").grid(row=0, column=0, sticky='w', padx=5, pady=3)
        self.preset_var = tk.StringVar()
        preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var,
                                    values=list(AIRCRAFT_PRESETS.keys()), state="readonly")
        preset_combo.grid(row=0, column=1, padx=5, pady=3, sticky='ew')
        preset_combo.bind('<<ComboboxSelected>>', self.on_preset_selected)

        ttk.Button(preset_frame, text="Charger",
                   command=self.load_preset).grid(row=0, column=2, padx=5, pady=3)

        preset_frame.grid_columnconfigure(1, weight=1)

        # Informations avion
        aircraft_group = ttk.LabelFrame(scrollable_frame, text="Informations de l'aéronef", padding=10)
        aircraft_group.pack(fill='x', padx=10, pady=5)

        aircraft_fields = [
            ("Immatriculation (ex: C-FXYZ):", "registration"),
            ("Type d'avion (ex: C172):", "aircraft_type"),
            ("Vitesse de croisière (kn):", "cruise_speed"),
            ("Consommation (GPH):", "fuel_burn"),
            ("Capacité réservoir (gal):", "fuel_capacity"),
            ("Poids à vide (lbs):", "empty_weight"),
            ("Charge utile max (lbs):", "max_payload"),
            ("Équipements:", "equipment")
        ]

        for i, (label, key) in enumerate(aircraft_fields):
            ttk.Label(aircraft_group, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=3)
            entry = ttk.Entry(aircraft_group, width=25)
            entry.grid(row=i, column=1, padx=5, pady=3, sticky='ew')
            self.aircraft_entries[key] = entry

            # Ajouter tooltips
            if key == "cruise_speed":
                add_tooltip(entry, "Vitesse vraie de croisière en nœuds")
            elif key == "fuel_burn":
                add_tooltip(entry, "Consommation en gallons par heure")
            elif key == "fuel_capacity":
                add_tooltip(entry, "Capacité totale du réservoir en gallons")

        aircraft_group.grid_columnconfigure(1, weight=1)

        # Informations vol
        flight_group = ttk.LabelFrame(scrollable_frame, text="Informations du vol", padding=10)
        flight_group.pack(fill='x', padx=10, pady=5)

        flight_fields = [
            ("Date (YYYY-MM-DD):", "date"),
            ("Heure de départ (HH:MM):", "departure_time"),
            ("Nombre de passagers:", "passengers"),
            ("Poids bagages (lbs):", "baggage_weight"),
            ("Nom du pilote:", "pilot_name"),
            ("Licence pilote:", "pilot_license"),
            ("Temps de réserve (min):", "reserve_time")
        ]

        for i, (label, key) in enumerate(flight_fields):
            ttk.Label(flight_group, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=3)
            entry = ttk.Entry(flight_group, width=25)
            entry.grid(row=i, column=1, padx=5, pady=3, sticky='ew')
            self.flight_entries[key] = entry

        flight_group.grid_columnconfigure(1, weight=1)

        # Boutons de gestion
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(button_frame, text="💾 Sauvegarder profil",
                   command=self.save_aircraft_profile).pack(side='left', padx=5)
        ttk.Button(button_frame, text="📁 Charger profil",
                   command=self.load_aircraft_profile).pack(side='left', padx=5)
        ttk.Button(button_frame, text="🔄 Réinitialiser",
                   command=self.clear_all).pack(side='left', padx=5)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def setup_defaults(self):
        """
        Configurer les valeurs par défaut pour certains champs de saisie.

        - Temps de réserve à 45 minutes
        - Vitesse de croisière à 110 kn
        - Consommation à 7.5 GPH
        - Capacité du réservoir à 40 gallons
        """
        self.flight_entries['reserve_time'].insert(0, "45")
        self.aircraft_entries['cruise_speed'].insert(0, "110")
        self.aircraft_entries['fuel_burn'].insert(0, "7.5")
        self.aircraft_entries['fuel_capacity'].insert(0, "40")

    def on_preset_selected(self, event=None):
        """
        Appelé quand un aéronef prédéfini est sélectionné dans la liste déroulante.

        Met à jour les champs du formulaire avec les données du preset sélectionné.

        :param event: Événement tkinter (optionnel)
        """
        # Mise à jour en temps réel lors de la sélection
        self.load_preset()

    def load_preset(self):
        """
        Charger un aéronef prédéfini.

        Récupère le preset sélectionné et remplit les champs du formulaire
        avec les valeurs correspondantes. Met à jour la barre de statut
        avec le nom de l'aéronef chargé.
        """
        preset_name = self.preset_var.get()
        if preset_name in AIRCRAFT_PRESETS:
            aircraft = AIRCRAFT_PRESETS[preset_name]

            # Remplir les champs
            self.aircraft_entries['registration'].delete(0, tk.END)
            self.aircraft_entries['registration'].insert(0, aircraft.registration)

            self.aircraft_entries['aircraft_type'].delete(0, tk.END)
            self.aircraft_entries['aircraft_type'].insert(0, aircraft.aircraft_type)

            self.aircraft_entries['cruise_speed'].delete(0, tk.END)
            self.aircraft_entries['cruise_speed'].insert(0, str(aircraft.cruise_speed))

            self.aircraft_entries['fuel_burn'].delete(0, tk.END)
            self.aircraft_entries['fuel_burn'].insert(0, str(aircraft.fuel_burn))

            self.aircraft_entries['fuel_capacity'].delete(0, tk.END)
            self.aircraft_entries['fuel_capacity'].insert(0, str(aircraft.fuel_capacity))

            self.aircraft_entries['empty_weight'].delete(0, tk.END)
            self.aircraft_entries['empty_weight'].insert(0, str(aircraft.empty_weight))

            self.aircraft_entries['max_payload'].delete(0, tk.END)
            self.aircraft_entries['max_payload'].insert(0, str(aircraft.max_payload))

            self.aircraft_entries['equipment'].delete(0, tk.END)
            self.aircraft_entries['equipment'].insert(0, aircraft.equipment)

            self.main_window.status_bar.set_status(f"Aéronef {preset_name} chargé")

    def get_aircraft_data(self) -> Dict[str, Any]:
        """
        Obtenir les données d'aéronef.

        Parcourt tous les champs d'entrée de l'aéronef et retourne
        un dictionnaire avec les clés correspondantes et leurs valeurs.

        :return: Dictionnaire des données d'aéronef.
        """
        return {key: entry.get() for key, entry in self.aircraft_entries.items()}

    def get_flight_data(self) -> Dict[str, Any]:
        """
        Obtenir les données de vol.

        Parcourt tous les champs d'entrée du vol et retourne
        un dictionnaire avec les clés correspondantes et leurs valeurs.

        :return: Dictionnaire des données de vol.
        """
        return {key: entry.get() for key, entry in self.flight_entries.items()}

    def clear_all(self):
        """
        Effacer tous les champs de saisie.

        Vide tous les champs des informations d'aéronef et de vol,
        puis réinitialise les valeurs par défaut.
        """
        for entry in self.aircraft_entries.values():
            entry.delete(0, tk.END)
        for entry in self.flight_entries.values():
            entry.delete(0, tk.END)
        self.setup_defaults()

    def save_aircraft_profile(self):
        """
        Sauvegarder le profil d'aéronef.

        Fonctionnalité placeholder pour sauvegarder un profil,
        affiche un message d'information pour l'instant.
        """
        try:
            # Obtenir les données actuelles de l'aéronef et du vol
            aircraft_data = self.get_aircraft_data()
            flight_data = self.get_flight_data()

            # Vérifier qu'il y a des données à sauvegarder
            if not any(aircraft_data.values()) and not any(flight_data.values()):
                messagebox.showwarning("Attention", "Aucune donnée à sauvegarder")
                return

            # Demander le nom du fichier de sauvegarde
            filename = filedialog.asksaveasfilename(
                title="Sauvegarder le profil d'aéronef",
                defaultextension=".json",
                filetypes=[
                    ("Profils d'aéronef", "*.json"),
                    ("Tous les fichiers", "*.*")
                ],
                initialdir=os.path.join(os.path.expanduser("~"), "Documents", "VFR_Planner", "Aircraft_Profiles")
            )

            if not filename:
                return

            # Créer le répertoire si nécessaire
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Préparer les données à sauvegarder
            profile_data = {
                'profile_info': {
                    'name': os.path.splitext(os.path.basename(filename))[0],
                    'created_at': self.main_window.root.tk.call('clock', 'format',
                                                                self.main_window.root.tk.call('clock', 'seconds'),
                                                                '-format', '%Y-%m-%d %H:%M:%S'),
                    'vfr_planner_version': getattr(self.main_window, '__version__', '1.0.0')
                },
                'aircraft': aircraft_data,
                'flight': flight_data
            }

            # Sauvegarder dans le fichier JSON
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)

            # Confirmation
            profile_name = os.path.splitext(os.path.basename(filename))[0]
            messagebox.showinfo("Succès", f"Profil d'aéronef '{profile_name}' sauvegardé avec succès")
            self.main_window.status_bar.set_status(f"Profil {profile_name} sauvegardé")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde du profil:\n{str(e)}")

    def load_aircraft_profile(self):
        """
        Charger un profil d'aéronef.

        Fonctionnalité placeholder pour charger un profil,
        affiche un message d'information pour l'instant.
        """
        try:
            # Sélectionner le fichier à charger
            filename = filedialog.askopenfilename(
                title="Charger un profil d'aéronef",
                filetypes=[
                    ("Profils d'aéronef", "*.json"),
                    ("Tous les fichiers", "*.*")
                ],
                initialdir=os.path.join(os.path.expanduser("~"), "Documents", "VFR_Planner", "Aircraft_Profiles")
            )

            if not filename:
                return

            # Charger les données depuis le fichier
            with open(filename, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)

            # Vérifier la structure du fichier
            if 'aircraft' not in profile_data and 'flight' not in profile_data:
                messagebox.showerror("Erreur", "Fichier de profil invalide")
                return

            # Effacer les champs actuels
            self.clear_all()

            # Charger les données d'aéronef
            aircraft_data = profile_data.get('aircraft', {})
            for key, value in aircraft_data.items():
                if key in self.aircraft_entries and value:
                    entry = self.aircraft_entries[key]
                    entry.delete(0, tk.END)
                    entry.insert(0, str(value))

            # Charger les données de vol
            flight_data = profile_data.get('flight', {})
            for key, value in flight_data.items():
                if key in self.flight_entries and value:
                    entry = self.flight_entries[key]
                    entry.delete(0, tk.END)
                    entry.insert(0, str(value))

            # Confirmation
            profile_name = profile_data.get('profile_info', {}).get('name',
                                                                    os.path.splitext(os.path.basename(filename))[0])
            messagebox.showinfo("Succès", f"Profil d'aéronef '{profile_name}' chargé avec succès")
            self.main_window.status_bar.set_status(f"Profil {profile_name} chargé")

            # Marquer le projet comme modifié
            if hasattr(self.main_window, 'mark_unsaved'):
                self.main_window.mark_unsaved()

        except FileNotFoundError:
            messagebox.showerror("Erreur", "Fichier de profil introuvable")
        except json.JSONDecodeError:
            messagebox.showerror("Erreur", "Fichier de profil corrompu ou invalide")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement du profil:\n{str(e)}")


class AirportsTab(ttk.Frame):
    """Onglet pour la sélection d'aéroports"""

    def __init__(self, parent, main_window):
        """
        Initialiser l'onglet de sélection d'aéroports.

        :param parent: Widget parent
        :param main_window: Référence vers la fenêtre principale
        """
        super().__init__(parent)
        self.main_window = main_window
        self.departure_airport = None
        self.destination_airport = None

        # Initialiser les attributs avant create_widgets
        self.departure_search = None
        self.destination_search = None
        self.filter_panel = None
        self.flight_info_text = None

        self.create_widgets()

    def create_widgets(self):
        """
        Créer les widgets de l'onglet.

        Initialise les différents panneaux, zones de recherche,
        boutons d'action et la zone d'informations de vol.
        """
        try:
            # Instructions
            instructions = ttk.Label(self,
                                     text="Recherchez vos aéroports par code ou nom. "
                                          "🔵=ICAO, 🟡=IATA, 🟢=Local/GPS",
                                     wraplength=600, justify='left')
            instructions.pack(pady=5, padx=10)

            # Frame principal
            main_frame = ttk.Frame(self)
            main_frame.pack(fill='both', expand=True, padx=10, pady=5)

            # Panneau de filtres (gauche)
            if FilterPanel:
                self.filter_panel = FilterPanel(main_frame, self.main_window.airport_db,
                                                self.on_filters_updated)
                self.filter_panel.pack(side='left', fill='y', padx=(0, 5))
            else:
                # Panneau de filtres simplifié si FilterPanel n'est pas disponible
                filter_frame = ttk.LabelFrame(main_frame, text="Filtres", padding=5)
                filter_frame.pack(side='left', fill='y', padx=(0, 5))
                ttk.Label(filter_frame, text="Filtres non disponibles").pack()
                self.filter_panel = None

            # Panneau principal (droite)
            selection_frame = ttk.Frame(main_frame)
            selection_frame.pack(side='right', fill='both', expand=True)

            # Aéroport de départ
            departure_frame = ttk.LabelFrame(selection_frame, text="Aéroport de départ", padding=10)
            departure_frame.pack(fill='x', pady=5)

            self.departure_search = AirportSearchWidget(departure_frame,
                                                        self.main_window.airport_db, "Départ:")
            self.departure_search.pack(fill='x')
            self.departure_search.set_callback(self.on_departure_selected)

            # Aéroport d'arrivée
            destination_frame = ttk.LabelFrame(selection_frame, text="Aéroport d'arrivée", padding=10)
            destination_frame.pack(fill='x', pady=5)

            self.destination_search = AirportSearchWidget(destination_frame,
                                                          self.main_window.airport_db, "Arrivée:")
            self.destination_search.pack(fill='x')
            self.destination_search.set_callback(self.on_destination_selected)

            # Boutons d'action
            button_frame = ttk.Frame(selection_frame)
            button_frame.pack(fill='x', pady=10)

            ttk.Button(button_frame, text="🔄 Inverser",
                       command=self.swap_airports).pack(side='left', padx=5)
            ttk.Button(button_frame, text="📍 Ajouter à l'itinéraire",
                       command=self.add_to_route).pack(side='left', padx=5)
            ttk.Button(button_frame, text="🗺️ Voir sur carte",
                       command=self.show_on_map).pack(side='left', padx=5)

            # Informations de vol
            info_frame = ttk.LabelFrame(selection_frame, text="Informations de vol", padding=10)
            info_frame.pack(fill='both', expand=True, pady=5)

            self.flight_info_text = tk.Text(info_frame, height=8, wrap='word')
            self.flight_info_text.pack(fill='both', expand=True)

        except Exception as e:
            print(f"Erreur création widgets AirportsTab: {e}")
            # Créer des widgets minimaux en cas d'erreur
            self.departure_search = None
            self.destination_search = None
            self.flight_info_text = None

    def on_filters_updated(self):
        """
        Appelé quand les filtres sont mis à jour.

        Réinitialise les recherches actuelles et met à jour la barre de statut
        avec le nombre d'aéroports filtrés.

        En cas d'erreur, affiche un message dans la console.
        """
        try:
            # Effacer les recherches en cours
            if self.departure_search:
                self.departure_search.clear()
            if self.destination_search:
                self.destination_search.clear()

            # Mettre à jour la barre d'état
            if hasattr(self.main_window, 'airport_db') and hasattr(self.main_window, 'status_bar'):
                stats = self.main_window.airport_db.get_filter_stats()
                self.main_window.status_bar.set_airports_count(stats['filtered'])
        except Exception as e:
            print(f"Erreur mise à jour filtres: {e}")

    def on_departure_selected(self, airport):
        """
        Callback appelé lors de la sélection de l'aéroport de départ.

        :param airport: dict contenant les données de l'aéroport sélectionné
        """
        self.departure_airport = airport
        self.update_flight_info()
        self.main_window.status_bar.set_status(f"Départ: {airport['icao']} - {airport['name']}")

    def on_destination_selected(self, airport):
        """
        Callback appelé lors de la sélection de l'aéroport d'arrivée.

        :param airport: dict contenant les données de l'aéroport sélectionné
        """
        self.destination_airport = airport
        self.update_flight_info()
        self.main_window.status_bar.set_status(f"Arrivée: {airport['icao']} - {airport['name']}")

    def update_flight_info(self):
        """
        Met à jour les informations de vol affichées.

        Calcule la distance, le cap magnétique, et estime le temps de vol
        en fonction de la vitesse de croisière.
        Met à jour la zone de texte avec ces informations.
        """
        if not (self.departure_airport and self.destination_airport and self.flight_info_text):
            return

        try:
            # Calculer distance et cap
            distance = calculate_distance(
                self.departure_airport['lat'], self.departure_airport['lon'],
                self.destination_airport['lat'], self.destination_airport['lon']
            )

            bearing = calculate_bearing(
                self.departure_airport['lat'], self.departure_airport['lon'],
                self.destination_airport['lat'], self.destination_airport['lon']
            )

            # Estimer temps de vol
            try:
                if hasattr(self.main_window, 'aircraft_tab'):
                    aircraft_data = self.main_window.aircraft_tab.get_aircraft_data()
                    cruise_speed = float(aircraft_data.get('cruise_speed', 110))
                else:
                    cruise_speed = 110
            except (ValueError, AttributeError):
                cruise_speed = 110

            flight_time = distance / cruise_speed * 60  # minutes

            info_text = f"""INFORMATIONS DE VOL DIRECT

    Départ: {self.departure_airport['icao']} - {self.departure_airport['name']}
            {self.departure_airport['city']}
            {self.departure_airport['lat']:.4f}°N, {abs(self.departure_airport['lon']):.4f}°W

    Arrivée: {self.destination_airport['icao']} - {self.destination_airport['name']}
             {self.destination_airport['city']}
             {self.destination_airport['lat']:.4f}°N, {abs(self.destination_airport['lon']):.4f}°W

    Distance directe: {distance:.1f} NM
    Cap magnétique: {bearing:.0f}°
    Temps de vol estimé: {flight_time:.0f} min ({flight_time / 60:.1f}h)
    Vitesse de croisière: {cruise_speed} kn

    Note: Calculs pour vol direct sans vent.
    Utilisez 'Plan de vol' pour calculs détaillés avec météo.
    """

            self.flight_info_text.delete('1.0', tk.END)
            self.flight_info_text.insert('1.0', info_text)

        except Exception as e:
            print(f"Erreur mise à jour infos vol: {e}")
            if self.flight_info_text:
                self.flight_info_text.delete('1.0', tk.END)
                self.flight_info_text.insert('1.0', f"Erreur calcul: {e}")

    def swap_airports(self):
        """
        Inverse les aéroports de départ et d'arrivée.

        Met à jour les champs de sélection et rafraîchit les informations de vol.
        Affiche un avertissement si les deux aéroports ne sont pas sélectionnés.
        """
        if (self.departure_airport and self.destination_airport and
                self.departure_search and self.destination_search):

            # Échanger
            temp = self.departure_airport
            self.departure_airport = self.destination_airport
            self.destination_airport = temp

            # Mettre à jour l'affichage
            self.departure_search.set_airport(self.departure_airport)
            self.destination_search.set_airport(self.destination_airport)

            self.update_flight_info()
            if hasattr(self.main_window, 'status_bar'):
                self.main_window.status_bar.set_status("Aéroports inversés")
        else:
            messagebox.showwarning("Attention", "Sélectionnez d'abord les deux aéroports")

    def add_to_route(self):
        """
        Ajoute les aéroports de départ et d'arrivée à l'itinéraire.

        Affiche un avertissement si les aéroports ne sont pas sélectionnés.
        Met à jour l'onglet itinéraire et la barre de statut.
        """
        if not (self.departure_airport and self.destination_airport):
            messagebox.showwarning("Attention", "Sélectionnez les aéroports de départ et d'arrivée")
            return

        try:
            # Ajouter à l'onglet itinéraire
            if hasattr(self.main_window, 'route_tab'):
                self.main_window.route_tab.clear_waypoints()
                self.main_window.route_tab.add_airport_waypoint(self.departure_airport)
                self.main_window.route_tab.add_airport_waypoint(self.destination_airport)

                if hasattr(self.main_window, 'status_bar'):
                    self.main_window.status_bar.set_status("Aéroports ajoutés à l'itinéraire")
        except Exception as e:
            print(f"Erreur ajout à l'itinéraire: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'ajout à l'itinéraire:\n{e}")

    def show_on_map(self):
        """
        Affiche les aéroports de départ et d'arrivée sur une carte interactive.

        Génère une carte Folium centrée entre les deux aéroports,
        avec marqueurs et ligne directe.
        Ouvre la carte dans le navigateur par défaut.
        Affiche un avertissement si les aéroports ne sont pas sélectionnés.
        """
        if not (self.departure_airport and self.destination_airport):
            messagebox.showwarning("Attention", "Sélectionnez d'abord les aéroports")
            return

        try:
            # Centre de la carte
            center_lat = (self.departure_airport['lat'] + self.destination_airport['lat']) / 2
            center_lon = (self.departure_airport['lon'] + self.destination_airport['lon']) / 2

            # Créer carte
            m = folium.Map(location=[center_lat, center_lon], zoom_start=7)

            # Marqueurs
            folium.Marker(
                [self.departure_airport['lat'], self.departure_airport['lon']],
                popup=f"DÉPART: {self.departure_airport['icao']}<br>{self.departure_airport['name']}",
                tooltip=f"Départ: {self.departure_airport['icao']}",
                icon=folium.Icon(color='green', icon='play')
            ).add_to(m)

            folium.Marker(
                [self.destination_airport['lat'], self.destination_airport['lon']],
                popup=f"ARRIVÉE: {self.destination_airport['icao']}<br>{self.destination_airport['name']}",
                tooltip=f"Arrivée: {self.destination_airport['icao']}",
                icon=folium.Icon(color='red', icon='stop')
            ).add_to(m)

            # Ligne directe
            folium.PolyLine(
                [[self.departure_airport['lat'], self.departure_airport['lon']],
                 [self.destination_airport['lat'], self.destination_airport['lon']]],
                color='blue', weight=3, opacity=0.7,
                popup="Route directe"
            ).add_to(m)

            # Sauvegarder et ouvrir
            map_file = "airports_map.html"
            m.save(map_file)
            webbrowser.open(f"file://{os.path.abspath(map_file)}")

            if hasattr(self.main_window, 'status_bar'):
                self.main_window.status_bar.set_status("Carte ouverte dans le navigateur")

        except Exception as e:
            print(f"Erreur création carte: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de la création de la carte:\n{e}")


class RouteTab(ttk.Frame):
    """Onglet pour l'itinéraire détaillé"""

    def __init__(self, parent, main_window):
        """
        Initialiser l'onglet itinéraire.

        :param parent: widget parent
        :param main_window: fenêtre principale de l'application
        """
        super().__init__(parent)
        self.main_window = main_window
        self.waypoints = []

        self.create_widgets()

    def create_widgets(self):
        """Créer les widgets de l'onglet"""
        # Frame principal
        main_frame = ttk.PanedWindow(self, orient='horizontal')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Panneau gauche - Liste des waypoints
        left_frame = ttk.Frame(main_frame)
        main_frame.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Itinéraire (waypoints):").pack(anchor='w', pady=5)

        # Listbox avec scrollbar
        listbox_frame = ttk.Frame(left_frame)
        listbox_frame.pack(fill='both', expand=True, pady=5)

        self.waypoint_listbox = tk.Listbox(listbox_frame, height=15)
        self.waypoint_listbox.pack(side='left', fill='both', expand=True)
        self.waypoint_listbox.bind('<<ListboxSelect>>', self.on_waypoint_select)

        wp_scrollbar = ttk.Scrollbar(listbox_frame, orient='vertical')
        wp_scrollbar.pack(side='right', fill='y')
        self.waypoint_listbox.config(yscrollcommand=wp_scrollbar.set)
        wp_scrollbar.config(command=self.waypoint_listbox.yview)

        # Boutons de gestion waypoints
        wp_button_frame = ttk.Frame(left_frame)
        wp_button_frame.pack(fill='x', pady=5)

        ttk.Button(wp_button_frame, text="➕ Ajouter",
                   command=self.add_custom_waypoint).pack(side='left', padx=2)
        ttk.Button(wp_button_frame, text="🗑️ Supprimer",
                   command=self.remove_waypoint).pack(side='left', padx=2)
        ttk.Button(wp_button_frame, text="⬆️ Monter",
                   command=self.move_waypoint_up).pack(side='left', padx=2)
        ttk.Button(wp_button_frame, text="⬇️ Descendre",
                   command=self.move_waypoint_down).pack(side='left', padx=2)

        # Panneau droit - Détails du waypoint
        right_frame = ttk.Frame(main_frame)
        main_frame.add(right_frame, weight=1)

        details_frame = ttk.LabelFrame(right_frame, text="Détails du waypoint", padding=10)
        details_frame.pack(fill='both', expand=True, pady=5)

        self.waypoint_detail_text = tk.Text(details_frame, wrap='word')
        self.waypoint_detail_text.pack(fill='both', expand=True)

    def add_airport_waypoint(self, airport: Dict[str, Any]):
        """
        Ajouter un aéroport comme waypoint.

        :param airport: dictionnaire contenant les informations de l'aéroport
        """
        waypoint = {
            'name': airport['icao'],
            'lat': airport['lat'],
            'lon': airport['lon'],
            'type': 'airport',
            'info': airport
        }
        self.waypoints.append(waypoint)
        self.update_waypoint_list()

    def add_custom_waypoint(self):
        """
        Ajouter un waypoint personnalisé via une boîte de dialogue.
        """
        dialog = CustomWaypointDialog(self, self.main_window.airport_db)
        if dialog.result:
            self.waypoints.append(dialog.result)
            self.update_waypoint_list()

    def remove_waypoint(self):
        """
        Supprimer le waypoint sélectionné dans la liste.
        """
        selection = self.waypoint_listbox.curselection()
        if selection:
            index = selection[0]
            del self.waypoints[index]
            self.update_waypoint_list()

    def move_waypoint_up(self):
        """
        Déplacer le waypoint sélectionné vers le haut dans la liste.
        """
        selection = self.waypoint_listbox.curselection()
        if selection and selection[0] > 0:
            index = selection[0]
            self.waypoints[index], self.waypoints[index - 1] = \
                self.waypoints[index - 1], self.waypoints[index]
            self.update_waypoint_list()
            self.waypoint_listbox.selection_set(index - 1)

    def move_waypoint_down(self):
        """
        Déplacer le waypoint sélectionné vers le bas dans la liste.
        """
        selection = self.waypoint_listbox.curselection()
        if selection and selection[0] < len(self.waypoints) - 1:
            index = selection[0]
            self.waypoints[index], self.waypoints[index + 1] = \
                self.waypoints[index + 1], self.waypoints[index]
            self.update_waypoint_list()
            self.waypoint_listbox.selection_set(index + 1)

    def clear_waypoints(self):
        """
        Effacer tous les waypoints de la liste.
        """
        self.waypoints.clear()
        self.update_waypoint_list()

    def update_waypoint_list(self):
        """
        Mettre à jour l'affichage des waypoints dans la liste.
        """
        self.waypoint_listbox.delete(0, tk.END)
        for i, wp in enumerate(self.waypoints):
            display_text = f"{i + 1}. {wp['name']} ({wp['lat']:.4f}, {wp['lon']:.4f})"
            if wp.get('type') == 'airport':
                display_text += " ✈️"
            self.waypoint_listbox.insert(tk.END, display_text)

    def on_waypoint_select(self, event):
        """
        Afficher les détails du waypoint sélectionné dans le panneau droit.

        :param event: événement Tkinter lié à la sélection dans la liste
        """
        selection = self.waypoint_listbox.curselection()
        if selection:
            wp = self.waypoints[selection[0]]
            details = f"Waypoint: {wp['name']}\n"
            details += f"Latitude: {wp['lat']:.6f}°\n"
            details += f"Longitude: {wp['lon']:.6f}°\n"
            details += f"Type: {wp.get('type', 'custom')}\n"

            if wp.get('info'):
                info = wp['info']
                details += f"\nInformations aéroport:\n"
                details += f"Nom complet: {info.get('name', 'N/A')}\n"
                details += f"Ville: {info.get('city', 'N/A')}\n"
                details += f"Pays: {info.get('country', 'N/A')}\n"
                details += f"Type: {info.get('type', 'N/A')}\n"

            self.waypoint_detail_text.delete('1.0', tk.END)
            self.waypoint_detail_text.insert('1.0', details)

    def get_waypoints(self) -> List[Dict[str, Any]]:
        """
        Obtenir la liste des waypoints actuels.

        :return: copie de la liste des waypoints
        """
        return self.waypoints.copy()


class PlanTab(ttk.Frame):
    """Onglet pour le plan de vol final avec timing météo corrigé"""

    def __init__(self, parent, main_window):
        """
        Initialiser l'onglet Plan de vol.

        :param parent: widget parent
        :param main_window: fenêtre principale de l'application
        """
        super().__init__(parent)
        self.main_window = main_window
        self.calculated_itinerary = None

        self.create_widgets()

    def create_widgets(self):
        """Créer les widgets de l'onglet"""
        # Frame principal
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Configuration et boutons
        config_frame = ttk.LabelFrame(main_frame, text="Configuration météo", padding=10)
        config_frame.pack(fill='x', pady=5)

        # Info sur l'API intégrée
        api_info = ttk.Label(config_frame,
                             text="✅ API météo Tomorrow.io configurée automatiquement",
                             foreground='green')
        api_info.pack(pady=5)

        # Boutons de configuration/test
        button_config_frame = ttk.Frame(config_frame)
        button_config_frame.pack(fill='x', pady=5)

        ttk.Button(button_config_frame, text="🧪 Tester API météo",
                   command=self.test_api).pack(side='left', padx=5)

        # Boutons de génération
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=5)

        ttk.Button(button_frame, text="🧮 Calculer itinéraire",
                   command=self.calculate_route).pack(side='left', padx=5)
        ttk.Button(button_frame, text="📊 Export Excel",
                   command=self.export_excel).pack(side='left', padx=5)
        ttk.Button(button_frame, text="📄 Export PDF",
                   command=self.export_pdf).pack(side='left', padx=5)
        ttk.Button(button_frame, text="🗺️ Carte interactive",
                   command=self.show_map).pack(side='left', padx=5)

        # Zone d'affichage du plan
        plan_frame = ttk.LabelFrame(main_frame, text="Plan de vol", padding=10)
        plan_frame.pack(fill='both', expand=True, pady=5)

        # Text widget avec scrollbar
        text_frame = ttk.Frame(plan_frame)
        text_frame.pack(fill='both', expand=True)

        self.plan_text = tk.Text(text_frame, wrap='none', font=('Courier', 9))
        self.plan_text.pack(side='left', fill='both', expand=True)

        plan_scrollbar_v = ttk.Scrollbar(text_frame, orient='vertical', command=self.plan_text.yview)
        plan_scrollbar_v.pack(side='right', fill='y')
        self.plan_text.configure(yscrollcommand=plan_scrollbar_v.set)

        plan_scrollbar_h = ttk.Scrollbar(plan_frame, orient='horizontal', command=self.plan_text.xview)
        plan_scrollbar_h.pack(side='bottom', fill='x')
        self.plan_text.configure(xscrollcommand=plan_scrollbar_h.set)

    def test_api(self):
        """
        Tester la clé API météo Tomorrow.io.

        Cette méthode effectue un test simple en demandant la météo à un point fixe (Montréal)
        et affiche un message indiquant si la clé API est valide ou non.

        Affiche un message d'erreur en cas d'échec.

        :raises Exception: si la récupération météo retourne une erreur
        """
        try:
            from ..calculations.weather import WeatherService
            from ..models.waypoint import Waypoint
            import datetime

            # Test avec un point connu
            weather_service = WeatherService(WEATHER_API_KEY)
            test_waypoint = Waypoint(45.458, -73.749, "CYUL")  # Montréal

            weather_data = weather_service.get_weather_for_point(
                test_waypoint, datetime.datetime.now()
            )

            if 'error' in weather_data:
                raise Exception(weather_data['error'])

            # API fonctionne
            self.main_window.status_bar.set_api_status(True, True)
            messagebox.showinfo("Succès",
                                f"API météo fonctionnelle!\n\n"
                                f"Test à Montréal:\n"
                                f"Vent: {weather_data['wind_direction']:.0f}°/{weather_data['wind_speed']:.0f}kn\n"
                                f"Température: {weather_data['temperature']:.0f}°C")

        except Exception as e:
            self.main_window.status_bar.set_api_status(True, False)
            messagebox.showerror("Erreur API", f"Test échoué:\n{e}")

    def calculate_route(self):
        """
        Calculer l'itinéraire complet avec timing météo corrigé.

        Cette méthode récupère les waypoints, les données de l'aéronef et du vol,
        puis appelle la fonction `create_itinerary_from_gui` avec la clé API météo.
        Elle affiche ensuite le plan de vol détaillé avec les informations de timing
        et met à jour la barre de statut.

        Affiche une alerte si moins de 2 waypoints sont présents.
        Gère les exceptions en affichant un message d'erreur.

        :return: None
        """
        # Vérifier les prérequis
        waypoints = self.main_window.route_tab.get_waypoints()
        if len(waypoints) < 2:
            messagebox.showwarning("Attention", "Au moins 2 waypoints requis")
            return

        try:
            # Préparer les données aéronef
            aircraft_data = self.main_window.aircraft_tab.get_aircraft_data()
            flight_data = self.main_window.aircraft_tab.get_flight_data()

            print(f"🛩️ Données aéronef: {aircraft_data}")
            print(f"✈️ Données vol: {flight_data}")

            aircraft_params = {
                'tas': float(aircraft_data.get('cruise_speed', 110)),
                'fuel_burn': float(aircraft_data.get('fuel_burn', 7.5)),
                'fuel_capacity': float(aircraft_data.get('fuel_capacity', 40)),
                'registration': aircraft_data.get('registration', ''),
                'aircraft_type': aircraft_data.get('aircraft_type', '')
            }

            # CORRECTION: Inclure date et heure de départ dans flight_params
            flight_params = {
                'date': flight_data.get('date', ''),
                'departure_time': flight_data.get('departure_time', ''),  # Utilise 'departure_time' au lieu de 'time'
                'pilot_name': flight_data.get('pilot_name', ''),
                'reserve_time': float(flight_data.get('reserve_time', 45)),
                'passengers': flight_data.get('passengers', ''),
                'baggage_weight': flight_data.get('baggage_weight', ''),
                'pilot_license': flight_data.get('pilot_license', '')
            }

            print(f"📅 Flight params avec timing: {flight_params}")

            # Vérifier que nous avons au moins une date et heure
            if not flight_params['date'] and not flight_params['departure_time']:
                print("⚠️ Pas de date/heure spécifiée, utilisation valeurs par défaut")
                from datetime import datetime
                today = datetime.now()
                flight_params['date'] = today.strftime('%Y-%m-%d')
                flight_params['departure_time'] = '10:00'
                print(f"📅 Valeurs par défaut: {flight_params['date']} à {flight_params['departure_time']}")

            # Calculer l'itinéraire avec clé API intégrée et timing corrigé
            self.main_window.status_bar.set_status("Calcul en cours avec météo temps réel...")
            self.main_window.root.update()

            itinerary = create_itinerary_from_gui(
                waypoints=waypoints,
                aircraft_params=aircraft_params,
                flight_params=flight_params,  # Contient maintenant date et departure_time
                api_key=WEATHER_API_KEY
            )

            # Stocker pour l'export
            self.calculated_itinerary = itinerary

            # Afficher le résultat avec info timing
            self.display_itinerary_with_timing(itinerary)

            summary = itinerary.get_summary()

            # Calculer heure d'arrivée
            if itinerary.start_time and summary['total_time']:
                import datetime
                eta = itinerary.start_time + datetime.timedelta(minutes=summary['total_time'])
                eta_local = eta.strftime('%H:%M')
                timing_info = f"Départ: {itinerary.start_time.strftime('%H:%M')} UTC, Arrivée: {eta_local}"
            else:
                timing_info = "Timing non disponible"

            self.main_window.status_bar.set_status(
                f"✅ Calculé: {len(itinerary.legs)} segments, {summary['total_time']:.0f} min - {timing_info}"
            )

        except Exception as e:
            print(f"❌ Erreur calcul: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur lors du calcul:\n{e}")
            self.main_window.status_bar.set_status("Erreur de calcul")

    def display_itinerary_with_timing(self, itinerary):
        """
        Afficher l'itinéraire calculé avec informations de timing détaillées.

        Affiche dans le widget texte un plan de vol formaté avec :
        - détails avion et pilote,
        - heure de départ et arrivée (UTC),
        - tableau détaillé des legs avec timing météo,
        - analyse carburant complète,
        - notes sur la météo et la navigation.

        :param itinerary: objet contenant les données de l'itinéraire calculé
        :type itinerary: Itinerary
        :return: None
        """
        summary = itinerary.get_summary()
        fuel_analysis = itinerary.get_fuel_analysis()

        plan_text = "PLAN DE VOL VFR - CALCUL AVEC TIMING MÉTÉO CORRIGÉ\n"
        plan_text += "=" * 80 + "\n\n"

        # Informations générales avec timing
        aircraft_data = self.main_window.aircraft_tab.get_aircraft_data()
        flight_data = self.main_window.aircraft_tab.get_flight_data()

        plan_text += f"Avion: {aircraft_data.get('registration', 'N/A')} ({aircraft_data.get('aircraft_type', 'N/A')})\n"
        plan_text += f"Pilote: {flight_data.get('pilot_name', 'N/A')}\n"
        plan_text += f"Date: {flight_data.get('date', 'N/A')}\n"
        plan_text += f"Heure départ: {flight_data.get('departure_time', 'N/A')}\n"

        # Afficher le timing de départ calculé
        if itinerary.start_time:
            plan_text += f"Heure départ UTC: {itinerary.start_time.strftime('%Y-%m-%d %H:%M')} UTC\n"

            # Calculer heure d'arrivée
            if summary['total_time']:
                import datetime
                eta_utc = itinerary.start_time + datetime.timedelta(minutes=summary['total_time'])
                plan_text += f"Heure arrivée UTC: {eta_utc.strftime('%H:%M')} UTC\n"

        plan_text += f"TAS: {aircraft_data.get('cruise_speed', 'N/A')} kn\n"
        plan_text += f"Consommation: {aircraft_data.get('fuel_burn', 'N/A')} GPH\n\n"

        # En-tête tableau avec colonnes timing
        plan_text += "LEG FROM     TO       DIST  TC  MH  WIND      GS  TIME  FUEL_LEG FUEL_TOT FUEL_LEFT  MÉTÉO_HEURE\n"
        plan_text += "-" * 95 + "\n"

        # Legs avec info timing météo
        for i, leg in enumerate(itinerary.legs):
            leg_dict = leg.to_dict()

            plan_text += f"{i + 1:2d}  {leg_dict['Starting WP'][:7]:7s} {leg_dict['Ending WP'][:7]:7s} "
            plan_text += f"{leg_dict['Distance (NM)']:5.1f} {leg_dict['True course (deg)']:3.0f} "
            plan_text += f"{leg_dict['Magnetic heading (deg)']:3.0f} {leg_dict['Wind Direction (deg)']:3.0f}°/{leg_dict['Wind Speed (kn)']:2.0f}kn "
            plan_text += f"{leg_dict['Groundspeed (kn)']:3.0f} {leg_dict['Leg time (min)']:4.0f} "
            plan_text += f"{leg_dict['Fuel burn leg (gal)']:7.1f} {leg_dict['Fuel burn tot (gal)']:7.1f} "
            plan_text += f"{leg_dict['Fuel left (gal)']:8.1f}  "

            # Ajouter info timing météo
            weather_time = leg_dict.get('Time weather', 'N/A')
            if weather_time and weather_time != 'N/A':
                plan_text += f"{weather_time[:5]}"  # Afficher HH:MM seulement
            else:
                plan_text += "N/A  "

            plan_text += "\n"

        # Totaux
        plan_text += "-" * 95 + "\n"
        plan_text += f"TOTAUX:              {summary['total_distance']:5.1f}                   "
        plan_text += f"{summary['total_time']:4.0f} {summary['total_fuel']:16.1f}\n\n"

        # Section timing détaillée
        plan_text += f"INFORMATIONS DE TIMING:\n"
        if itinerary.start_time:
            plan_text += f"Heure départ configurée: {itinerary.start_time.strftime('%Y-%m-%d %H:%M UTC')}\n"

            # Afficher timing de chaque leg
            current_time = itinerary.start_time
            plan_text += f"\nTiming des segments:\n"
            for i, leg in enumerate(itinerary.legs):
                leg_dict = leg.to_dict()
                eta = current_time + datetime.timedelta(minutes=leg_dict['Leg time (min)'])
                plan_text += f"  Leg {i + 1}: {current_time.strftime('%H:%M')} → {eta.strftime('%H:%M')} "
                plan_text += f"(météo au milieu: {leg_dict.get('Time weather', 'N/A')[:5]})\n"
                current_time = eta
        else:
            plan_text += f"Timing non configuré\n"

        # Analyse carburant
        plan_text += f"\nANALYSE CARBURANT:\n"
        plan_text += f"Temps total: {summary['total_time'] / 60:.1f}h ({summary['total_time']:.0f} min)\n"
        plan_text += f"Carburant route: {fuel_analysis['route_fuel']:.1f} gal\n"
        plan_text += f"Carburant réserve: {fuel_analysis['reserve_fuel']:.1f} gal\n"
        plan_text += f"Total requis: {fuel_analysis['total_required']:.1f} gal\n"
        plan_text += f"Capacité avion: {fuel_analysis['aircraft_capacity']:.1f} gal\n"

        if fuel_analysis['is_sufficient']:
            plan_text += f"✅ Carburant suffisant (marge: {fuel_analysis['remaining']:.1f} gal)\n"
        else:
            plan_text += f"⚠️ CARBURANT INSUFFISANT (déficit: {-fuel_analysis['remaining']:.1f} gal)\n"
            plan_text += "   Ajoutez des arrêts de ravitaillement!\n"

        plan_text += f"\n📊 Météo: Tomorrow.io API (timing corrigé - météo au milieu des legs)\n"
        plan_text += f"🧭 Navigation: Calculs précis avec vent\n"
        plan_text += f"🕐 Timing: Heure utilisateur respectée, météo interpolée\n"

        # Afficher
        self.plan_text.delete('1.0', tk.END)
        self.plan_text.insert('1.0', plan_text)

    def display_itinerary(self, itinerary):
        """
        Afficher l'itinéraire calculé (méthode legacy).

        Cette méthode appelle simplement `display_itinerary_with_timing` pour afficher
        l'itinéraire avec les informations de timing.

        :param itinerary: Objet représentant l'itinéraire calculé.
        :type itinerary: Itinerary
        :return: None
        """
        self.display_itinerary_with_timing(itinerary)

    def export_excel(self):
        """
        Exporter l'itinéraire calculé vers un fichier Excel.

        Ouvre une boîte de dialogue pour choisir le fichier de destination.
        Utilise la fonction `export_to_excel` pour créer le fichier Excel.
        Affiche un message d'erreur si aucun itinéraire n'a été calculé
        ou si une erreur survient lors de l'export.

        :return: None
        """
        if not self.calculated_itinerary:
            messagebox.showwarning("Attention", "Calculez d'abord l'itinéraire")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Exporter plan de vol Excel"
        )

        if filename:
            try:
                from ..export.excel_export import export_to_excel
                flight_data, legs_data = self.calculated_itinerary.get_flight_plan_data()
                export_to_excel(flight_data, legs_data, filename)

                messagebox.showinfo("Succès", f"Plan exporté vers:\n{filename}")
                self.main_window.status_bar.set_status(f"Export Excel: {filename}")

            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur export Excel:\n{e}")

    def export_pdf(self):
        """
        Exporter l'itinéraire calculé vers un fichier PDF.

        Ouvre une boîte de dialogue pour choisir le fichier de destination.
        Utilise la fonction `export_to_pdf` pour créer le fichier PDF.
        Affiche un message d'erreur si aucun itinéraire n'a été calculé
        ou si une erreur survient lors de l'export.

        :return: None
        """
        if not self.calculated_itinerary:
            messagebox.showwarning("Attention", "Calculez d'abord l'itinéraire")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Exporter plan de vol PDF"
        )

        if filename:
            try:
                from ..export.pdf_export import export_to_pdf
                flight_data, legs_data = self.calculated_itinerary.get_flight_plan_data()
                export_to_pdf(flight_data, legs_data, filename)

                messagebox.showinfo("Succès", f"Plan exporté vers:\n{filename}")
                self.main_window.status_bar.set_status(f"Export PDF: {filename}")

            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur export PDF:\n{e}")

    def show_map(self):
        """
        Afficher la carte interactive du plan de vol.

        Récupère les waypoints de l'itinéraire, crée une carte centrée,
        ajoute des marqueurs pour chaque waypoint et trace la route entre eux.
        Sauvegarde la carte en HTML et l'ouvre dans le navigateur par défaut.

        Affiche un avertissement si aucun waypoint n'est défini
        et un message d'erreur en cas de problème lors de la création de la carte.

        :return: None
        """
        waypoints = self.main_window.route_tab.get_waypoints()
        if not waypoints:
            messagebox.showwarning("Attention", "Aucun waypoint défini")
            return

        try:
            # Centre de la carte
            center_lat = sum(wp['lat'] for wp in waypoints) / len(waypoints)
            center_lon = sum(wp['lon'] for wp in waypoints) / len(waypoints)

            m = folium.Map(location=[center_lat, center_lon], zoom_start=8)

            # Ajouter waypoints
            for i, wp in enumerate(waypoints):
                color = 'green' if i == 0 else 'red' if i == len(waypoints) - 1 else 'blue'
                icon = 'play' if i == 0 else 'stop' if i == len(waypoints) - 1 else 'info-sign'

                folium.Marker(
                    [wp['lat'], wp['lon']],
                    popup=f"WP{i + 1}: {wp['name']}",
                    tooltip=f"#{i + 1}: {wp['name']}",
                    icon=folium.Icon(color=color, icon=icon)
                ).add_to(m)

            # Route
            if len(waypoints) > 1:
                coords = [[wp['lat'], wp['lon']] for wp in waypoints]
                folium.PolyLine(coords, color='red', weight=3, opacity=0.8).add_to(m)

            # Sauvegarder et ouvrir
            map_file = "flight_route.html"
            m.save(map_file)
            webbrowser.open(f"file://{os.path.abspath(map_file)}")
            self.main_window.status_bar.set_status("Carte interactive ouverte")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur création carte:\n{e}")
