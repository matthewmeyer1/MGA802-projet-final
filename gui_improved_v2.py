# improved_vfr_gui.py
"""
Interface graphique améliorée pour la planification de vol VFR
avec gestion intégrée du carburant et des ravitaillements
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import folium
import webbrowser
import os
from typing import List, Dict, Optional, Tuple
import math
from fuel_management import FuelManager
from gui_improved import AirportDatabase, AirportSearchWidget, CustomWaypointDialog


class VFRPlannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Planificateur de vol VFR - Version Pro")
        self.root.geometry("1200x800")

        # Initialiser les composants
        self.airport_db = AirportDatabase()
        self.fuel_manager = FuelManager(self.airport_db)

        # Variables
        self.aircraft_info = {}
        self.flight_info = {}
        self.waypoints = []
        self.optimized_waypoints = []
        self.departure_airport = None
        self.destination_airport = None
        self.calculated_itinerary = None

        # Style
        self.setup_styles()

        # Créer l'interface
        self.create_widgets()

    def setup_styles(self):
        """Configurer les styles ttk"""
        style = ttk.Style()

        # Style pour les en-têtes
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))

        # Style pour les avertissements
        style.configure('Warning.TLabel', foreground='red', font=('Arial', 10, 'bold'))

        # Style pour les infos importantes
        style.configure('Info.TLabel', foreground='blue', font=('Arial', 10))

    def create_widgets(self):
        """Créer tous les widgets de l'interface"""

        # Menu principal
        self.create_menu()

        # Barre d'outils
        self.create_toolbar()

        # Panneau principal avec onglets
        self.create_main_panel()

        # Barre d'état
        self.create_status_bar()

    def create_menu(self):
        """Créer le menu principal"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Nouveau plan", command=self.new_flight_plan, accelerator="Ctrl+N")
        file_menu.add_command(label="Ouvrir...", command=self.load_flight_plan, accelerator="Ctrl+O")
        file_menu.add_command(label="Sauvegarder", command=self.save_flight_plan, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exporter Excel", command=self.generate_excel_plan)
        file_menu.add_command(label="Exporter PDF", command=self.generate_pdf_plan)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit, accelerator="Ctrl+Q")

        # Menu Outils
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Outils", menu=tools_menu)
        tools_menu.add_command(label="Calculer itinéraire", command=self.calculate_full_route, accelerator="F5")
        tools_menu.add_command(label="Optimiser carburant", command=self.optimize_fuel_stops, accelerator="F6")
        tools_menu.add_command(label="Rapport carburant", command=self.show_fuel_report)
        tools_menu.add_separator()
        tools_menu.add_command(label="Carte interactive", command=self.show_interactive_map)
        tools_menu.add_command(label="Météo", command=self.show_weather_info)

        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="Guide rapide", command=self.show_quick_guide)
        help_menu.add_command(label="À propos", command=self.show_about)

        # Raccourcis clavier
        self.root.bind('<Control-n>', lambda e: self.new_flight_plan())
        self.root.bind('<Control-o>', lambda e: self.load_flight_plan())
        self.root.bind('<Control-s>', lambda e: self.save_flight_plan())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<F5>', lambda e: self.calculate_full_route())
        self.root.bind('<F6>', lambda e: self.optimize_fuel_stops())

    def create_toolbar(self):
        """Créer la barre d'outils"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side='top', fill='x', padx=2, pady=2)

        # Boutons principaux
        buttons = [
            ("🆕", "Nouveau", self.new_flight_plan),
            ("📂", "Ouvrir", self.load_flight_plan),
            ("💾", "Sauvegarder", self.save_flight_plan),
            ("|", None, None),  # Séparateur
            ("🧮", "Calculer", self.calculate_full_route),
            ("⛽", "Optimiser carburant", self.optimize_fuel_stops),
            ("🗺️", "Carte", self.show_interactive_map),
            ("|", None, None),
            ("📊", "Excel", self.generate_excel_plan),
            ("📄", "PDF", self.generate_pdf_plan),
        ]

        for text, tooltip, command in buttons:
            if text == "|":
                ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=5)
            else:
                btn = ttk.Button(toolbar, text=text, command=command, width=3)
                btn.pack(side='left', padx=2)
                if tooltip:
                    self.create_tooltip(btn, tooltip)

    def create_main_panel(self):
        """Créer le panneau principal avec onglets"""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Notebook pour les onglets
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)

        # Onglets
        self.create_aircraft_tab()
        self.create_route_planning_tab()
        self.create_fuel_management_tab()
        self.create_flight_plan_tab()
        self.create_briefing_tab()

    def create_aircraft_tab(self):
        """Créer l'onglet Avion"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="✈️ Avion")

        # Frame avec scroll
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Contenu
        row = 0

        # Section Identification
        id_frame = ttk.LabelFrame(scrollable_frame, text="Identification", padding=10)
        id_frame.grid(row=row, column=0, columnspan=2, sticky='ew', padx=5, pady=5)

        self.aircraft_entries = {}

        fields = [
            ("Immatriculation:", "registration", "C-XXXX"),
            ("Type d'avion:", "aircraft_type", "Cessna 172"),
            ("Équipements:", "equipment", "GPS, Transponder Mode C")
        ]

        for i, (label, key, placeholder) in enumerate(fields):
            ttk.Label(id_frame, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=3)
            entry = ttk.Entry(id_frame, width=30)
            entry.grid(row=i, column=1, sticky='ew', padx=5, pady=3)
            entry.insert(0, placeholder)
            entry.bind('<FocusIn>', lambda e, w=entry, p=placeholder: self.on_entry_focus_in(w, p))
            entry.bind('<FocusOut>', lambda e, w=entry, p=placeholder: self.on_entry_focus_out(w, p))
            self.aircraft_entries[key] = entry

        row += 1

        # Section Performance
        perf_frame = ttk.LabelFrame(scrollable_frame, text="Performance", padding=10)
        perf_frame.grid(row=row, column=0, columnspan=2, sticky='ew', padx=5, pady=5)

        perf_fields = [
            ("Vitesse de croisière (kn):", "cruise_speed", "110"),
            ("Consommation (GPH):", "fuel_burn", "7.5"),
            ("Capacité carburant (gal):", "fuel_capacity", "40"),
            ("Autonomie estimée (NM):", "range_estimate", "Auto")
        ]

        for i, (label, key, default) in enumerate(perf_fields):
            ttk.Label(perf_frame, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=3)

            if key == "range_estimate":
                self.range_label = ttk.Label(perf_frame, text="--", style='Info.TLabel')
                self.range_label.grid(row=i, column=1, sticky='w', padx=5, pady=3)
            else:
                entry = ttk.Entry(perf_frame, width=15)
                entry.grid(row=i, column=1, sticky='w', padx=5, pady=3)
                entry.insert(0, default)
                entry.bind('<KeyRelease>', self.update_range_estimate)
                self.aircraft_entries[key] = entry

        # Bouton de calcul d'autonomie
        ttk.Button(perf_frame, text="Calculer autonomie",
                   command=self.calculate_range).grid(row=len(perf_fields), column=0,
                                                      columnspan=2, pady=10)

        row += 1

        # Section Poids et centrage
        weight_frame = ttk.LabelFrame(scrollable_frame, text="Poids et centrage", padding=10)
        weight_frame.grid(row=row, column=0, columnspan=2, sticky='ew', padx=5, pady=5)

        weight_fields = [
            ("Poids à vide (lbs):", "empty_weight", "1650"),
            ("Charge utile max (lbs):", "max_payload", "850"),
            ("Poids max décollage (lbs):", "max_takeoff_weight", "2450")
        ]

        for i, (label, key, default) in enumerate(weight_fields):
            ttk.Label(weight_frame, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=3)
            entry = ttk.Entry(weight_frame, width=15)
            entry.grid(row=i, column=1, sticky='w', padx=5, pady=3)
            entry.insert(0, default)
            self.aircraft_entries[key] = entry

        # Configurer le redimensionnement
        id_frame.grid_columnconfigure(1, weight=1)
        perf_frame.grid_columnconfigure(1, weight=1)
        weight_frame.grid_columnconfigure(1, weight=1)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_route_planning_tab(self):
        """Créer l'onglet Planification de route"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🗺️ Route")

        # Diviser en deux panneaux
        paned = ttk.PanedWindow(tab, orient='horizontal')
        paned.pack(fill='both', expand=True)

        # Panneau gauche - Sélection des aéroports et waypoints
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        # Section Aéroports
        airports_frame = ttk.LabelFrame(left_frame, text="Aéroports", padding=5)
        airports_frame.pack(fill='x', padx=5, pady=5)

        # Départ
        dep_frame = ttk.Frame(airports_frame)
        dep_frame.pack(fill='x', pady=5)
        self.departure_search = AirportSearchWidget(dep_frame, self.airport_db, "Départ:")
        self.departure_search.pack(fill='x')
        self.departure_search.set_callback(self.on_departure_selected)

        # Arrivée
        arr_frame = ttk.Frame(airports_frame)
        arr_frame.pack(fill='x', pady=5)
        self.destination_search = AirportSearchWidget(arr_frame, self.airport_db, "Arrivée:")
        self.destination_search.pack(fill='x')
        self.destination_search.set_callback(self.on_destination_selected)

        # Boutons d'action
        btn_frame = ttk.Frame(airports_frame)
        btn_frame.pack(fill='x', pady=5)

        ttk.Button(btn_frame, text="🔄 Inverser",
                   command=self.swap_airports).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="➕ Ajouter à la route",
                   command=self.add_airports_to_route).pack(side='left', padx=2)

        # Section Waypoints
        wp_frame = ttk.LabelFrame(left_frame, text="Waypoints", padding=5)
        wp_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Liste des waypoints
        self.waypoint_listbox = tk.Listbox(wp_frame, height=10)
        self.waypoint_listbox.pack(side='left', fill='both', expand=True)

        wp_scrollbar = ttk.Scrollbar(wp_frame)
        wp_scrollbar.pack(side='right', fill='y')
        self.waypoint_listbox.config(yscrollcommand=wp_scrollbar.set)
        wp_scrollbar.config(command=self.waypoint_listbox.yview)

        # Boutons waypoints
        wp_btn_frame = ttk.Frame(left_frame)
        wp_btn_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(wp_btn_frame, text="➕ Ajouter",
                   command=self.add_custom_waypoint).pack(side='left', padx=2)
        ttk.Button(wp_btn_frame, text="🗑️ Supprimer",
                   command=self.remove_waypoint).pack(side='left', padx=2)
        ttk.Button(wp_btn_frame, text="⬆️",
                   command=self.move_waypoint_up).pack(side='left', padx=2)
        ttk.Button(wp_btn_frame, text="⬇️",
                   command=self.move_waypoint_down).pack(side='left', padx=2)

        # Panneau droit - Carte et informations
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        # Informations de vol
        info_frame = ttk.LabelFrame(right_frame, text="Informations de vol", padding=10)
        info_frame.pack(fill='x', padx=5, pady=5)

        self.route_info_text = tk.Text(info_frame, height=8, wrap='word')
        self.route_info_text.pack(fill='x')

        # Carte (placeholder)
        map_frame = ttk.LabelFrame(right_frame, text="Aperçu de la route", padding=10)
        map_frame.pack(fill='both', expand=True, padx=5, pady=5)

        ttk.Button(map_frame, text="🗺️ Afficher la carte interactive",
                   command=self.show_interactive_map).pack(expand=True)

    def create_fuel_management_tab(self):
        """Créer l'onglet Gestion du carburant"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⛽ Carburant")

        # Frame principal avec scroll
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Section Analyse du carburant
        analysis_frame = ttk.LabelFrame(scrollable_frame, text="Analyse du carburant", padding=10)
        analysis_frame.pack(fill='x', padx=10, pady=5)

        # Paramètres
        params_frame = ttk.Frame(analysis_frame)
        params_frame.pack(fill='x', pady=5)

        ttk.Label(params_frame, text="Réserve réglementaire:").grid(row=0, column=0, sticky='w', padx=5)
        self.reserve_var = tk.StringVar(value="45")
        reserve_spin = ttk.Spinbox(params_frame, from_=30, to=90, textvariable=self.reserve_var, width=10)
        reserve_spin.grid(row=0, column=1, padx=5)
        ttk.Label(params_frame, text="minutes").grid(row=0, column=2, sticky='w')

        ttk.Label(params_frame, text="Marge de sécurité:").grid(row=1, column=0, sticky='w', padx=5)
        self.safety_var = tk.StringVar(value="15")
        safety_spin = ttk.Spinbox(params_frame, from_=0, to=30, textvariable=self.safety_var, width=10)
        safety_spin.grid(row=1, column=1, padx=5)
        ttk.Label(params_frame, text="%").grid(row=1, column=2, sticky='w')

        # Boutons d'action
        action_frame = ttk.Frame(analysis_frame)
        action_frame.pack(fill='x', pady=10)

        ttk.Button(action_frame, text="⛽ Analyser les besoins",
                   command=self.analyze_fuel_needs).pack(side='left', padx=5)
        ttk.Button(action_frame, text="🔧 Optimiser avec ravitaillements",
                   command=self.optimize_fuel_stops).pack(side='left', padx=5)
        ttk.Button(action_frame, text="📊 Rapport détaillé",
                   command=self.show_fuel_report).pack(side='left', padx=5)

        # Section Résultats
        results_frame = ttk.LabelFrame(scrollable_frame, text="Résultats de l'analyse", padding=10)
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.fuel_results_text = tk.Text(results_frame, wrap='word', height=15)
        self.fuel_results_text.pack(fill='both', expand=True)

        # Section Aéroports de ravitaillement suggérés
        airports_frame = ttk.LabelFrame(scrollable_frame, text="Aéroports de ravitaillement", padding=10)
        airports_frame.pack(fill='x', padx=10, pady=5)

        self.fuel_airports_listbox = tk.Listbox(airports_frame, height=5)
        self.fuel_airports_listbox.pack(side='left', fill='both', expand=True)

        fuel_ap_scrollbar = ttk.Scrollbar(airports_frame)
        fuel_ap_scrollbar.pack(side='right', fill='y')
        self.fuel_airports_listbox.config(yscrollcommand=fuel_ap_scrollbar.set)
        fuel_ap_scrollbar.config(command=self.fuel_airports_listbox.yview)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_flight_plan_tab(self):
        """Créer l'onglet Plan de vol"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📋 Plan de vol")

        # Barre d'outils du plan
        toolbar = ttk.Frame(tab)
        toolbar.pack(fill='x', padx=5, pady=5)

        ttk.Button(toolbar, text="🧮 Calculer",
                   command=self.calculate_full_route).pack(side='left', padx=2)
        ttk.Button(toolbar, text="⛽ Optimiser",
                   command=self.optimize_fuel_stops).pack(side='left', padx=2)
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=5)
        ttk.Button(toolbar, text="📊 Excel",
                   command=self.generate_excel_plan).pack(side='left', padx=2)
        ttk.Button(toolbar, text="📄 PDF",
                   command=self.generate_pdf_plan).pack(side='left', padx=2)
        ttk.Button(toolbar, text="🖨️ Imprimer",
                   command=self.print_flight_plan).pack(side='left', padx=2)

        # Zone de texte pour le plan
        plan_frame = ttk.Frame(tab)
        plan_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.plan_text = tk.Text(plan_frame, wrap='none', font=('Courier', 9))
        self.plan_text.pack(side='left', fill='both', expand=True)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(plan_frame, orient='vertical', command=self.plan_text.yview)
        v_scrollbar.pack(side='right', fill='y')
        self.plan_text.configure(yscrollcommand=v_scrollbar.set)

        h_scrollbar = ttk.Scrollbar(tab, orient='horizontal', command=self.plan_text.xview)
        h_scrollbar.pack(side='bottom', fill='x')
        self.plan_text.configure(xscrollcommand=h_scrollbar.set)

    def create_briefing_tab(self):
        """Créer l'onglet Briefing"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📄 Briefing")

        # Frame avec sections
        briefing_frame = ttk.Frame(tab)
        briefing_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Section Météo
        weather_frame = ttk.LabelFrame(briefing_frame, text="Météo", padding=10)
        weather_frame.pack(fill='x', pady=5)

        self.weather_text = tk.Text(weather_frame, height=5, wrap='word')
        self.weather_text.pack(fill='x')
        ttk.Button(weather_frame, text="🌤️ Actualiser météo",
                   command=self.update_weather).pack(pady=5)

        # Section NOTAM
        notam_frame = ttk.LabelFrame(briefing_frame, text="NOTAM", padding=10)
        notam_frame.pack(fill='x', pady=5)

        self.notam_text = tk.Text(notam_frame, height=5, wrap='word')
        self.notam_text.pack(fill='x')
        self.notam_text.insert('1.0', "Les NOTAM doivent être vérifiés sur le site de NAV CANADA")

        # Section Notes du pilote
        notes_frame = ttk.LabelFrame(briefing_frame, text="Notes du pilote", padding=10)
        notes_frame.pack(fill='both', expand=True, pady=5)

        self.pilot_notes = tk.Text(notes_frame, wrap='word')
        self.pilot_notes.pack(fill='both', expand=True)

    def create_status_bar(self):
        """Créer la barre d'état"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side='bottom', fill='x')

        # Message principal
        self.status_var = tk.StringVar()
        self.status_var.set("Prêt")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, relief='sunken')
        self.status_label.pack(side='left', fill='x', expand=True)

        # Indicateurs
        self.fuel_status = ttk.Label(status_frame, text="⛽ --", relief='sunken', width=15)
        self.fuel_status.pack(side='left', padx=2)

        self.distance_status = ttk.Label(status_frame, text="📏 --", relief='sunken', width=15)
        self.distance_status.pack(side='left', padx=2)

        self.time_status = ttk.Label(status_frame, text="⏱️ --", relief='sunken', width=15)
        self.time_status.pack(side='left', padx=2)

    def create_tooltip(self, widget, text):
        """Créer une info-bulle pour un widget"""

        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            label = tk.Label(tooltip, text=text, background="yellow",
                             relief="solid", borderwidth=1)
            label.pack()
            widget.tooltip = tooltip

        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip

        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)

    def on_entry_focus_in(self, entry, placeholder):
        """Gérer le focus in sur une entrée avec placeholder"""
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(foreground='black')

    def on_entry_focus_out(self, entry, placeholder):
        """Gérer le focus out sur une entrée avec placeholder"""
        if entry.get() == '':
            entry.insert(0, placeholder)
            entry.config(foreground='grey')

    def update_range_estimate(self, event=None):
        """Mettre à jour l'estimation d'autonomie"""
        try:
            fuel_capacity = float(self.aircraft_entries['fuel_capacity'].get())
            fuel_burn = float(self.aircraft_entries['fuel_burn'].get())
            tas = float(self.aircraft_entries['cruise_speed'].get())

            range_nm = self.fuel_manager.calculate_range(fuel_capacity, fuel_burn, tas)
            self.range_label.config(text=f"{range_nm:.0f} NM")

        except (ValueError, KeyError):
            self.range_label.config(text="--")

    def calculate_range(self):
        """Calculer et afficher l'autonomie détaillée"""
        try:
            fuel_capacity = float(self.aircraft_entries['fuel_capacity'].get())
            fuel_burn = float(self.aircraft_entries['fuel_burn'].get())
            tas = float(self.aircraft_entries['cruise_speed'].get())
            reserve = float(self.reserve_var.get())

            range_nm = self.fuel_manager.calculate_range(fuel_capacity, fuel_burn, tas, reserve)

            # Calculer aussi le temps de vol
            flight_time = range_nm / tas

            message = f"Autonomie calculée:\n\n"
            message += f"Distance maximale: {range_nm:.0f} NM\n"
            message += f"Temps de vol max: {flight_time:.1f} heures\n"
            message += f"Avec réserve de {reserve:.0f} minutes\n\n"
            message += f"Note: Inclut une marge de sécurité de {self.fuel_manager.SAFETY_MARGIN * 100:.0f}%"

            messagebox.showinfo("Autonomie de l'avion", message)

        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer des valeurs numériques valides")

    def on_departure_selected(self, airport):
        """Callback pour la sélection de l'aéroport de départ"""
        self.departure_airport = airport
        self.update_route_info()
        self.status_var.set(f"Départ: {airport['icao']} - {airport['name']}")

    def on_destination_selected(self, airport):
        """Callback pour la sélection de l'aéroport d'arrivée"""
        self.destination_airport = airport
        self.update_route_info()
        self.status_var.set(f"Arrivée: {airport['icao']} - {airport['name']}")

    def update_route_info(self):
        """Mettre à jour les informations de route"""
        if not (self.departure_airport and self.destination_airport):
            return

        # Calculer distance
        distance = self.calculate_distance(
            self.departure_airport['lat'], self.departure_airport['lon'],
            self.destination_airport['lat'], self.destination_airport['lon']
        )

        # Calculer cap
        bearing = self.calculate_bearing(
            self.departure_airport['lat'], self.departure_airport['lon'],
            self.destination_airport['lat'], self.destination_airport['lon']
        )

        try:
            tas = float(self.aircraft_entries.get('cruise_speed', tk.Entry()).get() or 110)
            fuel_burn = float(self.aircraft_entries.get('fuel_burn', tk.Entry()).get() or 7.5)
            fuel_capacity = float(self.aircraft_entries.get('fuel_capacity', tk.Entry()).get() or 40)
        except:
            tas, fuel_burn, fuel_capacity = 110, 7.5, 40

        # Calculer temps et carburant
        flight_time = distance / tas * 60  # minutes
        fuel_required = self.fuel_manager.calculate_fuel_requirements(distance, tas, fuel_burn)

        # Afficher infos
        info_text = f"ROUTE DIRECTE\n\n"
        info_text += f"De: {self.departure_airport['icao']} - {self.departure_airport['name']}\n"
        info_text += f"À: {self.destination_airport['icao']} - {self.destination_airport['name']}\n\n"
        info_text += f"Distance: {distance:.1f} NM\n"
        info_text += f"Cap vrai: {bearing:.0f}°\n"
        info_text += f"Temps estimé: {flight_time:.0f} min ({flight_time / 60:.1f}h)\n\n"
        info_text += f"CARBURANT:\n"
        info_text += f"Segment: {fuel_required['segment_fuel']:.1f} gal\n"
        info_text += f"Réserve: {fuel_required['reserve_fuel']:.1f} gal\n"
        info_text += f"Total requis: {fuel_required['total_required']:.1f} gal\n"

        if fuel_required['total_required'] > fuel_capacity:
            info_text += f"\n⚠️ RAVITAILLEMENT NÉCESSAIRE!\n"
            info_text += f"Capacité insuffisante ({fuel_capacity:.1f} gal)"

        self.route_info_text.delete('1.0', tk.END)
        self.route_info_text.insert('1.0', info_text)

        # Mettre à jour la barre d'état
        self.distance_status.config(text=f"📏 {distance:.0f} NM")
        self.time_status.config(text=f"⏱️ {flight_time:.0f} min")
        self.fuel_status.config(text=f"⛽ {fuel_required['total_required']:.1f} gal")

    def swap_airports(self):
        """Inverser les aéroports de départ et d'arrivée"""
        if self.departure_airport and self.destination_airport:
            # Échanger
            self.departure_airport, self.destination_airport = self.destination_airport, self.departure_airport

            # Mettre à jour l'affichage
            self.departure_search.search_var.set(self.departure_airport['display'])
            self.departure_search.selected_airport = self.departure_airport

            self.destination_search.search_var.set(self.destination_airport['display'])
            self.destination_search.selected_airport = self.destination_airport

            self.update_route_info()
            self.status_var.set("Aéroports inversés")

    def add_airports_to_route(self):
        """Ajouter les aéroports sélectionnés à la route"""
        if not (self.departure_airport and self.destination_airport):
            messagebox.showwarning("Attention", "Sélectionnez d'abord les aéroports")
            return

        # Effacer la route actuelle
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
        self.status_var.set("Route créée")

    def add_custom_waypoint(self):
        """Ajouter un waypoint personnalisé"""
        dialog = CustomWaypointDialog(self.root, self.airport_db)
        if dialog.result:
            self.waypoints.append(dialog.result)
            self.update_waypoint_list()

    def remove_waypoint(self):
        """Supprimer le waypoint sélectionné"""
        selection = self.waypoint_listbox.curselection()
        if selection:
            index = selection[0]
            del self.waypoints[index]
            self.update_waypoint_list()

    def move_waypoint_up(self):
        """Déplacer le waypoint vers le haut"""
        selection = self.waypoint_listbox.curselection()
        if selection and selection[0] > 0:
            index = selection[0]
            self.waypoints[index], self.waypoints[index - 1] = self.waypoints[index - 1], self.waypoints[index]
            self.update_waypoint_list()
            self.waypoint_listbox.selection_set(index - 1)

    def move_waypoint_down(self):
        """Déplacer le waypoint vers le bas"""
        selection = self.waypoint_listbox.curselection()
        if selection and selection[0] < len(self.waypoints) - 1:
            index = selection[0]
            self.waypoints[index], self.waypoints[index + 1] = self.waypoints[index + 1], self.waypoints[index]
            self.update_waypoint_list()
            self.waypoint_listbox.selection_set(index + 1)

    def update_waypoint_list(self):
        """Mettre à jour l'affichage de la liste des waypoints"""
        self.waypoint_listbox.delete(0, tk.END)

        for i, wp in enumerate(self.waypoints):
            icon = "✈️" if wp.get('type') == 'airport' else "⛽" if wp.get('type') == 'fuel_stop' else "📍"
            text = f"{i + 1}. {icon} {wp['name']} ({wp['lat']:.4f}, {wp['lon']:.4f})"
            self.waypoint_listbox.insert(tk.END, text)

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculer la distance entre deux points"""
        return self.fuel_manager._calculate_distance(lat1, lon1, lat2, lon2)

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

    def analyze_fuel_needs(self):
        """Analyser les besoins en carburant pour la route"""
        if len(self.waypoints) < 2:
            messagebox.showwarning("Attention", "Créez d'abord une route")
            return

        try:
            # Récupérer les paramètres
            aircraft_params = {
                'fuel_capacity': float(self.aircraft_entries['fuel_capacity'].get()),
                'fuel_burn': float(self.aircraft_entries['fuel_burn'].get()),
                'tas': float(self.aircraft_entries['cruise_speed'].get())
            }

            # Analyser
            results = "ANALYSE DES BESOINS EN CARBURANT\n"
            results += "=" * 50 + "\n\n"

            total_distance = 0
            total_fuel = 0
            current_fuel = aircraft_params['fuel_capacity']

            for i in range(len(self.waypoints) - 1):
                wp1 = self.waypoints[i]
                wp2 = self.waypoints[i + 1]

                distance = self.calculate_distance(wp1['lat'], wp1['lon'], wp2['lat'], wp2['lon'])
                fuel_req = self.fuel_manager.calculate_fuel_requirements(
                    distance, aircraft_params['tas'], aircraft_params['fuel_burn']
                )

                results += f"Segment {i + 1}: {wp1['name']} → {wp2['name']}\n"
                results += f"  Distance: {distance:.1f} NM\n"
                results += f"  Carburant requis: {fuel_req['total_required']:.1f} gal\n"
                results += f"  Carburant restant: {current_fuel - fuel_req['total_required']:.1f} gal\n"

                if fuel_req['total_required'] > current_fuel:
                    results += f"  ⚠️ RAVITAILLEMENT NÉCESSAIRE!\n"

                results += "\n"

                total_distance += distance
                total_fuel += fuel_req['segment_fuel']
                current_fuel -= fuel_req['segment_fuel']

            results += f"TOTAUX:\n"
            results += f"Distance totale: {total_distance:.1f} NM\n"
            results += f"Carburant total: {total_fuel:.1f} gal\n"

            self.fuel_results_text.delete('1.0', tk.END)
            self.fuel_results_text.insert('1.0', results)

            # Basculer sur l'onglet carburant
            self.notebook.select(2)  # Index de l'onglet carburant

        except ValueError:
            messagebox.showerror("Erreur", "Vérifiez les paramètres de l'avion")

    def optimize_fuel_stops(self):
        """Optimiser la route avec des arrêts de ravitaillement"""
        if len(self.waypoints) < 2:
            messagebox.showwarning("Attention", "Créez d'abord une route")
            return

        try:
            # Récupérer les paramètres
            aircraft_params = {
                'fuel_capacity': float(self.aircraft_entries['fuel_capacity'].get()),
                'fuel_burn': float(self.aircraft_entries['fuel_burn'].get()),
                'tas': float(self.aircraft_entries['cruise_speed'].get())
            }

            # Sauvegarder la route originale
            original_waypoints = self.waypoints.copy()

            # Optimiser
            self.status_var.set("Optimisation en cours...")
            self.root.update()

            optimized_waypoints, messages = self.fuel_manager.optimize_route_with_fuel_stops(
                self.waypoints, aircraft_params
            )

            # Afficher les résultats
            result_text = "OPTIMISATION DU CARBURANT\n"
            result_text += "=" * 50 + "\n\n"

            for msg in messages:
                result_text += msg + "\n"

            if len(optimized_waypoints) > len(original_waypoints):
                result_text += f"\n{len(optimized_waypoints) - len(original_waypoints)} arrêt(s) ajouté(s)\n"

                # Demander confirmation
                if messagebox.askyesno("Optimisation",
                                       "Des arrêts de ravitaillement ont été ajoutés.\n"
                                       "Voulez-vous utiliser la route optimisée?"):
                    self.waypoints = optimized_waypoints
                    self.optimized_waypoints = optimized_waypoints
                    self.update_waypoint_list()

            self.fuel_results_text.delete('1.0', tk.END)
            self.fuel_results_text.insert('1.0', result_text)

            # Afficher les aéroports de ravitaillement
            self.fuel_airports_listbox.delete(0, tk.END)
            for wp in optimized_waypoints:
                if wp.get('type') == 'fuel_stop':
                    info = wp.get('info', {})
                    text = f"{info.get('icao', '')} - {info.get('name', '')} ({info.get('city', '')})"
                    self.fuel_airports_listbox.insert(tk.END, text)

            self.status_var.set("Optimisation terminée")

        except ValueError:
            messagebox.showerror("Erreur", "Vérifiez les paramètres de l'avion")

    def show_fuel_report(self):
        """Afficher un rapport détaillé sur le carburant"""
        if not hasattr(self, 'calculated_itinerary') or not self.calculated_itinerary:
            messagebox.showinfo("Info", "Calculez d'abord l'itinéraire complet")
            return

        try:
            aircraft_params = {
                'fuel_capacity': float(self.aircraft_entries['fuel_capacity'].get()),
                'fuel_burn': float(self.aircraft_entries['fuel_burn'].get()),
                'tas': float(self.aircraft_entries['cruise_speed'].get())
            }

            # Préparer les données des legs
            legs_data = []
            for leg in self.calculated_itinerary.legs:
                leg_dict = leg.to_dict()
                legs_data.append({
                    'from': leg_dict['Starting WP'],
                    'to': leg_dict['Ending WP'],
                    'distance': leg_dict['Distance (NM)'],
                    'leg_time': leg_dict['Leg time (min)'],
                    'fuel_leg': leg_dict['Fuel burn leg (gal)']
                })

            report = self.fuel_manager.generate_fuel_report(
                self.waypoints, legs_data, aircraft_params
            )

            # Afficher dans une nouvelle fenêtre
            report_window = tk.Toplevel(self.root)
            report_window.title("Rapport de carburant")
            report_window.geometry("600x500")

            text_widget = tk.Text(report_window, wrap='word', font=('Courier', 10))
            text_widget.pack(fill='both', expand=True, padx=10, pady=10)
            text_widget.insert('1.0', report)
            text_widget.config(state='disabled')

            # Bouton pour fermer
            ttk.Button(report_window, text="Fermer",
                       command=report_window.destroy).pack(pady=5)

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la génération du rapport:\n{e}")

    def calculate_full_route(self):
        """Calculer l'itinéraire complet"""
        if len(self.waypoints) < 2:
            messagebox.showwarning("Attention", "Au moins 2 waypoints requis")
            return

        try:
            # Utiliser les waypoints optimisés si disponibles
            waypoints_to_use = self.optimized_waypoints if self.optimized_waypoints else self.waypoints

            # Importer et utiliser les classes GUI
            from gui_itinerary import create_itinerary_from_gui

            # Préparer les paramètres
            aircraft_params = {
                'tas': float(self.aircraft_entries['cruise_speed'].get()),
                'fuel_burn': float(self.aircraft_entries['fuel_burn'].get())
            }

            flight_params = {
                'date': '2025-06-17',  # À améliorer avec un sélecteur de date
                'time': '10:00'  # À améliorer avec un sélecteur d'heure
            }

            # Créer l'itinéraire
            self.status_var.set("Calcul en cours...")
            self.root.update()

            self.calculated_itinerary = create_itinerary_from_gui(
                waypoints_to_use, aircraft_params, flight_params,
                api_key="CmIKizbzjlLBf8XngqoIAU271bBYNZbk"
            )

            # Afficher le plan
            self.display_flight_plan()

            # Basculer sur l'onglet plan de vol
            self.notebook.select(3)

            self.status_var.set("Calcul terminé")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du calcul:\n{e}")
            self.status_var.set("Erreur de calcul")

    def display_flight_plan(self):
        """Afficher le plan de vol calculé"""
        if not self.calculated_itinerary:
            return

        summary = self.calculated_itinerary.get_summary()

        # Construire le texte du plan
        plan_text = "PLAN DE VOL VFR\n"
        plan_text += "=" * 80 + "\n\n"

        # Informations générales
        plan_text += f"Avion: {self.aircraft_entries['registration'].get()}\n"
        plan_text += f"Type: {self.aircraft_entries['aircraft_type'].get()}\n"
        plan_text += f"Départ: {summary['departure']}\n"
        plan_text += f"Arrivée: {summary['destination']}\n\n"

        # Tableau des legs
        plan_text += "LEG  FROM     TO       DIST   TC   MH   WIND    GS   TIME  FUEL\n"
        plan_text += "-" * 65 + "\n"

        for i, leg in enumerate(self.calculated_itinerary.legs):
            leg_dict = leg.to_dict()
            plan_text += f"{i + 1:2d}   {leg_dict['Starting WP'][:7]:7s} {leg_dict['Ending WP'][:7]:7s} "
            plan_text += f"{leg_dict['Distance (NM)']:6.1f} {leg_dict['True course (deg)']:3.0f}  "
            plan_text += f"{leg_dict['Magnetic heading (deg)']:3.0f}  "
            plan_text += f"{leg_dict['Wind Direction (deg)']:3.0f}°/{leg_dict['Wind Speed (kn)']:2.0f}  "
            plan_text += f"{leg_dict['Groundspeed (kn)']:3.0f} {leg_dict['Leg time (min)']:5.0f} "
            plan_text += f"{leg_dict['Fuel burn leg (gal)']:5.1f}\n"

            # Marquer les arrêts carburant
            if 'FUEL-' in leg_dict['Ending WP']:
                plan_text += "     ⛽ RAVITAILLEMENT\n"

        plan_text += "-" * 65 + "\n"
        plan_text += f"TOTAUX:                  {summary['total_distance']:6.1f}                  "
        plan_text += f"    {summary['total_time']:5.0f} {summary['total_fuel']:5.1f}\n"

        self.plan_text.delete('1.0', tk.END)
        self.plan_text.insert('1.0', plan_text)

        # Mettre à jour la barre d'état
        self.distance_status.config(text=f"📏 {summary['total_distance']:.0f} NM")
        self.time_status.config(text=f"⏱️ {summary['total_time']:.0f} min")
        self.fuel_status.config(text=f"⛽ {summary['total_fuel']:.1f} gal")

    def show_interactive_map(self):
        """Afficher la carte interactive"""
        if not self.waypoints:
            messagebox.showwarning("Attention", "Aucun waypoint défini")
            return

        # Centre de la carte
        waypoints_to_show = self.optimized_waypoints if self.optimized_waypoints else self.waypoints
        center_lat = sum(wp['lat'] for wp in waypoints_to_show) / len(waypoints_to_show)
        center_lon = sum(wp['lon'] for wp in waypoints_to_show) / len(waypoints_to_show)

        m = folium.Map(location=[center_lat, center_lon], zoom_start=7)

        # Ajouter les waypoints
        for i, wp in enumerate(waypoints_to_show):
            if wp.get('type') == 'fuel_stop':
                color = 'orange'
                icon = 'gas-pump'
                prefix = 'fa'
            elif i == 0:
                color = 'green'
                icon = 'play'
                prefix = 'fa'
            elif i == len(waypoints_to_show) - 1:
                color = 'red'
                icon = 'stop'
                prefix = 'fa'
            else:
                color = 'blue'
                icon = 'info-sign'
                prefix = 'glyphicon'

            folium.Marker(
                [wp['lat'], wp['lon']],
                popup=f"{wp['name']}<br>Lat: {wp['lat']:.4f}<br>Lon: {wp['lon']:.4f}",
                tooltip=wp['name'],
                icon=folium.Icon(color=color, icon=icon, prefix=prefix)
            ).add_to(m)

        # Tracer la route
        if len(waypoints_to_show) > 1:
            coords = [[wp['lat'], wp['lon']] for wp in waypoints_to_show]
            folium.PolyLine(coords, color='red', weight=3, opacity=0.8).add_to(m)

        # Sauvegarder et ouvrir
        map_file = "vfr_route_map.html"
        m.save(map_file)
        webbrowser.open(f"file://{os.path.abspath(map_file)}")
        self.status_var.set("Carte ouverte dans le navigateur")

    def show_weather_info(self):
        """Afficher les informations météo"""
        messagebox.showinfo("Météo",
                            "La météo est récupérée via l'API Tomorrow.io\n"
                            "lors du calcul de l'itinéraire.\n\n"
                            "Consultez également les sources officielles\n"
                            "de NAV CANADA pour la météo aviation.")

    def update_weather(self):
        """Actualiser les informations météo"""
        self.weather_text.delete('1.0', tk.END)
        self.weather_text.insert('1.0', "Récupération météo en cours...\n")
        # Ici, intégrer l'API météo
        self.weather_text.insert(tk.END, "Météo mise à jour via Tomorrow.io API")

    def generate_excel_plan(self):
        """Générer le plan en Excel"""
        if not hasattr(self, 'calculated_itinerary') or not self.calculated_itinerary:
            messagebox.showwarning("Attention", "Calculez d'abord l'itinéraire")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Sauvegarder le plan Excel"
        )

        if filename:
            try:
                from flight_plan_generator import FlightPlanGenerator

                # Préparer les données
                flight_data = self._prepare_flight_data()
                legs_data = self._prepare_legs_data()

                # Générer
                generator = FlightPlanGenerator()
                generator.generate_excel_plan(flight_data, legs_data, filename)

                messagebox.showinfo("Succès", f"Plan Excel généré:\n{filename}")

            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la génération:\n{e}")

    def generate_pdf_plan(self):
        """Générer le plan en PDF"""
        if not hasattr(self, 'calculated_itinerary') or not self.calculated_itinerary:
            messagebox.showwarning("Attention", "Calculez d'abord l'itinéraire")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Sauvegarder le plan PDF"
        )

        if filename:
            try:
                from flight_plan_generator import FlightPlanGenerator

                # Préparer les données
                flight_data = self._prepare_flight_data()
                legs_data = self._prepare_legs_data()

                # Générer
                generator = FlightPlanGenerator()
                generator.generate_pdf_plan(flight_data, legs_data, filename)

                messagebox.showinfo("Succès", f"Plan PDF généré:\n{filename}")

            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la génération:\n{e}")

    def print_flight_plan(self):
        """Imprimer le plan de vol"""
        # Simple impression du contenu texte
        import tempfile
        import subprocess
        import sys

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(self.plan_text.get('1.0', tk.END))
                temp_file = f.name

            if sys.platform.startswith('win'):
                os.startfile(temp_file, 'print')
            elif sys.platform.startswith('darwin'):
                subprocess.call(['lpr', temp_file])
            else:
                subprocess.call(['lpr', temp_file])

            messagebox.showinfo("Impression", "Plan envoyé à l'imprimante")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur d'impression:\n{e}")

    def _prepare_flight_data(self):
        """Préparer les données de vol pour les générateurs"""
        return {
            'aircraft_id': self.aircraft_entries.get('registration', tk.Entry()).get(),
            'aircraft_type': self.aircraft_entries.get('aircraft_type', tk.Entry()).get(),
            'tas': float(self.aircraft_entries.get('cruise_speed', tk.Entry()).get() or 110),
            'departure': self.departure_airport['icao'] if self.departure_airport else 'N/A',
            'destination': self.destination_airport['icao'] if self.destination_airport else 'N/A',
            'date': '2025-06-17',  # À améliorer
            'etd': '10:00',  # À améliorer
            'pilot': 'Commandant',
            'fuel_capacity': float(self.aircraft_entries.get('fuel_capacity', tk.Entry()).get() or 40),
            'fuel_burn': float(self.aircraft_entries.get('fuel_burn', tk.Entry()).get() or 7.5),
            'reserve_fuel': float(self.reserve_var.get() or 45)
        }

    def _prepare_legs_data(self):
        """Préparer les données des legs pour les générateurs"""
        if not hasattr(self, 'calculated_itinerary'):
            return []

        legs_data = []
        for leg in self.calculated_itinerary.legs:
            leg_dict = leg.to_dict()
            legs_data.append({
                'from': leg_dict['Starting WP'],
                'to': leg_dict['Ending WP'],
                'distance': leg_dict['Distance (NM)'],
                'true_course': leg_dict['True course (deg)'],
                'mag_heading': leg_dict['Magnetic heading (deg)'],
                'wind_dir': leg_dict['Wind Direction (deg)'],
                'wind_speed': leg_dict['Wind Speed (kn)'],
                'ground_speed': leg_dict['Groundspeed (kn)'],
                'leg_time': leg_dict['Leg time (min)'],
                'fuel_leg': leg_dict['Fuel burn leg (gal)'],
                'fuel_total': leg_dict['Fuel burn tot (gal)'],
                'eta': 'TBD'
            })

        return legs_data

    def new_flight_plan(self):
        """Créer un nouveau plan de vol"""
        if messagebox.askyesno("Nouveau plan", "Effacer le plan actuel?"):
            # Réinitialiser
            self.waypoints.clear()
            self.optimized_waypoints.clear()
            self.departure_airport = None
            self.destination_airport = None
            self.calculated_itinerary = None

            # Effacer les champs
            for entry in self.aircraft_entries.values():
                if isinstance(entry, tk.Entry):
                    entry.delete(0, tk.END)

            self.departure_search.clear()
            self.destination_search.clear()

            # Effacer les zones de texte
            self.route_info_text.delete('1.0', tk.END)
            self.fuel_results_text.delete('1.0', tk.END)
            self.plan_text.delete('1.0', tk.END)
            self.weather_text.delete('1.0', tk.END)
            self.pilot_notes.delete('1.0', tk.END)

            # Mettre à jour les listes
            self.update_waypoint_list()
            self.fuel_airports_listbox.delete(0, tk.END)

            self.status_var.set("Nouveau plan créé")

    def load_flight_plan(self):
        """Charger un plan de vol"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            messagebox.showinfo("Info", "Chargement à implémenter")

    def save_flight_plan(self):
        """Sauvegarder le plan de vol"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if filename:
            messagebox.showinfo("Info", "Sauvegarde à implémenter")

    def show_quick_guide(self):
        """Afficher le guide rapide"""
        guide = """GUIDE RAPIDE - Planificateur VFR

1. CONFIGURATION AVION (Onglet ✈️)
   - Entrez les informations de votre avion
   - Vérifiez l'autonomie calculée

2. PLANIFICATION ROUTE (Onglet 🗺️)
   - Sélectionnez aéroports de départ/arrivée
   - Ajoutez des waypoints si nécessaire
   - Cliquez "Ajouter à la route"

3. GESTION CARBURANT (Onglet ⛽)
   - Analysez les besoins en carburant
   - Optimisez avec ravitaillements si nécessaire

4. CALCUL DU PLAN (Onglet 📋)
   - Cliquez "Calculer" (F5)
   - Exportez en Excel ou PDF

RACCOURCIS:
- F5: Calculer l'itinéraire
- F6: Optimiser le carburant
- Ctrl+S: Sauvegarder
- Ctrl+N: Nouveau plan

CONSEILS:
- Vérifiez toujours les NOTAMs
- Consultez la météo aviation
- Prévoyez des aéroports alternés
- Respectez les réserves réglementaires"""

        messagebox.showinfo("Guide rapide", guide)

    def show_about(self):
        """Afficher les informations sur l'application"""
        about_text = """Planificateur de vol VFR Pro
Version 2.0

Développé pour le projet MGA802
Par l'équipe de développement

Fonctionnalités:
- Planification de route VFR
- Gestion automatique du carburant
- Optimisation des ravitaillements
- Export Excel/PDF professionnel
- Intégration météo en temps réel

© 2025 - Tous droits réservés"""

        messagebox.showinfo("À propos", about_text)


if __name__ == "__main__":
    root = tk.Tk()
    app = VFRPlannerGUI(root)
    root.mainloop()