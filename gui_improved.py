import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import folium
import webbrowser
import os
from typing import List, Dict, Optional, Tuple
import math
from datetime import datetime
from flight_plan_generator import *



class AirportDatabase:
    """Gestionnaire de la base de données d'aéroports"""

    def __init__(self, csv_path: str = "data/ressources/csv/airports.csv"):
        self.airports_df = None
        self.filtered_airports = None
        self.current_filters = {
            'countries': [],  # Vide = tous les pays
            'types': [],  # Vide = tous les types
            'icao_only': False,
            'iata_only': False
        }
        self.load_airports(csv_path)

    def load_airports(self, csv_path: str):
        """Charger la base de données d'aéroports"""
        try:
            print("Chargement de la base de données d'aéroports...")
            self.airports_df = pd.read_csv(csv_path)

            # Nettoyer les données de base
            self.airports_df['icao_code'] = self.airports_df['icao_code'].fillna('').str.upper()
            self.airports_df['iata_code'] = self.airports_df['iata_code'].fillna('').str.upper()
            self.airports_df['ident'] = self.airports_df['ident'].fillna('').str.upper()
            self.airports_df['local_code'] = self.airports_df['local_code'].fillna('').str.upper()
            self.airports_df['gps_code'] = self.airports_df['gps_code'].fillna('').str.upper()
            self.airports_df['municipality'] = self.airports_df['municipality'].fillna('Unknown')
            self.airports_df['name'] = self.airports_df['name'].fillna('Unnamed Airport')

            print(f"Base de données chargée: {len(self.airports_df)} aéroports totaux")

            # Appliquer filtres par défaut (Canada + US avec tous les types d'aéroports)
            self.current_filters = {
                'countries': ['CA', 'US'],
                'types': [],  # Tous les types par défaut
                'icao_only': False,  # Inclure tous les codes
                'iata_only': False
            }
            self.apply_filters()

        except Exception as e:
            print(f"Erreur lors du chargement: {e}")
            # Données de fallback
            self.create_fallback_data()

    def apply_filters(self):
        """Appliquer les filtres actuels"""
        if self.airports_df is None:
            return

        filtered_df = self.airports_df.copy()

        # Filtre par pays
        if self.current_filters['countries']:
            filtered_df = filtered_df[filtered_df['iso_country'].isin(self.current_filters['countries'])]

        # Filtre par type d'aéroport
        if self.current_filters['types']:
            filtered_df = filtered_df[filtered_df['type'].isin(self.current_filters['types'])]

        # Filtre ICAO seulement
        if self.current_filters['icao_only']:
            filtered_df = filtered_df[filtered_df['icao_code'] != '']

        # Filtre IATA seulement
        if self.current_filters['iata_only']:
            filtered_df = filtered_df[filtered_df['iata_code'] != '']

        self.filtered_airports = filtered_df.copy()

        # Créer nom d'affichage
        self.filtered_airports['display_name'] = self.create_display_names(self.filtered_airports)

        print(f"Filtres appliqués: {len(self.filtered_airports)} aéroports retenus")

        # Debug: Vérifier si CSE4 est présent
        if len(self.filtered_airports) > 0:
            cse4_check = self.filtered_airports[
                (self.filtered_airports['ident'].str.contains('CSE4', na=False)) |
                (self.filtered_airports['icao_code'].str.contains('CSE4', na=False)) |
                (self.filtered_airports['local_code'].str.contains('CSE4', na=False))
                ]
            if not cse4_check.empty:
                print("✅ CSE4 trouvé dans les résultats filtrés")
            else:
                print("⚠️ CSE4 non trouvé - vérification de la base...")
                # Vérifier dans la base complète
                cse4_full = self.airports_df[
                    (self.airports_df['ident'].str.contains('CSE4', na=False)) |
                    (self.airports_df['icao_code'].str.contains('CSE4', na=False)) |
                    (self.airports_df['local_code'].str.contains('CSE4', na=False))
                    ]
                if not cse4_full.empty:
                    print(f"CSE4 existe mais filtré: {cse4_full.iloc[0]['type']}, {cse4_full.iloc[0]['iso_country']}")

    def create_display_names(self, df):
        """Créer les noms d'affichage pour les aéroports"""
        display_names = []
        for _, row in df.iterrows():
            # Prioriser dans l'ordre: ICAO, IATA, ident (code principal), local_code
            code = (row['icao_code'] if row['icao_code'] else
                    row['iata_code'] if row['iata_code'] else
                    row['ident'] if row['ident'] else
                    row['local_code'] if row['local_code'] else
                    f"ID{row.get('id', 'Unknown')}")

            name = f"{code} - {row['name']}"
            if row['municipality'] and row['municipality'] != 'Unknown':
                name += f" ({row['municipality']})"
            if row['iso_country']:
                name += f" [{row['iso_country']}]"

            # Ajouter indicateur du type de code
            if row['icao_code']:
                name += " 🔵"  # ICAO
            elif row['iata_code']:
                name += " 🟡"  # IATA
            else:
                name += " 🟢"  # Local/Ident

            display_names.append(name)
        return display_names

    def get_available_countries(self):
        """Obtenir la liste des pays disponibles"""
        if self.airports_df is None:
            return []
        return sorted(self.airports_df['iso_country'].dropna().unique())

    def get_available_types(self):
        """Obtenir la liste des types d'aéroports disponibles"""
        if self.airports_df is None:
            return []
        return sorted(self.airports_df['type'].dropna().unique())

    def update_filters(self, countries=None, types=None, icao_only=None, iata_only=None):
        """Mettre à jour les filtres"""
        if countries is not None:
            self.current_filters['countries'] = countries
        if types is not None:
            self.current_filters['types'] = types
        if icao_only is not None:
            self.current_filters['icao_only'] = icao_only
        if iata_only is not None:
            self.current_filters['iata_only'] = iata_only

        self.apply_filters()

    def reset_filters(self):
        """Réinitialiser tous les filtres (charger tous les aéroports)"""
        self.current_filters = {
            'countries': [],
            'types': [],
            'icao_only': False,
            'iata_only': False
        }
        self.apply_filters()

    def get_filter_stats(self):
        """Obtenir des statistiques sur les filtres"""
        total = len(self.airports_df) if self.airports_df is not None else 0
        filtered = len(self.filtered_airports) if self.filtered_airports is not None else 0
        return {
            'total': total,
            'filtered': filtered,
            'percentage': (filtered / total * 100) if total > 0 else 0
        }

    def create_fallback_data(self):
        """Créer des données de base si le fichier CSV n'est pas trouvé"""
        fallback_data = {
            'ident': ['CYUL', 'CYQB', 'CYOW', 'CYYC', 'CYVR', 'CYYZ', 'KBOS', 'KJFK', 'CSE4'],
            'icao_code': ['CYUL', 'CYQB', 'CYOW', 'CYYC', 'CYVR', 'CYYZ', 'KBOS', 'KJFK', ''],
            'iata_code': ['YUL', 'YQB', 'YOW', 'YYC', 'YVR', 'YYZ', 'BOS', 'JFK', ''],
            'local_code': ['', '', '', '', '', '', '', '', 'CSE4'],
            'gps_code': ['', '', '', '', '', '', '', '', 'CSE4'],
            'name': ['Montreal Trudeau', 'Quebec Jean Lesage', 'Ottawa Macdonald-Cartier',
                     'Calgary', 'Vancouver', 'Toronto Pearson', 'Boston Logan', 'New York JFK', 'Saint-Esprit'],
            'latitude_deg': [45.458, 46.791, 45.323, 51.114, 49.194, 43.677, 42.364, 40.640, 45.9],
            'longitude_deg': [-73.749, -71.393, -75.669, -114.019, -123.184, -79.631, -71.005, -73.779, -73.6],
            'municipality': ['Montreal', 'Quebec', 'Ottawa', 'Calgary', 'Vancouver', 'Toronto', 'Boston', 'New York',
                             'Saint-Esprit'],
            'iso_country': ['CA', 'CA', 'CA', 'CA', 'CA', 'CA', 'US', 'US', 'CA'],
            'type': ['large_airport', 'large_airport', 'large_airport', 'large_airport', 'large_airport',
                     'large_airport', 'large_airport', 'large_airport', 'small_airport']
        }

        self.airports_df = pd.DataFrame(fallback_data)
        self.filtered_airports = self.airports_df.copy()
        self.filtered_airports['display_name'] = self.create_display_names(self.filtered_airports)
        print("Utilisation des données de base (9 aéroports, incluant CSE4)")

    def search_airports(self, query: str, max_results: int = 20) -> List[Dict]:
        """Rechercher des aéroports par nom, code ICAO, IATA, ident, local_code, ou ville"""
        if self.filtered_airports is None or query == "":
            return []

        query = query.upper()

        # Recherche dans TOUTES les colonnes de codes et informations
        mask = (
                self.filtered_airports['icao_code'].str.contains(query, na=False) |
                self.filtered_airports['iata_code'].str.contains(query, na=False) |
                self.filtered_airports['ident'].str.contains(query, na=False) |
                self.filtered_airports['local_code'].str.contains(query, na=False) |
                self.filtered_airports['gps_code'].str.contains(query, na=False) |
                self.filtered_airports['name'].str.upper().str.contains(query, na=False) |
                self.filtered_airports['municipality'].str.upper().str.contains(query, na=False)
        )

        results = self.filtered_airports[mask].head(max_results)

        return [
            {
                'icao': row['icao_code'] if row['icao_code'] else row['ident'],
                'iata': row['iata_code'],
                'ident': row['ident'],
                'local_code': row['local_code'],
                'gps_code': row['gps_code'],
                'name': row['name'],
                'city': row['municipality'],
                'country': row['iso_country'],
                'type': row['type'],
                'lat': row['latitude_deg'],
                'lon': row['longitude_deg'],
                'display': row['display_name']
            }
            for _, row in results.iterrows()
        ]

    def get_airport_by_code(self, code: str) -> Optional[Dict]:
        """Obtenir un aéroport par n'importe quel code (ICAO, IATA, ident, local_code, gps_code)"""
        if self.filtered_airports is None:
            return None

        code = code.upper()
        match = self.filtered_airports[
            (self.filtered_airports['icao_code'] == code) |
            (self.filtered_airports['iata_code'] == code) |
            (self.filtered_airports['ident'] == code) |
            (self.filtered_airports['local_code'] == code) |
            (self.filtered_airports['gps_code'] == code)
            ]

        if not match.empty:
            row = match.iloc[0]
            return {
                'icao': row['icao_code'] if row['icao_code'] else row['ident'],
                'iata': row['iata_code'],
                'ident': row['ident'],
                'local_code': row['local_code'],
                'gps_code': row['gps_code'],
                'name': row['name'],
                'city': row['municipality'],
                'country': row['iso_country'],
                'type': row['type'],
                'lat': row['latitude_deg'],
                'lon': row['longitude_deg'],
                'display': row['display_name']
            }
        return None


