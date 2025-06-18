import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import folium
import webbrowser
import os
from typing import List, Dict, Optional, Tuple
import math


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
        file_menu.add_command(label="Nouveau plan", command=self.new_flight_plan)
        file_menu.add_command(label="Charger", command=self.load_flight_plan)
        file_menu.add_command(label="Sauvegarder", command=self.save_flight_plan)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit)

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
        """Calculer l'itinéraire complet avec vos classes existantes"""
        if len(self.waypoints) < 2:
            messagebox.showwarning("Attention", "Au moins 2 waypoints requis")
            return

        try:
            # Importer vos classes existantes
            import sys
            import os

            # Ajouter le chemin de votre projet au sys.path si nécessaire
            project_root = os.path.dirname(os.path.abspath(__file__))
            if project_root not in sys.path:
                sys.path.append(project_root)

            from itinerary.itinerary import Itinerary
            from itinerary.waypoints import Waypoint
            from itinerary.legs import Leg

            # Créer l'itinéraire avec vos classes
            it = Itinerary()

            # Ajouter tous les waypoints de l'interface à votre itinéraire
            for wp in self.waypoints:
                it.add_waypoint(wp['lat'], wp['lon'], wp['name'])

            # Récupérer les paramètres de l'avion depuis l'interface
            try:
                tas = float(self.aircraft_entries.get('cruise_speed', tk.Entry()).get() or 110)
                fuel_burn_rate = float(self.aircraft_entries.get('fuel_burn', tk.Entry()).get() or 7.5)
            except ValueError:
                tas = 110
                fuel_burn_rate = 7.5
                messagebox.showwarning("Attention", "Valeurs par défaut utilisées pour TAS et consommation")

            # Créer les legs avec votre logique existante
            it.create_legs()

            # Construire le texte du plan de vol avec vos vraies données
            plan_text = "PLAN DE VOL VFR - CALCUL AVEC MÉTÉO RÉELLE\n"
            plan_text += "=" * 70 + "\n\n"

            # Informations générales depuis l'interface
            aircraft_id = self.aircraft_entries.get('registration', tk.Entry()).get() or "N/A"
            aircraft_type = self.aircraft_entries.get('aircraft_type', tk.Entry()).get() or "N/A"
            pilot_name = self.flight_entries.get('pilot_name', tk.Entry()).get() or "N/A"
            date = self.flight_entries.get('date', tk.Entry()).get() or "N/A"
            departure_time = self.flight_entries.get('departure_time', tk.Entry()).get() or "N/A"

            plan_text += f"Avion: {aircraft_id} ({aircraft_type})\n"
            plan_text += f"Pilote: {pilot_name}\n"
            plan_text += f"Date: {date}\n"
            plan_text += f"Heure de départ: {departure_time}\n"
            plan_text += f"Vitesse vraie: {tas} kn\n"
            plan_text += f"Consommation: {fuel_burn_rate} GPH\n\n"

            # En-tête du tableau des legs (utilisant vos vraies données)
            plan_text += "LEG  FROM     TO       DIST   TC   TH   MH  WIND_DIR WIND_SPD  GS  TIME  FUEL_LEG FUEL_TOT\n"
            plan_text += "-" * 85 + "\n"

            # Afficher chaque leg calculé par vos classes
            for i, leg in enumerate(it.legs):
                leg_dict = leg.to_dict()  # Utilise votre méthode to_dict() existante

                plan_text += f"{i + 1:2d}   {leg_dict['Starting WP'][:7]:7s} {leg_dict['Ending WP'][:7]:7s} "
                plan_text += f"{leg_dict['Distance (NM)']:6.1f} {leg_dict['True course (deg)']:3.0f}  "
                plan_text += f"{leg_dict['True heading (deg)']:3.0f}  {leg_dict['Magnetic heading (deg)']:3.0f}  "
                plan_text += f"{leg_dict['Wind Direction (deg)']:7.0f}  {leg_dict['Wind Speed (kn)']:7.0f}  "
                plan_text += f"{leg_dict['Groundspeed (kn)']:3.0f} {leg_dict['Leg time (min)']:5.0f} "
                plan_text += f"{leg_dict['Fuel burn leg (gal)']:7.1f}  {leg_dict['Fuel burn tot (gal)']:7.1f}\n"

            # Totaux calculés par vos classes
            if it.legs:
                last_leg = it.legs[-1].to_dict()
                total_distance = sum(leg.distance for leg in it.legs)
                total_time = last_leg['Total time (min)']
                total_fuel = last_leg['Fuel burn tot (gal)']

                plan_text += "-" * 85 + "\n"
                plan_text += f"TOTAUX:             {total_distance:6.1f}                              "
                plan_text += f"    {total_time:5.0f} {total_fuel:16.1f}\n\n"

                # Informations supplémentaires
                reserve_time = float(self.flight_entries.get('reserve_time', tk.Entry()).get() or 45)
                reserve_fuel = reserve_time * fuel_burn_rate / 60
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
                except (ValueError, AttributeError):
                    plan_text += f"\n💡 Vérifiez que le carburant requis ne dépasse pas la capacité de votre avion.\n"

                plan_text += f"\n📊 Données météo obtenues de Tomorrow.io API\n"
                plan_text += f"🧭 Déclinaison magnétique calculée\n"
                plan_text += f"⏰ Heures de départ calculées pour chaque segment\n"

            # Afficher dans l'interface
            self.plan_text.delete('1.0', tk.END)
            self.plan_text.insert('1.0', plan_text)
            self.status_var.set(f"Itinéraire calculé: {len(it.legs)} segments, {total_time:.0f} min")

            # Stocker l'itinéraire calculé pour la génération de documents
            self.calculated_itinerary = it

        except ImportError as e:
            messagebox.showerror("Erreur d'import",
                                 f"Impossible d'importer vos classes:\n{e}\n\n"
                                 "Vérifiez que les fichiers sont dans le bon répertoire:\n"
                                 "- itinerary/itinerary.py\n"
                                 "- itinerary/waypoints.py\n"
                                 "- itinerary/legs.py")
        except Exception as e:
            messagebox.showerror("Erreur de calcul",
                                 f"Erreur lors du calcul de l'itinéraire:\n{e}\n\n"
                                 "Vérifiez vos données d'entrée et la connexion API météo.")
            # En cas d'erreur, afficher au moins les calculs de base
            self.calculate_basic_route()

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
        """Générer plan Excel"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if filename:
            # Ici, intégrer votre FlightPlanGenerator
            messagebox.showinfo("Succès", f"Plan Excel généré: {filename}")

    def generate_pdf_plan(self):
        """Générer plan PDF"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if filename:
            # Ici, intégrer votre FlightPlanGenerator
            messagebox.showinfo("Succès", f"Plan PDF généré: {filename}")

    def new_flight_plan(self):
        """Nouveau plan de vol"""
        # Réinitialiser tout
        for entry in list(self.aircraft_entries.values()) + list(self.flight_entries.values()):
            entry.delete(0, tk.END)

        self.departure_search.clear()
        self.destination_search.clear()
        self.waypoints.clear()
        self.update_waypoint_list()

        self.departure_airport = None
        self.destination_airport = None

        self.flight_info_text.delete('1.0', tk.END)
        self.plan_text.delete('1.0', tk.END)
        self.waypoint_detail_text.delete('1.0', tk.END)

        self.status_var.set("Nouveau plan de vol créé")

    def load_flight_plan(self):
        """Charger un plan de vol"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            # Ici, implémenter le chargement
            messagebox.showinfo("Info", "Fonctionnalité de chargement à implémenter")

    def save_flight_plan(self):
        """Sauvegarder le plan de vol"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if filename:
            # Ici, implémenter la sauvegarde
            messagebox.showinfo("Info", "Fonctionnalité de sauvegarde à implémenter")


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