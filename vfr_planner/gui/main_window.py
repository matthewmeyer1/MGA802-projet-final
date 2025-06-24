"""
Fenêtre principale de l'application VFR Planner
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os

from .tabs import AircraftTab, AirportsTab, RouteTab, PlanTab
from .widgets import StatusBarWidget
from ..data.airport_db import AirportDatabase
from .. import __version__, __author__


class VFRPlannerGUI:
    """Fenêtre principale de l'application VFR Planner"""

    def __init__(self, root):
        self.root = root
        self.setup_window()

        # Initialiser la base de données d'aéroports
        self.airport_db = AirportDatabase()

        # Variables de l'application
        self.current_project_file = None
        self.unsaved_changes = False

        # Créer l'interface
        self.create_menu()
        self.create_widgets()
        self.setup_bindings()

        # Initialiser la barre d'état
        self.update_status_bar()

    def setup_window(self):
        """Configurer la fenêtre principale"""
        self.root.title(f"VFR Planner v{__version__}")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)

        # Icône (si disponible)
        try:
            # Charger icône depuis les ressources
            icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass  # Ignorer si pas d'icône

        # Configuration de fermeture
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_menu(self):
        """Créer la barre de menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Nouveau plan", command=self.new_project, accelerator="Ctrl+N")
        file_menu.add_command(label="Ouvrir...", command=self.open_project, accelerator="Ctrl+O")
        file_menu.add_command(label="Sauvegarder", command=self.save_project, accelerator="Ctrl+S")
        file_menu.add_command(label="Sauvegarder sous...", command=self.save_project_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exporter Excel...", command=self.export_excel)
        file_menu.add_command(label="Exporter PDF...", command=self.export_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.on_closing, accelerator="Ctrl+Q")

        # Menu Édition
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Édition", menu=edit_menu)
        edit_menu.add_command(label="Copier plan", command=self.copy_plan, accelerator="Ctrl+C")
        edit_menu.add_command(label="Préférences...", command=self.show_preferences)

        # Menu Outils
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Outils", menu=tools_menu)
        tools_menu.add_command(label="Calculer itinéraire", command=self.calculate_route)
        tools_menu.add_command(label="Vérifier météo", command=self.check_weather)
        tools_menu.add_command(label="Carte interactive", command=self.show_interactive_map)
        tools_menu.add_separator()
        tools_menu.add_command(label="Diagnostic système", command=self.system_diagnostic)
        tools_menu.add_command(label="Test API météo", command=self.test_weather_api)

        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="Guide d'utilisation", command=self.show_user_guide)
        help_menu.add_command(label="Raccourcis clavier", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="À propos", command=self.show_about)

    def create_widgets(self):
        """Créer les widgets principaux"""
        try:
            # Notebook pour les onglets
            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

            # Onglet 1: Aéronef
            self.aircraft_tab = AircraftTab(self.notebook, self)
            self.notebook.add(self.aircraft_tab, text="✈️ Aéronef")

            # Onglet 2: Aéroports
            self.airports_tab = AirportsTab(self.notebook, self)
            self.notebook.add(self.airports_tab, text="🛫 Aéroports")

            # Onglet 3: Itinéraire
            self.route_tab = RouteTab(self.notebook, self)
            self.notebook.add(self.route_tab, text="🗺️ Itinéraire")

            # Onglet 4: Plan de vol
            self.plan_tab = PlanTab(self.notebook, self)
            self.notebook.add(self.plan_tab, text="📋 Plan de vol")

            # Barre d'état
            self.status_bar = StatusBarWidget(self.root)
            self.status_bar.pack(side='bottom', fill='x')

            print("Widgets créés avec succès")

        except Exception as e:
            print(f"Erreur lors de la création des widgets: {e}")
            import traceback
            traceback.print_exc()

            # Créer une interface minimale en cas d'erreur
            error_label = tk.Label(self.root, text=f"Erreur d'initialisation: {e}")
            error_label.pack(expand=True)

            # Barre d'état minimale
            self.status_bar = StatusBarWidget(self.root)
            self.status_bar.pack(side='bottom', fill='x')
            self.status_bar.set_status(f"Erreur: {e}")

    def setup_bindings(self):
        """Configurer les raccourcis clavier"""
        self.root.bind('<Control-n>', lambda e: self.new_project())
        self.root.bind('<Control-o>', lambda e: self.open_project())
        self.root.bind('<Control-s>', lambda e: self.save_project())
        self.root.bind('<Control-Shift-S>', lambda e: self.save_project_as())
        self.root.bind('<Control-q>', lambda e: self.on_closing())
        self.root.bind('<Control-c>', lambda e: self.copy_plan())
        self.root.bind('<F5>', lambda e: self.calculate_route())
        self.root.bind('<F9>', lambda e: self.show_interactive_map())

        # Détecter les changements pour marquer comme modifié
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)

    def update_status_bar(self):
        """Mettre à jour la barre d'état"""
        # Statut API
        api_key = self.plan_tab.api_key_var.get().strip() if hasattr(self.plan_tab, 'api_key_var') else ""
        self.status_bar.set_api_status(bool(api_key))

        # Nombre d'aéroports
        stats = self.airport_db.get_filter_stats()
        self.status_bar.set_airports_count(stats['filtered'])

        # Message par défaut
        self.status_bar.set_status("Prêt - Configurez votre aéronef et sélectionnez vos aéroports")

    def on_tab_changed(self, event):
        """Appelé quand l'onglet change"""
        # Mettre à jour selon l'onglet actuel
        current_tab = self.notebook.index(self.notebook.select())

        if current_tab == 0:  # Aéronef
            self.status_bar.set_status("Configurez les paramètres de votre aéronef")
        elif current_tab == 1:  # Aéroports
            self.status_bar.set_status("Sélectionnez vos aéroports de départ et d'arrivée")
        elif current_tab == 2:  # Itinéraire
            self.status_bar.set_status("Définissez votre itinéraire détaillé")
        elif current_tab == 3:  # Plan
            self.status_bar.set_status("Calculez et exportez votre plan de vol")

    def mark_unsaved(self):
        """Marquer le projet comme modifié"""
        if not self.unsaved_changes:
            self.unsaved_changes = True
            title = self.root.title()
            if not title.endswith(" *"):
                self.root.title(title + " *")

    def mark_saved(self):
        """Marquer le projet comme sauvegardé"""
        self.unsaved_changes = False
        title = self.root.title()
        if title.endswith(" *"):
            self.root.title(title[:-2])

    # Actions du menu Fichier
    def new_project(self):
        """Créer un nouveau projet"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Nouveau projet",
                "Sauvegarder les modifications actuelles?"
            )
            if result is True:
                if not self.save_project():
                    return
            elif result is None:
                return

        # Réinitialiser tout avec vérifications
        try:
            self.aircraft_tab.clear_all()

            if hasattr(self.airports_tab, 'departure_search') and self.airports_tab.departure_search:
                self.airports_tab.departure_search.clear()
            if hasattr(self.airports_tab, 'destination_search') and self.airports_tab.destination_search:
                self.airports_tab.destination_search.clear()
            if hasattr(self.airports_tab, 'flight_info_text') and self.airports_tab.flight_info_text:
                self.airports_tab.flight_info_text.delete('1.0', tk.END)

            if hasattr(self.route_tab, 'clear_waypoints'):
                self.route_tab.clear_waypoints()
            if hasattr(self.route_tab, 'waypoint_detail_text') and self.route_tab.waypoint_detail_text:
                self.route_tab.waypoint_detail_text.delete('1.0', tk.END)

            if hasattr(self.plan_tab, 'plan_text') and self.plan_tab.plan_text:
                self.plan_tab.plan_text.delete('1.0', tk.END)
            if hasattr(self.plan_tab, 'calculated_itinerary'):
                self.plan_tab.calculated_itinerary = None

            self.current_project_file = None
            self.mark_saved()
            self.root.title(f"VFR Planner v{__version__} - Nouveau projet")
            self.status_bar.set_status("Nouveau projet créé")

        except Exception as e:
            print(f"Erreur lors de la réinitialisation: {e}")
            self.status_bar.set_status("Erreur lors de la création du nouveau projet")

    def open_project(self):
        """Ouvrir un projet"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Ouvrir projet",
                "Sauvegarder les modifications actuelles?"
            )
            if result is True:
                if not self.save_project():
                    return
            elif result is None:
                return

        filename = filedialog.askopenfilename(
            title="Ouvrir un projet VFR",
            filetypes=[("Projets VFR", "*.vfr"), ("JSON files", "*.json"), ("Tous", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)

                self.load_project_data(project_data)
                self.current_project_file = filename
                self.mark_saved()

                project_name = os.path.basename(filename)
                self.root.title(f"VFR Planner v{__version__} - {project_name}")
                self.status_bar.set_status(f"Projet ouvert: {project_name}")

            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'ouverture:\n{e}")

    def save_project(self):
        """Sauvegarder le projet"""
        if self.current_project_file:
            return self.save_project_to_file(self.current_project_file)
        else:
            return self.save_project_as()

    def save_project_as(self):
        """Sauvegarder le projet sous un nouveau nom"""
        filename = filedialog.asksaveasfilename(
            title="Sauvegarder le projet VFR",
            defaultextension=".vfr",
            filetypes=[("Projets VFR", "*.vfr"), ("JSON files", "*.json")]
        )

        if filename:
            return self.save_project_to_file(filename)
        return False

    def save_project_to_file(self, filename):
        """Sauvegarder vers un fichier spécifique"""
        try:
            project_data = self.get_project_data()

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)

            self.current_project_file = filename
            self.mark_saved()

            project_name = os.path.basename(filename)
            self.root.title(f"VFR Planner v{__version__} - {project_name}")
            self.status_bar.set_status(f"Projet sauvegardé: {project_name}")
            return True

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde:\n{e}")
            return False

    def get_project_data(self):
        """Obtenir les données du projet pour sauvegarde"""
        return {
            'version': __version__,
            'aircraft': self.aircraft_tab.get_aircraft_data(),
            'flight': self.aircraft_tab.get_flight_data(),
            'departure_airport': self.airports_tab.departure_airport,
            'destination_airport': self.airports_tab.destination_airport,
            'waypoints': self.route_tab.get_waypoints(),
            'api_key': self.plan_tab.api_key_var.get() if hasattr(self.plan_tab, 'api_key_var') else "",
            'saved_at': tk._default_root.tk.call('clock', 'format',
                                               tk._default_root.tk.call('clock', 'seconds'),
                                               '-format', '%Y-%m-%d %H:%M:%S')
        }

    def load_project_data(self, project_data):
        """Charger les données d'un projet"""
        try:
            # Charger aéronef
            aircraft_data = project_data.get('aircraft', {})
            for key, value in aircraft_data.items():
                if key in self.aircraft_tab.aircraft_entries:
                    entry = self.aircraft_tab.aircraft_entries[key]
                    entry.delete(0, tk.END)
                    entry.insert(0, str(value))

            # Charger vol
            flight_data = project_data.get('flight', {})
            for key, value in flight_data.items():
                if key in self.aircraft_tab.flight_entries:
                    entry = self.aircraft_tab.flight_entries[key]
                    entry.delete(0, tk.END)
                    entry.insert(0, str(value))

            # Charger aéroports avec vérifications
            if project_data.get('departure_airport') and hasattr(self.airports_tab, 'departure_search') and self.airports_tab.departure_search:
                self.airports_tab.departure_airport = project_data['departure_airport']
                self.airports_tab.departure_search.set_airport(project_data['departure_airport'])

            if project_data.get('destination_airport') and hasattr(self.airports_tab, 'destination_search') and self.airports_tab.destination_search:
                self.airports_tab.destination_airport = project_data['destination_airport']
                self.airports_tab.destination_search.set_airport(project_data['destination_airport'])

            # Charger waypoints
            waypoints = project_data.get('waypoints', [])
            if hasattr(self.route_tab, 'waypoints'):
                self.route_tab.waypoints = waypoints
                if hasattr(self.route_tab, 'update_waypoint_list'):
                    self.route_tab.update_waypoint_list()

            # Charger clé API
            api_key = project_data.get('api_key', '')
            if hasattr(self.plan_tab, 'api_key_var'):
                self.plan_tab.api_key_var.set(api_key)

            # Mettre à jour les affichages
            if hasattr(self.airports_tab, 'update_flight_info'):
                self.airports_tab.update_flight_info()
            self.update_status_bar()

        except Exception as e:
            print(f"Erreur lors du chargement des données: {e}")
            messagebox.showerror("Erreur", f"Erreur lors du chargement:\n{e}")

    def export_excel(self):
        """Exporter vers Excel"""
        self.plan_tab.export_excel()

    def export_pdf(self):
        """Exporter vers PDF"""
        self.plan_tab.export_pdf()

    def copy_plan(self):
        """Copier le plan de vol dans le presse-papier"""
        plan_content = self.plan_tab.plan_text.get('1.0', tk.END)
        if plan_content.strip():
            self.root.clipboard_clear()
            self.root.clipboard_append(plan_content)
            self.status_bar.set_status("Plan copié dans le presse-papier")
        else:
            messagebox.showwarning("Attention", "Aucun plan de vol à copier")

    def show_preferences(self):
        """Afficher les préférences"""
        messagebox.showinfo("Préférences", "Fonctionnalité à implémenter")

    # Actions du menu Outils
    def calculate_route(self):
        """Calculer l'itinéraire"""
        self.plan_tab.calculate_route()

    def check_weather(self):
        """Vérifier la météo"""
        waypoints = self.route_tab.get_waypoints()
        if not waypoints:
            messagebox.showwarning("Attention", "Aucun waypoint défini")
            return

        try:
            from ..calculations.weather import WeatherService
            from ..models.waypoint import Waypoint
            import datetime

            api_key = self.plan_tab.api_key_var.get().strip()
            if not api_key:
                messagebox.showwarning("Attention", "Configurez d'abord votre clé API météo")
                return

            weather_service = WeatherService(api_key)

            # Analyser la météo pour la route
            wp_objects = [Waypoint(wp['lat'], wp['lon'], wp['name']) for wp in waypoints]
            analysis = weather_service.analyze_weather_for_route(wp_objects, datetime.datetime.now())

            if 'error' in analysis:
                raise Exception(analysis['error'])

            # Afficher les résultats
            self.show_weather_analysis(analysis)

        except Exception as e:
            messagebox.showerror("Erreur météo", f"Erreur lors de l'analyse météo:\n{e}")

    def show_weather_analysis(self, analysis):
        """Afficher l'analyse météo dans une fenêtre"""
        weather_window = tk.Toplevel(self.root)
        weather_window.title("Analyse météorologique")
        weather_window.geometry("600x500")

        # Zone de texte avec scrollbar
        text_frame = ttk.Frame(weather_window)
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)

        weather_text = tk.Text(text_frame, wrap='word')
        weather_text.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=weather_text.yview)
        scrollbar.pack(side='right', fill='y')
        weather_text.configure(yscrollcommand=scrollbar.set)

        # Formater le contenu
        content = "ANALYSE MÉTÉOROLOGIQUE DE LA ROUTE\n"
        content += "=" * 50 + "\n\n"

        for wp_weather in analysis['route_weather']:
            content += f"Waypoint: {wp_weather['waypoint']} à {wp_weather['time']}\n"
            weather = wp_weather['weather']
            content += f"  Vent: {weather['wind_direction']:.0f}°/{weather['wind_speed']:.0f}kn\n"
            content += f"  Température: {weather['temperature']:.0f}°C\n"
            content += f"  Visibilité: {weather['visibility']:.1f}km\n"
            content += f"  Précipitations: {weather['precipitation']:.1f}mm/h\n\n"

        if 'analysis' in analysis and analysis['analysis']:
            content += "RÉSUMÉ:\n"
            anal = analysis['analysis']
            content += f"Vent moyen: {anal['wind_speed']['avg']:.0f}kn\n"
            content += f"Visibilité minimale: {anal['visibility']['min']:.1f}km\n"

            if anal['alerts']:
                content += "\nALERTES:\n"
                for alert in anal['alerts']:
                    content += f"⚠️ {alert}\n"

        weather_text.insert('1.0', content)
        weather_text.configure(state='disabled')

    def show_interactive_map(self):
        """Afficher la carte interactive"""
        self.plan_tab.show_map()

    def system_diagnostic(self):
        """Afficher un diagnostic du système"""
        import sys
        import platform

        diagnostic = f"""DIAGNOSTIC SYSTÈME VFR PLANNER

Version VFR Planner: {__version__}
Auteurs: {__author__}

Système:
- OS: {platform.system()} {platform.release()}
- Python: {sys.version.split()[0]}
- Tkinter: Disponible

Base de données:
- Aéroports chargés: {len(self.airport_db)}
- Fichier CSV: {"✅" if self.airport_db.csv_path else "❌"}

Modules requis:
"""
        # Vérifier les modules
        modules = [
            ('pandas', 'Manipulation de données'),
            ('folium', 'Cartes interactives'),
            ('requests', 'API météo'),
            ('openpyxl', 'Export Excel'),
            ('reportlab', 'Export PDF'),
            ('geopy', 'Calculs géographiques'),
            ('pytz', 'Fuseaux horaires')
        ]

        for module, description in modules:
            try:
                __import__(module)
                diagnostic += f"✅ {module}: {description}\n"
            except ImportError:
                diagnostic += f"❌ {module}: {description} (manquant)\n"

        messagebox.showinfo("Diagnostic système", diagnostic)

    def test_weather_api(self):
        """Tester l'API météo"""
        self.plan_tab.test_api()

    # Actions du menu Aide
    def show_user_guide(self):
        """Afficher le guide d'utilisation"""
        guide_text = """GUIDE D'UTILISATION VFR PLANNER

1. CONFIGURATION DE L'AÉRONEF
   - Sélectionnez un aéronef prédéfini ou saisissez vos paramètres
   - Remplissez les informations de vol (date, heure, pilote, etc.)

2. SÉLECTION DES AÉROPORTS
   - Utilisez les filtres pour affiner la recherche
   - Recherchez par code ICAO, IATA ou nom
   - Sélectionnez départ et arrivée

3. PLANIFICATION DE L'ITINÉRAIRE
   - Ajoutez des waypoints intermédiaires si nécessaire
   - Modifiez l'ordre des waypoints
   - Vérifiez les détails de chaque point

4. CALCUL ET EXPORT DU PLAN
   - Configurez votre clé API Tomorrow.io pour la météo
   - Calculez l'itinéraire complet avec vent
   - Exportez en Excel ou PDF

RACCOURCIS CLAVIER:
- Ctrl+N: Nouveau projet
- Ctrl+O: Ouvrir projet
- Ctrl+S: Sauvegarder
- F5: Calculer itinéraire
- F9: Carte interactive

SUPPORT: Consultez la documentation complète sur GitHub
"""

        guide_window = tk.Toplevel(self.root)
        guide_window.title("Guide d'utilisation")
        guide_window.geometry("600x500")

        text_widget = tk.Text(guide_window, wrap='word', padx=10, pady=10)
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', guide_text)
        text_widget.configure(state='disabled')

    def show_shortcuts(self):
        """Afficher les raccourcis clavier"""
        shortcuts = """RACCOURCIS CLAVIER VFR PLANNER

Fichier:
Ctrl+N         Nouveau projet
Ctrl+O         Ouvrir projet
Ctrl+S         Sauvegarder
Ctrl+Shift+S   Sauvegarder sous
Ctrl+Q         Quitter

Édition:
Ctrl+C         Copier le plan de vol

Outils:
F5             Calculer l'itinéraire
F9             Carte interactive

Navigation:
Tab            Basculer entre les champs
Ctrl+Tab       Changer d'onglet
Échap          Annuler dialogue
"""
        messagebox.showinfo("Raccourcis clavier", shortcuts)

    def show_about(self):
        """Afficher les informations sur l'application"""
        about_text = f"""VFR PLANNER

Version: {__version__}
Auteurs: {__author__}

Outil de planification de vol VFR avec calculs automatiques
de navigation, intégration météo et génération de plans
de vol professionnels.

Projet MGA802-01 - École Polytechnique de Montréal

Fonctionnalités:
• Base de données d'aéroports complète
• Calculs de navigation précis avec vent
• Intégration API météo (Tomorrow.io)
• Export Excel et PDF professionnel
• Cartes interactives
• Interface intuitive

© 2025 - Projet éducatif
"""
        messagebox.showinfo("À propos de VFR Planner", about_text)

    def on_closing(self):
        """Gérer la fermeture de l'application"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Fermeture",
                "Sauvegarder les modifications avant de quitter?"
            )
            if result is True:
                if not self.save_project():
                    return
            elif result is None:
                return

        self.root.destroy()