class AirportSearchWidget(ttk.Frame):
    """Widget de recherche d'aéroports avec autocomplete"""

    def __init__(self, parent, airport_db: AirportDatabase, label_text: str = "Aéroport:"):
        super().__init__(parent)
        self.airport_db = airport_db
        self.selected_airport = None
        self.callback = None

        # Label
        self.label = ttk.Label(self, text=label_text)
        self.label.grid(row=0, column=0, sticky='w', padx=5, pady=2)

        # Entry avec autocomplete
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        self.search_entry = ttk.Entry(self, textvariable=self.search_var, width=40)
        self.search_entry.grid(row=1, column=0, columnspan=2, sticky='ew', padx=5, pady=2)

        # Listbox pour les résultats
        self.results_frame = ttk.Frame(self)
        self.results_frame.grid(row=2, column=0, columnspan=2, sticky='ew', padx=5, pady=2)

        self.results_listbox = tk.Listbox(self.results_frame, height=5)
        self.results_listbox.pack(side='left', fill='both', expand=True)
        self.results_listbox.bind('<<ListboxSelect>>', self.on_select)

        scrollbar = ttk.Scrollbar(self.results_frame, orient='vertical')
        scrollbar.pack(side='right', fill='y')
        self.results_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.results_listbox.yview)

        # Initialement caché
        self.results_frame.grid_remove()

        # Info sélection
        self.info_label = ttk.Label(self, text="", foreground='blue')
        self.info_label.grid(row=3, column=0, columnspan=2, sticky='w', padx=5, pady=2)

        self.grid_columnconfigure(0, weight=1)

    def on_search_change(self, *args):
        """Appelé quand le texte de recherche change"""
        query = self.search_var.get()

        if len(query) < 2:
            self.results_frame.grid_remove()
            return

        # Rechercher aéroports
        results = self.airport_db.search_airports(query)

        # Mettre à jour la listbox
        self.results_listbox.delete(0, tk.END)
        for airport in results:
            self.results_listbox.insert(tk.END, airport['display'])

        if results:
            self.results_frame.grid()
        else:
            self.results_frame.grid_remove()

    def on_select(self, event):
        """Appelé quand un aéroport est sélectionné"""
        selection = self.results_listbox.curselection()
        if not selection:
            return

        # Retrouver l'aéroport sélectionné
        selected_text = self.results_listbox.get(selection[0])
        # Extraire le code (premier élément avant le premier " - ")
        code = selected_text.split(' - ')[0]
        self.selected_airport = self.airport_db.get_airport_by_code(code)

        if self.selected_airport:
            self.search_var.set(self.selected_airport['display'])
            self.info_label.config(
                text=f"Lat: {self.selected_airport['lat']:.4f}, "
                     f"Lon: {self.selected_airport['lon']:.4f}, "
                     f"Type: {self.selected_airport.get('type', 'N/A')}"
            )
            self.results_frame.grid_remove()

            # Appeler callback si défini
            if self.callback:
                self.callback(self.selected_airport)

    def set_callback(self, callback):
        """Définir une fonction de callback pour la sélection"""
        self.callback = callback

    def get_selected_airport(self):
        """Retourner l'aéroport sélectionné"""
        return self.selected_airport

    def clear(self):
        """Effacer la sélection"""
        self.search_var.set("")
        self.selected_airport = None
        self.info_label.config(text="")
        self.results_frame.grid_remove()


class VFRPlannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Outil de planification de vol VFR")
        self.root.geometry("1000x700")

        # Base de données d'aéroports
        self.airport_db = AirportDatabase()

        # Variables
        self.aircraft_info = {}
        self.flight_info = {}
        self.waypoints = []
        self.departure_airport = None
        self.destination_airport = None

        self.create_widgets()

    def create_widgets(self):
        # Menu principal
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="📄 Nouveau plan", command=self.new_flight_plan, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="📁 Ouvrir plan...", command=self.load_flight_plan, accelerator="Ctrl+O")
        file_menu.add_command(label="💾 Sauvegarder plan...", command=self.save_flight_plan, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="📊 Exporter plan Excel...", command=self.generate_excel_plan)
        file_menu.add_command(label="📄 Exporter plan PDF...", command=self.generate_pdf_plan)
        file_menu.add_command(label="📝 Exporter résumé...", command=self.export_flight_plan_summary)
        file_menu.add_separator()
        file_menu.add_command(label="❌ Quitter", command=self.root.quit, accelerator="Ctrl+Q")

        # Menu outils
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Outils", menu=tools_menu)
        tools_menu.add_command(label="🔧 Diagnostic imports", command=self.diagnose_import_issues)
        tools_menu.add_command(label="🔍 Test CSE4", command=self.test_cse4_search)
        tools_menu.add_command(label="🔄 Réinitialiser filtres", command=self.reset_airport_filters)
        tools_menu.add_separator()
        tools_menu.add_command(label="🗺️ Carte interactive", command=self.show_interactive_map)

        # Menu aide
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="📖 Guide d'utilisation", command=self.show_usage_guide)
        help_menu.add_command(label="ℹ️ À propos", command=self.show_about)

        # Raccourcis clavier
        self.root.bind('<Control-n>', lambda e: self.new_flight_plan())
        self.root.bind('<Control-o>', lambda e: self.load_flight_plan())
        self.root.bind('<Control-s>', lambda e: self.save_flight_plan())
        self.root.bind('<Control-q>', lambda e: self.root.quit())

        # Notebook pour les onglets
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Onglet 1: Information avion
        aircraft_frame = ttk.Frame(notebook)
        notebook.add(aircraft_frame, text="✈️ Avion")
        self.create_aircraft_tab(aircraft_frame)

        # Onglet 2: Sélection aéroports
        airports_frame = ttk.Frame(notebook)
        notebook.add(airports_frame, text="🛫 Aéroports")
        self.create_airports_tab(airports_frame)

        # Onglet 3: Itinéraire détaillé
        route_frame = ttk.Frame(notebook)
        notebook.add(route_frame, text="🗺️ Itinéraire")
        self.create_route_tab(route_frame)

        # Onglet 4: Plan de vol
        plan_frame = ttk.Frame(notebook)
        notebook.add(plan_frame, text="📋 Plan de vol")
        self.create_plan_tab(plan_frame)

        # Barre d'état
        self.status_var = tk.StringVar()
        self.status_var.set("Prêt - Sélectionnez les aéroports de départ et d'arrivée")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief='sunken')
        status_bar.pack(side='bottom', fill='x')

    def create_aircraft_tab(self, parent):
        # Frame principal avec scroll
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Informations avion
        aircraft_group = ttk.LabelFrame(scrollable_frame, text="Informations de l'avion", padding=10)
        aircraft_group.pack(fill='x', padx=10, pady=5)

        aircraft_fields = [
            ("Immatriculation (ex: C-FXYZ):", "registration"),
            ("Type d'avion (ex: C172):", "aircraft_type"),
            ("Vitesse de croisière (kn):", "cruise_speed"),
            ("Consommation (GPH):", "fuel_burn"),
            ("Capacité réservoir (gal):", "fuel_capacity"),
            ("Poids à vide (lbs):", "empty_weight"),
            ("Charge utile max (lbs):", "max_payload"),
            ("Équipements (GPS, Transponder, etc.):", "equipment")
        ]

        self.aircraft_entries = {}
        for i, (label, key) in enumerate(aircraft_fields):
            ttk.Label(aircraft_group, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=3)
            entry = ttk.Entry(aircraft_group, width=25)
            entry.grid(row=i, column=1, padx=5, pady=3, sticky='ew')
            self.aircraft_entries[key] = entry

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

        self.flight_entries = {}
        for i, (label, key) in enumerate(flight_fields):
            ttk.Label(flight_group, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=3)
            entry = ttk.Entry(flight_group, width=25)
            entry.grid(row=i, column=1, padx=5, pady=3, sticky='ew')
            self.flight_entries[key] = entry

        flight_group.grid_columnconfigure(1, weight=1)

        # Valeurs par défaut
        self.flight_entries['reserve_time'].insert(0, "45")
        self.aircraft_entries['cruise_speed'].insert(0, "110")
        self.aircraft_entries['fuel_burn'].insert(0, "7.5")

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_airports_tab(self, parent):
        # Instructions
        instructions = ttk.Label(parent,
                                 text="Recherchez vos aéroports par code (ICAO, IATA, local) ou nom. "
                                      "🔵=ICAO officiel, 🟡=IATA, 🟢=Code local/GPS. "
                                      "Configurez les filtres pour affiner la recherche.",
                                 wraplength=600, justify='left')
        instructions.pack(pady=5, padx=10)

        # Frame principal avec panneau de filtres
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Panneau de filtres (à gauche)
        filter_frame = ttk.LabelFrame(main_frame, text="🔍 Filtres de recherche", padding=5)
        filter_frame.pack(side='left', fill='y', padx=(0, 5))

        # Statistiques
        stats = self.airport_db.get_filter_stats()
        self.stats_label = ttk.Label(filter_frame,
                                     text=f"📊 {stats['filtered']:,} / {stats['total']:,} aéroports\n({stats['percentage']:.1f}%)",
                                     font=('Arial', 9))
        self.stats_label.pack(pady=5)

        # Filtres par pays
        countries_frame = ttk.LabelFrame(filter_frame, text="Pays", padding=3)
        countries_frame.pack(fill='x', pady=2)

        self.country_vars = {}
        available_countries = self.airport_db.get_available_countries()

        # Frame avec scroll pour les pays
        countries_scroll_frame = ttk.Frame(countries_frame)
        countries_scroll_frame.pack(fill='both', expand=True)

        countries_canvas = tk.Canvas(countries_scroll_frame, height=80)
        countries_scrollbar = ttk.Scrollbar(countries_scroll_frame, orient="vertical", command=countries_canvas.yview)
        countries_scrollable = ttk.Frame(countries_canvas)

        countries_scrollable.bind(
            "<Configure>",
            lambda e: countries_canvas.configure(scrollregion=countries_canvas.bbox("all"))
        )

        countries_canvas.create_window((0, 0), window=countries_scrollable, anchor="nw")
        countries_canvas.configure(yscrollcommand=countries_scrollbar.set)

        # Principales options de pays
        priority_countries = ['CA', 'US', 'FR', 'GB', 'DE', 'AU']
        other_countries = [c for c in available_countries if c not in priority_countries]

        for i, country in enumerate(priority_countries + other_countries[:10]):  # Limiter l'affichage
            if country in available_countries:
                var = tk.BooleanVar()
                # Cocher Canada et US par défaut
                if country in ['CA', 'US']:
                    var.set(True)
                self.country_vars[country] = var
                cb = ttk.Checkbutton(countries_scrollable, text=country, variable=var,
                                     command=self.update_airport_filters)
                cb.grid(row=i // 2, column=i % 2, sticky='w', padx=2)

        countries_canvas.pack(side="left", fill="both", expand=True)
        countries_scrollbar.pack(side="right", fill="y")

        # Filtres par type d'aéroport
        types_frame = ttk.LabelFrame(filter_frame, text="Types d'aéroports", padding=3)
        types_frame.pack(fill='x', pady=2)

        self.type_vars = {}
        available_types = self.airport_db.get_available_types()
        type_labels = {
            'large_airport': 'Grands (✈️)',
            'medium_airport': 'Moyens (🛩️)',
            'small_airport': 'Petits (🚁)',
            'heliport': 'Héliports',
            'seaplane_base': 'Hydravions',
            'balloonport': 'Ballons',
            'closed': 'Fermés'
        }

        for i, airport_type in enumerate(available_types):
            var = tk.BooleanVar()
            # Tous les types décochés par défaut pour inclure tout
            var.set(False)
            self.type_vars[airport_type] = var
            label = type_labels.get(airport_type, airport_type.replace('_', ' ').title())
            cb = ttk.Checkbutton(types_frame, text=label, variable=var,
                                 command=self.update_airport_filters)
            cb.grid(row=i // 2, column=i % 2, sticky='w', padx=2)

        # Options de codes
        codes_frame = ttk.LabelFrame(filter_frame, text="Codes d'identification", padding=3)
        codes_frame.pack(fill='x', pady=2)

        self.icao_only_var = tk.BooleanVar(value=False)  # Décoché par défaut
        self.iata_only_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(codes_frame, text="Code ICAO requis (CYUL)", variable=self.icao_only_var,
                        command=self.update_airport_filters).pack(anchor='w')
        ttk.Checkbutton(codes_frame, text="Code IATA requis (YUL)", variable=self.iata_only_var,
                        command=self.update_airport_filters).pack(anchor='w')

        # Boutons de contrôle des filtres
        filter_buttons_frame = ttk.Frame(filter_frame)
        filter_buttons_frame.pack(fill='x', pady=5)

        ttk.Button(filter_buttons_frame, text="🔄 Réinitialiser",
                   command=self.reset_airport_filters).pack(side='top', fill='x', pady=1)
        ttk.Button(filter_buttons_frame, text="🌍 Tous les pays",
                   command=self.select_all_countries).pack(side='top', fill='x', pady=1)
        ttk.Button(filter_buttons_frame, text="✈️ Tous les types",
                   command=self.select_all_types).pack(side='top', fill='x', pady=1)
        ttk.Button(filter_buttons_frame, text="🔍 Test CSE4",
                   command=self.test_cse4_search).pack(side='top', fill='x', pady=1)

        # Panneau principal de sélection d'aéroports (à droite)
        selection_frame = ttk.Frame(main_frame)
        selection_frame.pack(side='right', fill='both', expand=True)

        # Aéroport de départ
        departure_frame = ttk.LabelFrame(selection_frame, text="Aéroport de départ", padding=10)
        departure_frame.pack(fill='x', pady=5)

        self.departure_search = AirportSearchWidget(departure_frame, self.airport_db, "Départ:")
        self.departure_search.pack(fill='x')
        self.departure_search.set_callback(self.on_departure_selected)

        # Aéroport d'arrivée
        destination_frame = ttk.LabelFrame(selection_frame, text="Aéroport d'arrivée", padding=10)
        destination_frame.pack(fill='x', pady=5)

        self.destination_search = AirportSearchWidget(destination_frame, self.airport_db, "Arrivée:")
        self.destination_search.pack(fill='x')
        self.destination_search.set_callback(self.on_destination_selected)

        # Boutons d'action
        button_frame = ttk.Frame(selection_frame)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(button_frame, text="🔄 Inverser départ/arrivée",
                   command=self.swap_airports).pack(side='left', padx=5)
        ttk.Button(button_frame, text="📍 Ajouter à l'itinéraire",
                   command=self.add_airports_to_route).pack(side='left', padx=5)
        ttk.Button(button_frame, text="🗺️ Voir sur carte",
                   command=self.show_airports_on_map).pack(side='left', padx=5)

        # Informations de vol calculées
        self.flight_info_frame = ttk.LabelFrame(selection_frame, text="Informations de vol", padding=10)
        self.flight_info_frame.pack(fill='both', expand=True, pady=5)

        self.flight_info_text = tk.Text(self.flight_info_frame, height=8, wrap='word')
        self.flight_info_text.pack(fill='both', expand=True)

    def update_airport_filters(self):
        """Mettre à jour les filtres d'aéroports"""
        # Collecter les pays sélectionnés
        selected_countries = [country for country, var in self.country_vars.items() if var.get()]

        # Collecter les types sélectionnés
        selected_types = [airport_type for airport_type, var in self.type_vars.items() if var.get()]

        # Appliquer les filtres
        self.airport_db.update_filters(
            countries=selected_countries,
            types=selected_types,
            icao_only=self.icao_only_var.get(),
            iata_only=self.iata_only_var.get()
        )

        # Mettre à jour les statistiques
        stats = self.airport_db.get_filter_stats()
        self.stats_label.config(
            text=f"📊 {stats['filtered']:,} / {stats['total']:,} aéroports\n({stats['percentage']:.1f}%)"
        )

        # Effacer les recherches actuelles pour forcer le rafraîchissement
        self.departure_search.clear()
        self.destination_search.clear()

        self.status_var.set(f"Filtres mis à jour: {stats['filtered']:,} aéroports disponibles")

    def reset_airport_filters(self):
        """Réinitialiser tous les filtres (afficher tous les aéroports)"""
        # Décocher toutes les cases
        for var in self.country_vars.values():
            var.set(False)
        for var in self.type_vars.values():
            var.set(False)
        self.icao_only_var.set(False)
        self.iata_only_var.set(False)

        # Réinitialiser dans la base de données
        self.airport_db.reset_filters()

        # Mettre à jour l'affichage
        stats = self.airport_db.get_filter_stats()
        self.stats_label.config(
            text=f"📊 {stats['filtered']:,} / {stats['total']:,} aéroports\n({stats['percentage']:.1f}%)"
        )

        self.departure_search.clear()
        self.destination_search.clear()

        self.status_var.set(f"Tous les filtres réinitialisés - {stats['filtered']:,} aéroports disponibles")

    def select_all_countries(self):
        """Sélectionner tous les pays"""
        for var in self.country_vars.values():
            var.set(True)
        self.update_airport_filters()

    def select_all_types(self):
        """Sélectionner tous les types d'aéroports"""
        for var in self.type_vars.values():
            var.set(True)
        self.update_airport_filters()

    def test_cse4_search(self):
        """Tester la recherche de CSE4 pour diagnostiquer les problèmes"""
        if self.airport_db.airports_df is None:
            messagebox.showinfo("Test CSE4", "Base de données non chargée")
            return

        # Rechercher CSE4 dans la base complète
        full_df = self.airport_db.airports_df
        cse4_results = full_df[
            (full_df['ident'].str.contains('CSE4', na=False)) |
            (full_df['icao_code'].str.contains('CSE4', na=False)) |
            (full_df['local_code'].str.contains('CSE4', na=False)) |
            (full_df['gps_code'].str.contains('CSE4', na=False))
            ]

        message = "🔍 RÉSULTATS DE LA RECHERCHE CSE4:\n\n"

        if cse4_results.empty:
            message += "❌ CSE4 non trouvé dans la base de données complète.\n"
            message += "Vérifiez que le fichier airports.csv contient cet aéroport."
        else:
            for _, row in cse4_results.iterrows():
                message += f"✅ TROUVÉ: {row['ident']}\n"
                message += f"   Nom: {row['name']}\n"
                message += f"   Ville: {row['municipality']}\n"
                message += f"   Pays: {row['iso_country']}\n"
                message += f"   Type: {row['type']}\n"
                message += f"   ICAO: {row['icao_code']}\n"
                message += f"   IATA: {row['iata_code']}\n"
                message += f"   Local: {row['local_code']}\n"
                message += f"   GPS: {row['gps_code']}\n"
                message += f"   Coordonnées: {row['latitude_deg']:.4f}, {row['longitude_deg']:.4f}\n\n"

        # Vérifier dans les résultats filtrés
        filtered_cse4 = self.airport_db.search_airports("CSE4")
        if filtered_cse4:
            message += f"✅ CSE4 disponible dans les résultats filtrés actuels\n"
        else:
            message += f"⚠️ CSE4 filtré par les paramètres actuels\n"
            message += "Essayez de décocher les filtres ou cliquez 'Réinitialiser'\n"

        messagebox.showinfo("Test de recherche CSE4", message)

    def create_route_tab(self, parent):
        # Frame principal
        main_frame = ttk.PanedWindow(parent, orient='horizontal')
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

        ttk.Button(wp_button_frame, text="➕ Ajouter waypoint",
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

        self.waypoint_details = ttk.LabelFrame(right_frame, text="Détails du waypoint", padding=10)
        self.waypoint_details.pack(fill='both', expand=True, pady=5)

        self.waypoint_detail_text = tk.Text(self.waypoint_details, wrap='word')
        self.waypoint_detail_text.pack(fill='both', expand=True)

    def create_plan_tab(self, parent):
        # Frame principal
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Boutons de génération
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=5)

        ttk.Button(button_frame, text="🧮 Calculer itinéraire complet",
                   command=self.calculate_full_route).pack(side='left', padx=5)
        ttk.Button(button_frame, text="🔧 Diagnostic imports",
                   command=self.diagnose_import_issues).pack(side='left', padx=5)
        ttk.Button(button_frame, text="📊 Générer plan Excel",
                   command=self.generate_excel_plan).pack(side='left', padx=5)
        ttk.Button(button_frame, text="📄 Générer plan PDF",
                   command=self.generate_pdf_plan).pack(side='left', padx=5)
        ttk.Button(button_frame, text="🗺️ Carte interactive",
                   command=self.show_interactive_map).pack(side='left', padx=5)

        # Zone d'affichage du plan
        self.plan_frame = ttk.LabelFrame(main_frame, text="Aperçu du plan de vol", padding=10)
        self.plan_frame.pack(fill='both', expand=True, pady=5)

        # Text widget avec scrollbar
        text_frame = ttk.Frame(self.plan_frame)
        text_frame.pack(fill='both', expand=True)

        self.plan_text = tk.Text(text_frame, wrap='none', font=('Courier', 9))
        self.plan_text.pack(side='left', fill='both', expand=True)

        plan_scrollbar_v = ttk.Scrollbar(text_frame, orient='vertical', command=self.plan_text.yview)
        plan_scrollbar_v.pack(side='right', fill='y')
        self.plan_text.configure(yscrollcommand=plan_scrollbar_v.set)

        plan_scrollbar_h = ttk.Scrollbar(self.plan_frame, orient='horizontal', command=self.plan_text.xview)
        plan_scrollbar_h.pack(side='bottom', fill='x')
        self.plan_text.configure(xscrollcommand=plan_scrollbar_h.set)

    def on_departure_selected(self, airport):
        """Callback pour sélection aéroport de départ"""
        self.departure_airport = airport
        self.update_flight_info()
        self.status_var.set(f"Départ sélectionné: {airport['icao']} - {airport['name']}")

    def on_destination_selected(self, airport):
        """Callback pour sélection aéroport d'arrivée"""
        self.destination_airport = airport
        self.update_flight_info()
        self.status_var.set(f"Arrivée sélectionnée: {airport['icao']} - {airport['name']}")

    def update_flight_info(self):
        """Mettre à jour les informations de vol"""
        if not (self.departure_airport and self.destination_airport):
            return

        # Calculer distance directe
        distance = self.calculate_distance(
            self.departure_airport['lat'], self.departure_airport['lon'],
            self.destination_airport['lat'], self.destination_airport['lon']
        )

        # Calculer cap
        bearing = self.calculate_bearing(
            self.departure_airport['lat'], self.departure_airport['lon'],
            self.destination_airport['lat'], self.destination_airport['lon']
        )

        # Estimer temps de vol (vitesse de croisière par défaut)
        cruise_speed = 110  # kn par défaut
        try:
            cruise_speed = float(self.aircraft_entries.get('cruise_speed', {}).get() or 110)
        except (ValueError, AttributeError):
            pass

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

Note: Ces calculs sont pour un vol direct sans tenir compte du vent.
Utilisez l'onglet 'Plan de vol' pour des calculs détaillés avec météo.
"""

        self.flight_info_text.delete('1.0', tk.END)
        self.flight_info_text.insert('1.0', info_text)

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculer distance haversine en milles nautiques"""
        R = 6371.0  # Rayon terrestre en km

        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance_km = R * c
        return distance_km / 1.852  # Conversion km -> NM

    def calculate_bearing(self, lat1, lon1, lat2, lon2):
        """Calculer le cap entre deux points"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlon_rad = math.radians(lon2 - lon1)

        y = math.sin(dlon_rad) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) -
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad))

        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)

        return (bearing_deg + 360) % 360

    def swap_airports(self):
        """Inverser les aéroports de départ et d'arrivée"""
        if self.departure_airport and self.destination_airport:
            # Échanger les aéroports
            temp = self.departure_airport
            self.departure_airport = self.destination_airport
            self.destination_airport = temp

            # Mettre à jour l'affichage
            self.departure_search.search_var.set(self.departure_airport['display'])
            self.departure_search.selected_airport = self.departure_airport
            self.departure_search.info_label.config(
                text=f"Lat: {self.departure_airport['lat']:.4f}, "
                     f"Lon: {self.departure_airport['lon']:.4f}"
            )

            self.destination_search.search_var.set(self.destination_airport['display'])
            self.destination_search.selected_airport = self.destination_airport
            self.destination_search.info_label.config(
                text=f"Lat: {self.destination_airport['lat']:.4f}, "
                     f"Lon: {self.destination_airport['lon']:.4f}"
            )

            self.update_flight_info()
            self.status_var.set("Aéroports inversés")

    def add_airports_to_route(self):
        """Ajouter les aéroports à l'itinéraire"""
        if not (self.departure_airport and self.destination_airport):
            messagebox.showwarning("Attention", "Veuillez sélectionner les aéroports de départ et d'arrivée")
            return

        # Effacer l'itinéraire actuel
        self.waypoints.clear()

        # Ajouter départ et arrivée
        self.waypoints.append({
            'name': self.departure_airport['icao'],
            'lat': self.departure_airport['lat'],
            'lon': self.departure_airport['lon'],
            'type': 'airport',
            'info': self.departure_airport
        })

        self.waypoints.append({
            'name': self.destination_airport['icao'],
            'lat': self.destination_airport['lat'],
            'lon': self.destination_airport['lon'],
            'type': 'airport',
            'info': self.destination_airport
        })

        self.update_waypoint_list()
        self.status_var.set("Aéroports ajoutés à l'itinéraire")

    def add_custom_waypoint(self):
        """Ajouter un waypoint personnalisé"""
        dialog = CustomWaypointDialog(self.root, self.airport_db)
        if dialog.result:
            waypoint = dialog.result
            self.waypoints.append(waypoint)
            self.update_waypoint_list()

    def remove_waypoint(self):
        """Supprimer le waypoint sélectionné"""
        selection = self.waypoint_listbox.curselection()
        if selection:
            index = selection[0]
            del self.waypoints[index]
            self.update_waypoint_list()

    def move_waypoint_up(self):
        """Déplacer waypoint vers le haut"""
        selection = self.waypoint_listbox.curselection()
        if selection and selection[0] > 0:
            index = selection[0]
            self.waypoints[index], self.waypoints[index - 1] = \
                self.waypoints[index - 1], self.waypoints[index]
            self.update_waypoint_list()
            self.waypoint_listbox.selection_set(index - 1)

    def move_waypoint_down(self):
        """Déplacer waypoint vers le bas"""
        selection = self.waypoint_listbox.curselection()
        if selection and selection[0] < len(self.waypoints) - 1:
            index = selection[0]
            self.waypoints[index], self.waypoints[index + 1] = \
                self.waypoints[index + 1], self.waypoints[index]
            self.update_waypoint_list()
            self.waypoint_listbox.selection_set(index + 1)

    def update_waypoint_list(self):
        """Mettre à jour l'affichage des waypoints"""
        self.waypoint_listbox.delete(0, tk.END)
        for i, wp in enumerate(self.waypoints):
            display_text = f"{i + 1}. {wp['name']} ({wp['lat']:.4f}, {wp['lon']:.4f})"
            if wp.get('type') == 'airport':
                display_text += " ✈️"
            self.waypoint_listbox.insert(tk.END, display_text)

    def on_waypoint_select(self, event):
        """Afficher les détails du waypoint sélectionné"""
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

            self.waypoint_detail_text.delete('1.0', tk.END)
            self.waypoint_detail_text.insert('1.0', details)

    def show_airports_on_map(self):
        """Afficher les aéroports sur une carte"""
        if not (self.departure_airport and self.destination_airport):
            messagebox.showwarning("Attention", "Sélectionnez d'abord les aéroports")
            return

        # Calculer centre de la carte
        center_lat = (self.departure_airport['lat'] + self.destination_airport['lat']) / 2
        center_lon = (self.departure_airport['lon'] + self.destination_airport['lon']) / 2

        # Créer carte
        m = folium.Map(location=[center_lat, center_lon], zoom_start=7)

        # Ajouter marqueurs
        folium.Marker(
            [self.departure_airport['lat'], self.departure_airport['lon']],
            popup=f"DÉPART: {self.departure_airport['icao']}\n{self.departure_airport['name']}",
            tooltip=f"Départ: {self.departure_airport['icao']}",
            icon=folium.Icon(color='green', icon='play')
        ).add_to(m)

        folium.Marker(
            [self.destination_airport['lat'], self.destination_airport['lon']],
            popup=f"ARRIVÉE: {self.destination_airport['icao']}\n{self.destination_airport['name']}",
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
        self.status_var.set("Carte ouverte dans le navigateur")

    def show_interactive_map(self):
        """Afficher la carte interactive complète"""
        if not self.waypoints:
            messagebox.showwarning("Attention", "Aucun waypoint défini")
            return

        # Centre de la carte
        center_lat = sum(wp['lat'] for wp in self.waypoints) / len(self.waypoints)
        center_lon = sum(wp['lon'] for wp in self.waypoints) / len(self.waypoints)

        m = folium.Map(location=[center_lat, center_lon], zoom_start=8)

        # Ajouter tous les waypoints
        for i, wp in enumerate(self.waypoints):
            color = 'green' if i == 0 else 'red' if i == len(self.waypoints) - 1 else 'blue'
            icon = 'play' if i == 0 else 'stop' if i == len(self.waypoints) - 1 else 'info-sign'

            folium.Marker(
                [wp['lat'], wp['lon']],
                popup=f"WP{i + 1}: {wp['name']}",
                tooltip=f"#{i + 1}: {wp['name']}",
                icon=folium.Icon(color=color, icon=icon)
            ).add_to(m)

        # Tracer la route
        if len(self.waypoints) > 1:
            coords = [[wp['lat'], wp['lon']] for wp in self.waypoints]
            folium.PolyLine(coords, color='red', weight=3, opacity=0.8).add_to(m)

        # Sauvegarder et ouvrir
        map_file = "flight_route_map.html"
        m.save(map_file)
        webbrowser.open(f"file://{os.path.abspath(map_file)}")
        self.status_var.set("Carte de l'itinéraire ouverte")

    def calculate_full_route(self):
        """Calculer l'itinéraire complet avec classes GUI-compatibles"""
        if len(self.waypoints) < 2:
            messagebox.showwarning("Attention", "Au moins 2 waypoints requis")
            return

        try:
            # Utiliser les classes GUI-compatibles au lieu des originales
            from gui_itinerary import GuiItinerary, create_itinerary_from_gui

            # Préparer les paramètres depuis l'interface
            aircraft_params = {
                'tas': float(self.aircraft_entries.get('cruise_speed', tk.Entry()).get() or 110),
                'fuel_burn': float(self.aircraft_entries.get('fuel_burn', tk.Entry()).get() or 7.5)
            }

            flight_params = {
                'date': self.flight_entries.get('date', tk.Entry()).get(),
                'time': self.flight_entries.get('departure_time', tk.Entry()).get()
            }

            # Clé API Tomorrow.io (vous pouvez la mettre dans l'interface ou utiliser une par défaut)
            api_key = "CmIKizbzjlLBf8XngqoIAU271bBYNZbk"  # Votre clé existante

            # Créer l'itinéraire avec les nouvelles classes
            self.status_var.set("Calcul en cours...")
            self.root.update()

            itinerary = create_itinerary_from_gui(
                waypoints=self.waypoints,
                aircraft_params=aircraft_params,
                flight_params=flight_params,
                api_key=api_key
            )

            # Obtenir le résumé
            summary = itinerary.get_summary()

            # Construire le texte du plan de vol
            plan_text = "PLAN DE VOL VFR - CALCUL AVEC MÉTÉO RÉELLE\n"
            plan_text += "=" * 70 + "\n\n"

            # Informations générales depuis l'interface
            aircraft_id = self.aircraft_entries.get('registration', tk.Entry()).get() or "N/A"
            aircraft_type = self.aircraft_entries.get('aircraft_type', tk.Entry()).get() or "N/A"
            pilot_name = self.flight_entries.get('pilot_name', tk.Entry()).get() or "N/A"
            date = flight_params['date'] or "N/A"
            departure_time = flight_params['time'] or "N/A"

            plan_text += f"Avion: {aircraft_id} ({aircraft_type})\n"
            plan_text += f"Pilote: {pilot_name}\n"
            plan_text += f"Date: {date}\n"
            plan_text += f"Heure de départ: {departure_time}\n"
            plan_text += f"Vitesse vraie: {aircraft_params['tas']} kn\n"
            plan_text += f"Consommation: {aircraft_params['fuel_burn']} GPH\n\n"

            # En-tête du tableau des legs
            plan_text += "LEG  FROM     TO       DIST   TC   TH   MH  WIND_DIR WIND_SPD  GS  TIME  FUEL_LEG FUEL_TOT\n"
            plan_text += "-" * 85 + "\n"

            # Afficher chaque leg calculé
            for i, leg in enumerate(itinerary.legs):
                leg_dict = leg.to_dict()

                plan_text += f"{i + 1:2d}   {leg_dict['Starting WP'][:7]:7s} {leg_dict['Ending WP'][:7]:7s} "
                plan_text += f"{leg_dict['Distance (NM)']:6.1f} {leg_dict['True course (deg)']:3.0f}  "
                plan_text += f"{leg_dict['True heading (deg)']:3.0f}  {leg_dict['Magnetic heading (deg)']:3.0f}  "
                plan_text += f"{leg_dict['Wind Direction (deg)']:7.0f}  {leg_dict['Wind Speed (kn)']:7.1f}  "
                plan_text += f"{leg_dict['Groundspeed (kn)']:3.0f} {leg_dict['Leg time (min)']:5.0f} "
                plan_text += f"{leg_dict['Fuel burn leg (gal)']:7.1f}  {leg_dict['Fuel burn tot (gal)']:7.1f}\n"

                # Afficher erreurs météo s'il y en a
                if hasattr(leg, 'weather_error') and leg.weather_error:
                    plan_text += f"     ⚠️ Météo: {leg.weather_error}\n"

            # Totaux calculés
            total_distance = summary['total_distance']
            total_time = summary['total_time']
            total_fuel = summary['total_fuel']

            plan_text += "-" * 85 + "\n"
            plan_text += f"TOTAUX:             {total_distance:6.1f}                              "
            plan_text += f"    {total_time:5.0f} {total_fuel:16.1f}\n\n"

            # Informations supplémentaires
            reserve_time = float(self.flight_entries.get('reserve_time', tk.Entry()).get() or 45)
            reserve_fuel = reserve_time * aircraft_params['fuel_burn'] / 60
            total_fuel_required = total_fuel + reserve_fuel

            plan_text += f"Temps total de vol: {total_time / 60:.1f} heures ({total_time:.0f} minutes)\n"
            plan_text += f"Carburant de route: {total_fuel:.1f} gallons\n"
            plan_text += f"Carburant de réserve: {reserve_fuel:.1f} gallons ({reserve_time:.0f} min)\n"
            plan_text += f"Carburant total requis: {total_fuel_required:.1f} gallons\n"
            plan_text += f"Distance totale: {total_distance:.1f} NM\n"

            # Vérification capacité carburant
            try:
                fuel_capacity = float(self.aircraft_entries.get('fuel_capacity', tk.Entry()).get())
                if total_fuel_required > fuel_capacity:
                    plan_text += f"\n⚠️  ATTENTION: Carburant requis ({total_fuel_required:.1f} gal) "
                    plan_text += f"dépasse la capacité ({fuel_capacity:.1f} gal)!\n"
                    plan_text += "   Ajoutez des arrêts de ravitaillement.\n"
                else:
                    plan_text += f"\n✅ Carburant suffisant (capacité: {fuel_capacity:.1f} gal)\n"
            except (ValueError, AttributeError):
                plan_text += f"\n💡 Vérifiez que le carburant requis ne dépasse pas la capacité de votre avion.\n"

            plan_text += f"\n📊 Données météo: Tomorrow.io API (si disponible)\n"
            plan_text += f"🧭 Déclinaison magnétique: Calculée ou approximée\n"
            plan_text += f"⏰ Heures: Calculées automatiquement\n"
            plan_text += f"🛩️ Navigation: Correction de vent appliquée\n"

            # Afficher dans l'interface
            self.plan_text.delete('1.0', tk.END)
            self.plan_text.insert('1.0', plan_text)
            self.status_var.set(f"✅ Itinéraire calculé: {len(itinerary.legs)} segments, {total_time:.0f} min")

            # Stocker l'itinéraire calculé pour la génération de documents
            self.calculated_itinerary = itinerary

        except ImportError as e:
            messagebox.showerror("Classes GUI manquantes",
                                 f"Les classes GUI-compatibles sont requises.\n\n"
                                 f"Erreur: {e}\n\n"
                                 "Solutions:\n"
                                 "1. Sauvegardez le code 'Classes GUI-compatibles' comme 'gui_itinerary.py'\n"
                                 "2. Ou utilisez les calculs de base")
            self.calculate_basic_route()

        except Exception as e:
            error_msg = str(e)
            if "tomorrow.io" in error_msg.lower() or "api" in error_msg.lower():
                messagebox.showwarning("Erreur API météo",
                                       f"Problème avec l'API météo:\n{e}\n\n"
                                       "Le calcul continue avec vent par défaut.")
                # Continuer le calcul même en cas d'erreur météo
                try:
                    self.calculate_basic_route()
                except:
                    pass
            else:
                messagebox.showerror("Erreur de calcul",
                                     f"Erreur lors du calcul:\n{e}\n\n"
                                     "Vérifiez vos données d'entrée.")
                self.calculate_basic_route()

    def check_dependencies(self):
        """Vérifier les dépendances requises"""
        required_modules = [
            'geopy',
            'requests',
            'geomag',
            'datetime',
            'pytz'
        ]

        missing = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing.append(module)

        return missing

    def install_dependencies(self, dependencies):
        """Tenter d'installer les dépendances manquantes"""
        import subprocess
        import sys

        for dep in dependencies:
            try:
                # Mappings pour les noms de packages pip
                pip_names = {
                    'geopy': 'geopy',
                    'geomag': 'geomag',
                    'requests': 'requests',
                    'pytz': 'pytz'
                }

                pip_name = pip_names.get(dep, dep)
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', pip_name])
                messagebox.showinfo("Installation", f"Module '{dep}' installé avec succès!")

            except subprocess.CalledProcessError:
                messagebox.showerror("Erreur d'installation",
                                     f"Impossible d'installer '{dep}' automatiquement.\n"
                                     f"Installez manuellement: pip install {pip_name}")

    def diagnose_import_issues(self):
        """Diagnostiquer les problèmes d'import"""
        diagnostic = "🔍 DIAGNOSTIC DES IMPORTS:\n\n"

        # Vérifier la structure des fichiers
        import os

        files_to_check = [
            "itinerary/__init__.py",
            "itinerary/itinerary.py",
            "itinerary/waypoints.py",
            "itinerary/legs.py"
        ]

        diagnostic += "📁 Structure des fichiers:\n"
        for file_path in files_to_check:
            if os.path.exists(file_path):
                diagnostic += f"✅ {file_path} - Trouvé\n"
            else:
                diagnostic += f"❌ {file_path} - MANQUANT\n"

        diagnostic += "\n🐍 Modules Python:\n"
        modules_to_check = ['geopy', 'requests', 'geomag', 'pytz', 'python_weather']

        for module in modules_to_check:
            try:
                __import__(module)
                diagnostic += f"✅ {module} - Installé\n"
            except ImportError:
                diagnostic += f"❌ {module} - MANQUANT\n"

        diagnostic += "\n💡 SOLUTIONS:\n"
        diagnostic += "1. Installez les modules manquants:\n"
        diagnostic += "   pip install geopy requests geomag pytz\n\n"
        diagnostic += "2. Vérifiez la structure de vos fichiers\n\n"
        diagnostic += "3. Si vous utilisez python_weather, installez-le:\n"
        diagnostic += "   pip install python-weather\n\n"
        diagnostic += "4. Ou modifiez votre code pour utiliser seulement Tomorrow.io"

        messagebox.showinfo("Diagnostic des imports", diagnostic)

    def calculate_basic_route(self):
        """Calculs basiques sans vos classes (fallback)"""
        plan_text = "PLAN DE VOL VFR - CALCUL BASIQUE (MODE FALLBACK)\n"
        plan_text += "=" * 60 + "\n\n"

        # Informations générales
        aircraft_id = self.aircraft_entries.get('registration', tk.Entry()).get() or "N/A"
        aircraft_type = self.aircraft_entries.get('aircraft_type', tk.Entry()).get() or "N/A"
        pilot_name = self.flight_entries.get('pilot_name', tk.Entry()).get() or "N/A"
        date = self.flight_entries.get('date', tk.Entry()).get() or "N/A"

        plan_text += f"Avion: {aircraft_id} ({aircraft_type})\n"
        plan_text += f"Pilote: {pilot_name}\n"
        plan_text += f"Date: {date}\n\n"

        # Table des legs
        plan_text += "LEG  FROM    TO      DIST  TC   WIND    GS   TIME  FUEL\n"
        plan_text += "-" * 50 + "\n"

        total_distance = 0
        total_time = 0
        total_fuel = 0

        for i in range(len(self.waypoints) - 1):
            wp1 = self.waypoints[i]
            wp2 = self.waypoints[i + 1]

            # Calculs basiques
            distance = self.calculate_distance(wp1['lat'], wp1['lon'], wp2['lat'], wp2['lon'])
            bearing = self.calculate_bearing(wp1['lat'], wp1['lon'], wp2['lat'], wp2['lon'])

            # Paramètres par défaut
            cruise_speed = 110
            try:
                cruise_speed = float(self.aircraft_entries.get('cruise_speed', tk.Entry()).get() or 110)
            except ValueError:
                pass

            ground_speed = cruise_speed - 5  # Vent de face léger
            leg_time = distance / ground_speed * 60  # minutes

            fuel_burn = 7.5
            try:
                fuel_burn = float(self.aircraft_entries.get('fuel_burn', tk.Entry()).get() or 7.5)
            except ValueError:
                pass

            leg_fuel = leg_time * fuel_burn / 60

            total_distance += distance
            total_time += leg_time
            total_fuel += leg_fuel

            plan_text += f"{i + 1:2d}   {wp1['name'][:6]:6s} {wp2['name'][:6]:6s} "
            plan_text += f"{distance:5.1f} {bearing:3.0f}°  N/A    {ground_speed:3.0f}  {leg_time:4.0f}  {leg_fuel:4.1f}\n"

        plan_text += "-" * 50 + "\n"
        plan_text += f"TOTAUX:                {total_distance:5.1f}          {total_time:4.0f}  {total_fuel:4.1f}\n\n"

        plan_text += f"Temps total de vol: {total_time / 60:.1f} heures\n"
        plan_text += f"Carburant requis: {total_fuel:.1f} gallons\n"
        plan_text += f"Distance totale: {total_distance:.1f} NM\n\n"

        plan_text += "⚠️  CALCULS APPROXIMATIFS - Vent non pris en compte\n"
        plan_text += "💡 Intégrez vos classes pour des calculs précis avec météo"

        self.plan_text.delete('1.0', tk.END)
        self.plan_text.insert('1.0', plan_text)
        self.status_var.set("Calculs basiques effectués")

    def generate_excel_plan(self):
        """Générer plan Excel avec le vrai générateur"""
        if not hasattr(self, 'calculated_itinerary') or not self.calculated_itinerary:
            messagebox.showwarning("Attention", "Calculez d'abord l'itinéraire complet")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Sauvegarder le plan de vol Excel"
        )

        if filename:
            try:
                # Importer le générateur
                from flight_plan_generator import FlightPlanGenerator

                # Préparer les données de vol
                flight_data = self._prepare_flight_data()
                legs_data = self._prepare_legs_data()

                # Générer le fichier Excel
                generator = FlightPlanGenerator()
                generator.generate_excel_plan(flight_data, legs_data, filename)

                messagebox.showinfo("Succès", f"Plan Excel généré avec succès !\n\nFichier: {filename}")
                self.status_var.set(f"Plan Excel sauvegardé: {filename}")

                # Demander si l'utilisateur veut ouvrir le fichier
                if messagebox.askyesno("Ouvrir le fichier", "Voulez-vous ouvrir le fichier Excel ?"):
                    import os
                    import subprocess
                    import sys

                    if sys.platform.startswith('win'):
                        os.startfile(filename)
                    elif sys.platform.startswith('darwin'):
                        subprocess.call(['open', filename])
                    else:
                        subprocess.call(['xdg-open', filename])

            except ImportError:
                messagebox.showerror("Module manquant",
                                     "Le générateur de plan de vol n'est pas trouvé.\n\n"
                                     "Assurez-vous que 'flight_plan_generator.py' est présent.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la génération Excel:\n{e}")

    def generate_pdf_plan(self):
        """Générer plan PDF avec le vrai générateur"""
        if not hasattr(self, 'calculated_itinerary') or not self.calculated_itinerary:
            messagebox.showwarning("Attention", "Calculez d'abord l'itinéraire complet")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Sauvegarder le plan de vol PDF"
        )

        if filename:
            try:
                # Importer le générateur
                from flight_plan_generator import FlightPlanGenerator

                # Préparer les données de vol
                flight_data = self._prepare_flight_data()
                legs_data = self._prepare_legs_data()

                # Générer le fichier PDF
                generator = FlightPlanGenerator()
                generator.generate_pdf_plan(flight_data, legs_data, filename)

                messagebox.showinfo("Succès", f"Plan PDF généré avec succès !\n\nFichier: {filename}")
                self.status_var.set(f"Plan PDF sauvegardé: {filename}")

                # Demander si l'utilisateur veut ouvrir le fichier
                if messagebox.askyesno("Ouvrir le fichier", "Voulez-vous ouvrir le fichier PDF ?"):
                    import os
                    import subprocess
                    import sys

                    if sys.platform.startswith('win'):
                        os.startfile(filename)
                    elif sys.platform.startswith('darwin'):
                        subprocess.call(['open', filename])
                    else:
                        subprocess.call(['xdg-open', filename])

            except ImportError:
                messagebox.showerror("Module manquant",
                                     "Le générateur de plan de vol n'est pas trouvé.\n\n"
                                     "Assurez-vous que 'flight_plan_generator.py' est présent.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la génération PDF:\n{e}")

    def _prepare_flight_data(self) -> Dict[str, any]:
        """Préparer les données de vol pour le générateur"""
        return {
            'aircraft_id': self.aircraft_entries.get('registration', tk.Entry()).get() or 'N/A',
            'aircraft_type': self.aircraft_entries.get('aircraft_type', tk.Entry()).get() or 'N/A',
            'tas': float(self.aircraft_entries.get('cruise_speed', tk.Entry()).get() or 110),
            'departure': self.departure_airport['icao'] if self.departure_airport else 'N/A',
            'destination': self.destination_airport['icao'] if self.destination_airport else 'N/A',
            'date': self.flight_entries.get('date', tk.Entry()).get() or 'N/A',
            'etd': self.flight_entries.get('departure_time', tk.Entry()).get() or 'N/A',
            'pilot': self.flight_entries.get('pilot_name', tk.Entry()).get() or 'N/A',
            'fuel_capacity': float(self.aircraft_entries.get('fuel_capacity', tk.Entry()).get() or 0),
            'fuel_burn': float(self.aircraft_entries.get('fuel_burn', tk.Entry()).get() or 7.5),
            'reserve_fuel': float(self.flight_entries.get('reserve_time', tk.Entry()).get() or 45),
            'alternate': 'N/A',  # Vous pouvez ajouter un champ pour ça
            'weather_brief': f"Obtained via Tomorrow.io API",
            'notam_check': 'Required',
            'flight_following': 'Recommended'
        }

    def _prepare_legs_data(self) -> List[Dict[str, any]]:
        """Préparer les données des legs pour le générateur"""
        if not hasattr(self, 'calculated_itinerary') or not self.calculated_itinerary:
            return []

        legs_data = []
        for i, leg in enumerate(self.calculated_itinerary.legs):
            leg_dict = leg.to_dict()

            # Calculer ETA
            if i == 0:
                # Premier leg: utiliser heure de départ
                etd_str = self.flight_entries.get('departure_time', tk.Entry()).get() or '10:00'
                try:
                    etd_hour, etd_min = map(int, etd_str.split(':'))
                    eta_minutes = etd_min + leg_dict['Leg time (min)']
                    eta_hour = etd_hour + (eta_minutes // 60)
                    eta_min = eta_minutes % 60
                    eta = f"{eta_hour:02d}:{eta_min:02d}"
                except:
                    eta = "N/A"
            else:
                # Legs suivants: ajouter temps cumulé
                try:
                    total_time = leg_dict['Total time (min)']
                    etd_str = self.flight_entries.get('departure_time', tk.Entry()).get() or '10:00'
                    etd_hour, etd_min = map(int, etd_str.split(':'))
                    eta_minutes = etd_min + total_time
                    eta_hour = etd_hour + (eta_minutes // 60)
                    eta_min = int(eta_minutes % 60)
                    eta = f"{eta_hour:02d}:{eta_min:02d}"
                except:
                    eta = "N/A"

            leg_data = {
                'from': leg_dict['Starting WP'],
                'to': leg_dict['Ending WP'],
                'distance': leg_dict['Distance (NM)'],
                'true_course': leg_dict['True course (deg)'],
                'true_heading': leg_dict['True heading (deg)'],
                'mag_heading': leg_dict['Magnetic heading (deg)'],
                'wind_dir': leg_dict['Wind Direction (deg)'],
                'wind_speed': leg_dict['Wind Speed (kn)'],
                'ground_speed': leg_dict['Groundspeed (kn)'],
                'leg_time': leg_dict['Leg time (min)'],
                'total_time': leg_dict['Total time (min)'],
                'fuel_leg': leg_dict['Fuel burn leg (gal)'],
                'fuel_total': leg_dict['Fuel burn tot (gal)'],
                'eta': eta,
                'remarks': f"Wind: {leg_dict['Wind Direction (deg)']}°/{leg_dict['Wind Speed (kn)']}kn"
            }
            legs_data.append(leg_data)

        return legs_data

    def new_flight_plan(self):
        """Nouveau plan de vol"""
        # Confirmer avant de perdre le travail en cours
        if self.waypoints or any(
                entry.get() for entry in list(self.aircraft_entries.values()) + list(self.flight_entries.values())):
            if not messagebox.askyesno("Nouveau plan",
                                       "Créer un nouveau plan effacera le travail en cours.\n\nContinuer ?"):
                return

        # Réinitialiser tout
        for entry in list(self.aircraft_entries.values()) + list(self.flight_entries.values()):
            entry.delete(0, tk.END)

        # Remettre les valeurs par défaut
        self.flight_entries['reserve_time'].insert(0, "45")
        self.aircraft_entries['cruise_speed'].insert(0, "110")
        self.aircraft_entries['fuel_burn'].insert(0, "7.5")

        self.departure_search.clear()
        self.destination_search.clear()
        self.waypoints.clear()
        self.update_waypoint_list()

        self.departure_airport = None
        self.destination_airport = None

        self.flight_info_text.delete('1.0', tk.END)
        self.plan_text.delete('1.0', tk.END)
        self.waypoint_detail_text.delete('1.0', tk.END)

        # Effacer l'itinéraire calculé
        if hasattr(self, 'calculated_itinerary'):
            delattr(self, 'calculated_itinerary')

        self.status_var.set("Nouveau plan de vol créé")

    def save_flight_plan(self):
        """Sauvegarder le plan de vol complet en format JSON"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Sauvegarder le plan de vol"
        )

        if filename:
            try:
                # Collecter toutes les données de l'interface
                flight_plan_data = {
                    "metadata": {
                        "version": "1.0",
                        "created": datetime.now().isoformat(),
                        "generator": "VFR Flight Planner - MGA802"
                    },

                    "aircraft_info": {
                        key: entry.get() for key, entry in self.aircraft_entries.items()
                    },

                    "flight_info": {
                        key: entry.get() for key, entry in self.flight_entries.items()
                    },

                    "departure_airport": self.departure_airport,
                    "destination_airport": self.destination_airport,

                    "waypoints": self.waypoints,

                    "calculated_itinerary": None  # On sauvegarde les résultats s'ils existent
                }

                # Sauvegarder l'itinéraire calculé s'il existe
                if hasattr(self, 'calculated_itinerary') and self.calculated_itinerary:
                    try:
                        # Extraire les données essentielles de l'itinéraire
                        summary = self.calculated_itinerary.get_summary()
                        legs_data = []

                        for leg in self.calculated_itinerary.legs:
                            leg_dict = leg.to_dict()
                            legs_data.append(leg_dict)

                        flight_plan_data["calculated_itinerary"] = {
                            "summary": summary,
                            "legs": legs_data,
                            "calculation_time": datetime.now().isoformat()
                        }
                    except Exception as e:
                        print(f"Avertissement: Impossible de sauvegarder l'itinéraire calculé: {e}")

                # Sauvegarder en JSON avec indentation pour lisibilité
                import json
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(flight_plan_data, f, indent=2, ensure_ascii=False)

                messagebox.showinfo("Sauvegarde réussie",
                                    f"Plan de vol sauvegardé avec succès !\n\nFichier: {filename}")
                self.status_var.set(f"Plan sauvegardé: {filename}")

            except Exception as e:
                messagebox.showerror("Erreur de sauvegarde",
                                     f"Impossible de sauvegarder le plan de vol:\n{e}")

    def load_flight_plan(self):
        """Charger un plan de vol depuis un fichier JSON"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Charger un plan de vol"
        )

        if filename:
            try:
                # Confirmer avant de perdre le travail en cours
                if self.waypoints or any(entry.get() for entry in
                                         list(self.aircraft_entries.values()) + list(self.flight_entries.values())):
                    if not messagebox.askyesno("Charger plan",
                                               "Charger un plan effacera le travail en cours.\n\nContinuer ?"):
                        return

                # Charger le fichier JSON
                import json
                with open(filename, 'r', encoding='utf-8') as f:
                    flight_plan_data = json.load(f)

                # Vérifier la version et la structure
                if "metadata" not in flight_plan_data:
                    if not messagebox.askyesno("Format ancien",
                                               "Ce fichier semble être dans un format ancien.\n\nEssayer de le charger quand même ?"):
                        return

                # Effacer l'interface actuelle
                self.new_flight_plan()

                # Restaurer les informations de l'avion
                if "aircraft_info" in flight_plan_data:
                    for key, value in flight_plan_data["aircraft_info"].items():
                        if key in self.aircraft_entries and value:
                            self.aircraft_entries[key].insert(0, str(value))

                # Restaurer les informations de vol
                if "flight_info" in flight_plan_data:
                    for key, value in flight_plan_data["flight_info"].items():
                        if key in self.flight_entries and value:
                            self.flight_entries[key].insert(0, str(value))

                # Restaurer les aéroports de départ et d'arrivée
                if flight_plan_data.get("departure_airport"):
                    self.departure_airport = flight_plan_data["departure_airport"]
                    self.departure_search.selected_airport = self.departure_airport
                    self.departure_search.search_var.set(self.departure_airport.get('display', ''))
                    self.departure_search.info_label.config(
                        text=f"Lat: {self.departure_airport.get('lat', 0):.4f}, "
                             f"Lon: {self.departure_airport.get('lon', 0):.4f}, "
                             f"Type: {self.departure_airport.get('type', 'N/A')}"
                    )

                if flight_plan_data.get("destination_airport"):
                    self.destination_airport = flight_plan_data["destination_airport"]
                    self.destination_search.selected_airport = self.destination_airport
                    self.destination_search.search_var.set(self.destination_airport.get('display', ''))
                    self.destination_search.info_label.config(
                        text=f"Lat: {self.destination_airport.get('lat', 0):.4f}, "
                             f"Lon: {self.destination_airport.get('lon', 0):.4f}, "
                             f"Type: {self.destination_airport.get('type', 'N/A')}"
                    )

                # Mettre à jour les informations de vol si les deux aéroports sont chargés
                if self.departure_airport and self.destination_airport:
                    self.update_flight_info()

                # Restaurer les waypoints
                if "waypoints" in flight_plan_data:
                    self.waypoints = flight_plan_data["waypoints"]
                    self.update_waypoint_list()

                # Restaurer l'itinéraire calculé s'il existe
                if flight_plan_data.get("calculated_itinerary"):
                    try:
                        calc_data = flight_plan_data["calculated_itinerary"]

                        # Afficher un résumé de l'itinéraire calculé précédemment
                        summary = calc_data.get("summary", {})
                        legs = calc_data.get("legs", [])
                        calc_time = calc_data.get("calculation_time", "")

                        plan_text = "PLAN DE VOL CHARGÉ (calculé précédemment)\n"
                        plan_text += "=" * 60 + "\n\n"
                        plan_text += f"Calculé le: {calc_time}\n"
                        plan_text += f"Distance totale: {summary.get('total_distance', 0):.1f} NM\n"
                        plan_text += f"Temps total: {summary.get('total_time', 0):.0f} minutes\n"
                        plan_text += f"Carburant total: {summary.get('total_fuel', 0):.1f} gallons\n\n"

                        plan_text += "LEGS:\n"
                        plan_text += "-" * 40 + "\n"
                        for i, leg in enumerate(legs, 1):
                            plan_text += f"{i}. {leg.get('Starting WP', '')} → {leg.get('Ending WP', '')} "
                            plan_text += f"({leg.get('Distance (NM)', 0):.1f} NM, {leg.get('Leg time (min)', 0):.0f} min)\n"

                        plan_text += "\n⚠️ ATTENTION: Ces calculs peuvent être obsolètes.\n"
                        plan_text += "Recalculez l'itinéraire pour obtenir des données météo actuelles."

                        self.plan_text.delete('1.0', tk.END)
                        self.plan_text.insert('1.0', plan_text)

                    except Exception as e:
                        print(f"Impossible de restaurer l'itinéraire calculé: {e}")

                # Extraire le nom du fichier pour l'affichage
                import os
                file_basename = os.path.basename(filename)

                # Afficher les informations de chargement
                metadata = flight_plan_data.get("metadata", {})
                created_date = metadata.get("created", "")

                info_message = f"Plan de vol chargé avec succès !\n\n"
                info_message += f"Fichier: {file_basename}\n"
                if created_date:
                    info_message += f"Créé le: {created_date}\n"
                info_message += f"Waypoints: {len(self.waypoints)}\n"

                if self.departure_airport and self.destination_airport:
                    info_message += f"Route: {self.departure_airport.get('icao', '')} → {self.destination_airport.get('icao', '')}"

                messagebox.showinfo("Chargement réussi", info_message)
                self.status_var.set(f"Plan chargé: {file_basename}")

            except json.JSONDecodeError as e:
                messagebox.showerror("Erreur de format",
                                     f"Le fichier n'est pas un JSON valide:\n{e}")
            except Exception as e:
                messagebox.showerror("Erreur de chargement",
                                     f"Impossible de charger le plan de vol:\n{e}")

    def export_flight_plan_summary(self):
        """Exporter un résumé du plan de vol en format texte"""
        if not self.waypoints:
            messagebox.showwarning("Attention", "Aucun waypoint défini")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Exporter résumé du plan de vol"
        )

        if filename:
            try:
                # Générer le résumé textuel
                summary_text = "RÉSUMÉ DU PLAN DE VOL VFR\n"
                summary_text += "=" * 50 + "\n\n"
                summary_text += f"Généré le: {datetime.now().strftime('%Y-%m-%d à %H:%M')}\n\n"

                # Informations de base
                aircraft_id = self.aircraft_entries.get('registration', tk.Entry()).get() or 'N/A'
                aircraft_type = self.aircraft_entries.get('aircraft_type', tk.Entry()).get() or 'N/A'
                pilot_name = self.flight_entries.get('pilot_name', tk.Entry()).get() or 'N/A'

                summary_text += f"Avion: {aircraft_id} ({aircraft_type})\n"
                summary_text += f"Pilote: {pilot_name}\n"
                summary_text += f"Date: {self.flight_entries.get('date', tk.Entry()).get() or 'N/A'}\n"
                summary_text += f"Heure: {self.flight_entries.get('departure_time', tk.Entry()).get() or 'N/A'}\n\n"

                # Route
                if self.departure_airport and self.destination_airport:
                    summary_text += f"Départ: {self.departure_airport.get('icao', '')} - {self.departure_airport.get('name', '')}\n"
                    summary_text += f"Arrivée: {self.destination_airport.get('icao', '')} - {self.destination_airport.get('name', '')}\n\n"

                # Waypoints
                summary_text += "WAYPOINTS:\n"
                summary_text += "-" * 20 + "\n"
                for i, wp in enumerate(self.waypoints, 1):
                    summary_text += f"{i}. {wp['name']} ({wp['lat']:.4f}, {wp['lon']:.4f})\n"

                # Itinéraire calculé si disponible
                if hasattr(self, 'calculated_itinerary') and self.calculated_itinerary:
                    try:
                        summary = self.calculated_itinerary.get_summary()
                        summary_text += f"\nCALCULS:\n"
                        summary_text += f"-" * 20 + "\n"
                        summary_text += f"Distance: {summary.get('total_distance', 0):.1f} NM\n"
                        summary_text += f"Temps: {summary.get('total_time', 0) / 60:.1f} heures\n"
                        summary_text += f"Carburant: {summary.get('total_fuel', 0):.1f} gal\n"
                    except:
                        pass

                summary_text += f"\n\nFin du résumé\n"

                # Sauvegarder
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(summary_text)

                messagebox.showinfo("Export réussi",
                                    f"Résumé exporté avec succès !\n\nFichier: {filename}")

            except Exception as e:
                messagebox.showerror("Erreur d'export",
                                     f"Impossible d'exporter le résumé:\n{e}")

    def show_usage_guide(self):
        """Afficher le guide d'utilisation"""
        guide_text = """GUIDE D'UTILISATION - OUTIL VFR
================================

📋 WORKFLOW RECOMMANDÉ:

1. ONGLET AVION:
   • Remplir immatriculation, type d'avion
   • Vitesse de croisière (ex: 110 kn)
   • Consommation (ex: 7.5 GPH)
   • Capacité carburant (ex: 40 gal)

2. ONGLET AÉROPORTS:
   • Configurer filtres (pays, types)
   • Rechercher aéroport départ (ex: CYUL)
   • Rechercher aéroport arrivée (ex: CYQB)
   • Cliquer "Ajouter à l'itinéraire"

3. ONGLET ITINÉRAIRE:
   • Ajouter waypoints intermédiaires si besoin
   • Réorganiser l'ordre des waypoints

4. ONGLET PLAN DE VOL:
   • Cliquer "Calculer itinéraire complet"
   • Générer plan Excel ou PDF

🔍 RECHERCHE D'AÉROPORTS:
• Par code ICAO: CYUL, CYQB
• Par code IATA: YUL, YQB  
• Par code local: CSE4, CAM4
• Par nom: Montreal, Quebec
• Par ville: Toronto, Calgary

💾 SAUVEGARDE:
• Fichier → Sauvegarder plan
• Format JSON lisible
• Inclut tous paramètres et calculs

🔧 DÉPANNAGE:
• Menu Outils → Diagnostic imports
• Vérifier connexion internet (météo)
• CSE4 pas trouvé? → Test CSE4

📊 CODES COULEUR:
🔵 = Code ICAO officiel
🟡 = Code IATA  
🟢 = Code local/GPS"""

        # Créer fenêtre de guide
        guide_window = tk.Toplevel(self.root)
        guide_window.title("Guide d'utilisation")
        guide_window.geometry("600x500")
        guide_window.transient(self.root)

        text_widget = tk.Text(guide_window, wrap='word', padx=10, pady=10)
        scrollbar = ttk.Scrollbar(guide_window, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        text_widget.insert('1.0', guide_text)
        text_widget.config(state='disabled')  # Lecture seule

    def show_about(self):
        """Afficher les informations À propos"""
        about_text = """OUTIL DE PLANIFICATION DE VOL VFR
Version 1.0

Projet MGA802 - Introduction à la programmation avec Python
École de technologie supérieure (ÉTS)

ÉQUIPE DE DÉVELOPPEMENT:
• Antoine Gingras
• Matthew Meyer  
• Richard Nguekam
• Gabriel Wong-Lapierre

FONCTIONNALITÉS:
✈️ Planification complète de vols VFR
🗺️ Base de données de 83,000+ aéroports
🌤️ Intégration météo en temps réel
📊 Génération plans Excel et PDF
🧭 Calculs de navigation précis
💾 Sauvegarde/chargement de plans

TECHNOLOGIES UTILISÉES:
• Python 3.x avec Tkinter
• API Tomorrow.io pour météo
• OpenPyXL et ReportLab pour exports
• Folium pour cartes interactives
• Pandas pour gestion de données

Juin 2025 - ÉTS Montréal"""

        messagebox.showinfo("À propos", about_text)


class CustomWaypointDialog:
    def __init__(self, parent, airport_db):
        self.result = None
        self.airport_db = airport_db

        # Créer dialogue
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Ajouter Waypoint Personnalisé")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Type de waypoint
        ttk.Label(self.dialog, text="Type de waypoint:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.type_var = tk.StringVar(value="custom")
        type_frame = ttk.Frame(self.dialog)
        type_frame.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        ttk.Radiobutton(type_frame, text="Coordonnées", variable=self.type_var,
                        value="custom", command=self.on_type_change).pack(side='left')
        ttk.Radiobutton(type_frame, text="Aéroport", variable=self.type_var,
                        value="airport", command=self.on_type_change).pack(side='left')

        # Frame pour coordonnées
        self.coord_frame = ttk.LabelFrame(self.dialog, text="Coordonnées", padding=5)
        self.coord_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky='ew')

        ttk.Label(self.coord_frame, text="Nom:").grid(row=0, column=0, padx=5, pady=2, sticky='w')
        self.name_entry = ttk.Entry(self.coord_frame, width=20)
        self.name_entry.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(self.coord_frame, text="Latitude:").grid(row=1, column=0, padx=5, pady=2, sticky='w')
        self.lat_entry = ttk.Entry(self.coord_frame, width=20)
        self.lat_entry.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(self.coord_frame, text="Longitude:").grid(row=2, column=0, padx=5, pady=2, sticky='w')
        self.lon_entry = ttk.Entry(self.coord_frame, width=20)
        self.lon_entry.grid(row=2, column=1, padx=5, pady=2)

        # Frame pour aéroport
        self.airport_frame = ttk.LabelFrame(self.dialog, text="Recherche d'aéroport", padding=5)
        self.airport_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky='ew')

        self.airport_search = AirportSearchWidget(self.airport_frame, airport_db, "Aéroport:")
        self.airport_search.pack(fill='x')

        # Boutons
        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Annuler", command=self.cancel_clicked).pack(side='left', padx=5)

        # Configuration initiale
        self.on_type_change()
        self.name_entry.focus()

        # Attendre fermeture
        self.dialog.wait_window()

    def on_type_change(self):
        """Changer l'interface selon le type sélectionné"""
        if self.type_var.get() == "custom":
            self.coord_frame.grid()
            self.airport_frame.grid_remove()
        else:
            self.coord_frame.grid_remove()
            self.airport_frame.grid()

    def ok_clicked(self):
        try:
            if self.type_var.get() == "custom":
                name = self.name_entry.get().strip()
                lat = float(self.lat_entry.get())
                lon = float(self.lon_entry.get())

                if not name:
                    messagebox.showerror("Erreur", "Nom requis")
                    return

                self.result = {
                    'name': name,
                    'lat': lat,
                    'lon': lon,
                    'type': 'custom'
                }
            else:
                airport = self.airport_search.get_selected_airport()
                if not airport:
                    messagebox.showerror("Erreur", "Sélectionnez un aéroport")
                    return

                self.result = {
                    'name': airport['icao'],
                    'lat': airport['lat'],
                    'lon': airport['lon'],
                    'type': 'airport',
                    'info': airport
                }

            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Erreur", "Coordonnées invalides")

    def cancel_clicked(self):
        self.dialog.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = VFRPlannerGUI(root)
    root.mainloop()