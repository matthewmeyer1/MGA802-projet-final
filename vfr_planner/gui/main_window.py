"""
Fenêtre principale de l'application VFR Planner
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os

from .tabs import AircraftTab, AirportsTab, RouteTab, PlanTab, WEATHER_API_KEY
from .widgets import StatusBarWidget
from ..data.airport_db import AirportDatabase
from .. import __version__, __author__


class VFRPlannerGUI:
    """
    Fenêtre principale de l'application VFR Planner.

    :param root: Fenêtre racine Tkinter utilisée comme conteneur principal de l'interface graphique.
    :type root: tkinter.Tk
    """

    def __init__(self, root):
        """
        Initialise l'interface graphique de VFR Planner.

        Cette méthode configure la fenêtre principale, initialise la base de données d'aéroports,
        crée les widgets de l'interface et configure les événements nécessaires.
        """
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
        """
        Configure les propriétés de la fenêtre principale.

        Définie le titre, la taille minimale, l'icône (si disponible),
        et la procédure à exécuter lors de la fermeture de la fenêtre.
        """
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
        """
        Crée la barre de menu principale de l'application.

        Cette méthode configure les menus suivants :
        - Fichier : opérations sur les projets (nouveau, ouvrir, sauvegarder, exporter, quitter)
        - Édition : actions générales et préférences
        - Outils : fonctions utilitaires (calculs, météo, carte, diagnostics)
        - Aide : accès au guide, raccourcis et à propos
        """
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
        """
        Crée et affiche les widgets principaux de l'application.

        Cette méthode instancie les onglets de navigation (aéronef, aéroports, itinéraire, plan de vol),
        ainsi que la barre d'état. En cas d'erreur lors de la création, une interface minimale est affichée.
        """
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
        """
        Configure les raccourcis clavier et les événements de l'application.

        Cette méthode associe des combinaisons de touches à des actions comme
        créer un nouveau projet, ouvrir, sauvegarder, copier, etc.,
        ainsi que le changement d'onglet pour détecter les modifications.
        """
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
        """
        Met à jour le contenu de la barre d'état.

        Affiche l'état de la connexion à l'API météo, le nombre d'aéroports visibles,
        et un message de statut par défaut.
        """
        # Statut API - toujours configurée maintenant
        self.status_bar.set_api_status(True, True)

        # Nombre d'aéroports
        stats = self.airport_db.get_filter_stats()
        self.status_bar.set_airports_count(stats['filtered'])

        # Message par défaut
        self.status_bar.set_status("Prêt - API météo configurée automatiquement")

    def on_tab_changed(self, event):
        """
        Appelé lorsque l'utilisateur change d'onglet dans l'application.

        :param event: Événement Tkinter déclenché par le changement d'onglet.
        :type event: tkinter.Event
        """
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
        """
        Marque le projet comme ayant des modifications non sauvegardées.

        Ajoute un astérisque au titre de la fenêtre si ce n'est pas déjà fait.
        """
        if not self.unsaved_changes:
            self.unsaved_changes = True
            title = self.root.title()
            if not title.endswith(" *"):
                self.root.title(title + " *")

    def mark_saved(self):
        """
        Marque le projet comme sauvegardé.

        Retire l'astérisque du titre de la fenêtre si présent.
        """
        self.unsaved_changes = False
        title = self.root.title()
        if title.endswith(" *"):
            self.root.title(title[:-2])

    # Actions du menu Fichier
    def new_project(self):
        """
        Crée un nouveau projet en réinitialisant tous les onglets.

        Affiche une boîte de dialogue pour sauvegarder les modifications en cours si nécessaire.
        Réinitialise les widgets des onglets Aéronef, Aéroports, Itinéraire et Plan de vol.
        """
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
        """
        Ouvre un projet existant depuis un fichier .vfr ou .json.

        Affiche une boîte de dialogue de confirmation si des modifications non sauvegardées existent.
        Charge les données du projet sélectionné et met à jour l'interface.

        :return: None
        """
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
        """
        Sauvegarde le projet courant.

        Si un fichier de projet est déjà associé, il est écrasé.
        Sinon, déclenche une demande de nouveau nom de fichier.

        :return: True si la sauvegarde a réussi, False sinon.
        :rtype: bool
        """
        if self.current_project_file:
            return self.save_project_to_file(self.current_project_file)
        else:
            return self.save_project_as()

    def save_project_as(self):
        """
        Sauvegarde le projet sous un nouveau nom choisi par l'utilisateur.

        :return: True si la sauvegarde a réussi, False sinon.
        :rtype: bool
        """
        filename = filedialog.asksaveasfilename(
            title="Sauvegarder le projet VFR",
            defaultextension=".vfr",
            filetypes=[("Projets VFR", "*.vfr"), ("JSON files", "*.json")]
        )

        if filename:
            return self.save_project_to_file(filename)
        return False

    def save_project_to_file(self, filename):
        """
        Sauvegarde les données du projet dans un fichier.

        :param filename: Chemin du fichier dans lequel enregistrer les données du projet.
        :type filename: str
        :return: True si la sauvegarde a réussi, False sinon.
        :rtype: bool
        """
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
        """
        Extrait les données actuelles du projet pour les sauvegarder dans un fichier.

        :return: Dictionnaire contenant les données du projet.
        :rtype: dict
        """
        return {
            'version': __version__,
            'aircraft': self.aircraft_tab.get_aircraft_data(),
            'flight': self.aircraft_tab.get_flight_data(),
            'departure_airport': self.airports_tab.departure_airport,
            'destination_airport': self.airports_tab.destination_airport,
            'waypoints': self.route_tab.get_waypoints(),
            'api_configured': True,  # Toujours configurée maintenant
            'saved_at': tk._default_root.tk.call('clock', 'format',
                                                 tk._default_root.tk.call('clock', 'seconds'),
                                                 '-format', '%Y-%m-%d %H:%M:%S')
        }

    def load_project_data(self, project_data):
        """
        Charge les données d’un projet dans les différents onglets de l’interface.

        :param project_data: Dictionnaire contenant les données du projet à charger.
        :type project_data: dict
        :return: None
        """
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
            if project_data.get('departure_airport') and hasattr(self.airports_tab,
                                                                 'departure_search') and self.airports_tab.departure_search:
                self.airports_tab.departure_airport = project_data['departure_airport']
                self.airports_tab.departure_search.set_airport(project_data['departure_airport'])

            if project_data.get('destination_airport') and hasattr(self.airports_tab,
                                                                   'destination_search') and self.airports_tab.destination_search:
                self.airports_tab.destination_airport = project_data['destination_airport']
                self.airports_tab.destination_search.set_airport(project_data['destination_airport'])

            # Charger waypoints
            waypoints = project_data.get('waypoints', [])
            if hasattr(self.route_tab, 'waypoints'):
                self.route_tab.waypoints = waypoints
                if hasattr(self.route_tab, 'update_waypoint_list'):
                    self.route_tab.update_waypoint_list()

            # Mettre à jour les affichages
            if hasattr(self.airports_tab, 'update_flight_info'):
                self.airports_tab.update_flight_info()
            self.update_status_bar()

        except Exception as e:
            print(f"Erreur lors du chargement des données: {e}")
            messagebox.showerror("Erreur", f"Erreur lors du chargement:\n{e}")

    def export_excel(self):
        """
        Exporte le plan de vol au format Excel.

        Utilise la méthode d’exportation définie dans l’onglet `plan_tab`.
        """
        self.plan_tab.export_excel()

    def export_pdf(self):
        """
        Exporte le plan de vol au format PDF.

        Utilise la méthode d’exportation définie dans l’onglet `plan_tab`.
        """
        self.plan_tab.export_pdf()

    def copy_plan(self):
        """
        Copie le contenu du plan de vol dans le presse-papier.

        Si aucun plan n’est défini, affiche un message d’avertissement.
        """
        plan_content = self.plan_tab.plan_text.get('1.0', tk.END)
        if plan_content.strip():
            self.root.clipboard_clear()
            self.root.clipboard_append(plan_content)
            self.status_bar.set_status("Plan copié dans le presse-papier")
        else:
            messagebox.showwarning("Attention", "Aucun plan de vol à copier")

    def show_preferences(self):
        """
        Affiche une boîte de dialogue de préférences.

        Actuellement, cette fonctionnalité n’est pas encore implémentée.
        """
        messagebox.showinfo("Préférences", "Fonctionnalité à implémenter")

    # Actions du menu Outils
    def calculate_route(self):
        """
        Calcule automatiquement l'itinéraire de vol.

        Appelle la méthode de calcul définie dans l’onglet `plan_tab`.
        """
        self.plan_tab.calculate_route()

    def check_weather(self):
        """
        Vérifie les conditions météo le long de l'itinéraire de vol.

        Utilise les informations de vol (date, heure, vitesse) pour déterminer
        le moment exact de passage sur chaque waypoint et fait appel à l’API météo
        via `WeatherService`. Affiche les résultats dans une interface dédiée.

        En cas d'erreur, affiche un message à l'utilisateur.
        """
        waypoints = self.route_tab.get_waypoints()
        if not waypoints:
            messagebox.showwarning("Attention", "Aucun waypoint défini")
            return

        try:
            from ..calculations.weather import WeatherService
            from ..models.waypoint import Waypoint
            import datetime
            import pytz

            # Utiliser la clé API intégrée
            weather_service = WeatherService(WEATHER_API_KEY)

            # Récupérer les informations de vol pour le timing correct
            flight_data = self.aircraft_tab.get_flight_data()
            aircraft_data = self.aircraft_tab.get_aircraft_data()

            print(f"🌤️ Vérification météo avec timing vol:")
            print(f"   Flight data: {flight_data}")

            # Calculer l'heure de départ réelle
            date_str = flight_data.get('date', '')
            time_str = flight_data.get('departure_time', '')

            if date_str and time_str:
                # Utiliser les données de vol
                try:
                    # Parser la date et l'heure
                    year, month, day = map(int, date_str.split('-'))
                    hour, minute = map(int, time_str.split(':'))

                    # Créer datetime avec timezone
                    tz = pytz.timezone("America/Montreal")
                    dt = datetime.datetime(year, month, day, hour, minute)
                    dt = tz.localize(dt)
                    start_time = dt.astimezone(pytz.utc)

                    print(f"   Heure départ configurée: {start_time.strftime('%Y-%m-%d %H:%M UTC')}")

                except Exception as e:
                    print(f"   ⚠️ Erreur parsing date/heure: {e}, utilisation heure actuelle")
                    start_time = datetime.datetime.now(pytz.utc)
            else:
                print(f"   ⚠️ Pas de date/heure configurée, utilisation heure actuelle")
                start_time = datetime.datetime.now(pytz.utc)

            # Récupérer la vitesse de croisière pour des calculs précis
            try:
                cruise_speed = float(aircraft_data.get('cruise_speed', 110))
            except (ValueError, TypeError):
                cruise_speed = 110

            print(f"   Vitesse croisière: {cruise_speed} kn")

            # Convertir waypoints en objets Waypoint
            wp_objects = [Waypoint(wp['lat'], wp['lon'], wp['name']) for wp in waypoints]

            # Choisir la méthode d'analyse selon la disponibilité de l'itinéraire calculé
            if hasattr(self.plan_tab, 'calculated_itinerary') and self.plan_tab.calculated_itinerary:
                print("   📊 Utilisation itinéraire calculé pour analyse précise")
                analysis = weather_service.analyze_weather_for_itinerary(self.plan_tab.calculated_itinerary)
            else:
                print("   📊 Utilisation analyse basique avec calculs de distance")
                analysis = weather_service.analyze_weather_for_route(wp_objects, start_time, cruise_speed)

            if 'error' in analysis:
                raise Exception(analysis['error'])

            # Afficher les résultats
            self.show_weather_analysis(analysis, weather_service)

        except Exception as e:
            messagebox.showerror("Erreur météo", f"Erreur lors de l'analyse météo:\n{e}")

    def show_weather_analysis(self, analysis, weather_service):
        """
        Afficher l'analyse météo dans une fenêtre avec timing détaillé.

        Ouvre une nouvelle fenêtre affichant un rapport complet sur les conditions
        météo le long de la route de vol, incluant un résumé de vol, détails par waypoint,
        analyse des tendances météo et recommandations VFR.

        :param analysis: dict contenant les données d’analyse météo et timing
        :param weather_service: instance du service météo, utilisée pour vérifier les conditions VFR
        """
        weather_window = tk.Toplevel(self.root)
        weather_window.title("Analyse météorologique avec timing de vol")
        weather_window.geometry("700x600")

        # Zone de texte avec scrollbar
        text_frame = ttk.Frame(weather_window)
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)

        weather_text = tk.Text(text_frame, wrap='word', font=('Courier', 10))
        weather_text.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=weather_text.yview)
        scrollbar.pack(side='right', fill='y')
        weather_text.configure(yscrollcommand=scrollbar.set)

        # Formater le contenu avec timing détaillé
        content = "ANALYSE MÉTÉOROLOGIQUE DE LA ROUTE\n"
        content += "=" * 60 + "\n\n"

        # Informations de timing
        if 'flight_start_time' in analysis:
            start_time = analysis['flight_start_time']
            content += f"🕐 Heure de départ: {start_time}\n"

        if 'aircraft_speed' in analysis:
            content += f"✈️ Vitesse de croisière: {analysis['aircraft_speed']} kn\n"

        if 'method' in analysis:
            method_desc = "Itinéraire calculé (timing précis)" if analysis['method'] == 'calculated_itinerary' else "Calculs de distance"
            content += f"📊 Méthode: {method_desc}\n"

        content += f"📅 Analyse générée: {analysis['generated_at'][:19]}\n\n"

        # Résumé de vol si disponible
        if 'analysis' in analysis and 'flight_summary' in analysis['analysis']:
            summary = analysis['analysis']['flight_summary']
            content += "RÉSUMÉ DU VOL:\n"
            content += f"Temps total: {summary['total_time_minutes']:.0f} minutes ({summary['total_time_minutes']/60:.1f}h)\n"
            content += f"Distance totale: {summary['total_distance_nm']:.1f} NM\n"
            content += f"Départ: {summary['departure_time']}\n"
            content += f"Arrivée estimée: {summary['arrival_time']}\n\n"

        # Détails par waypoint
        content += "MÉTÉO PAR WAYPOINT:\n"
        content += "-" * 60 + "\n"

        for i, wp_weather in enumerate(analysis['route_weather']):
            content += f"\n{i+1}. Waypoint: {wp_weather['waypoint']}\n"
            content += f"   Heure: {wp_weather['time']}\n"

            if 'leg_info' in wp_weather:
                content += f"   Info: {wp_weather['leg_info']}\n"

            weather = wp_weather['weather']
            content += f"   Vent: {weather['wind_direction']:.0f}°/{weather['wind_speed']:.0f} kn\n"
            content += f"   Température: {weather['temperature']:.0f}°C\n"
            content += f"   Visibilité: {weather['visibility']:.1f} km\n"
            content += f"   Couverture nuageuse: {weather['cloud_cover']:.0f}%\n"
            content += f"   Précipitations: {weather['precipitation']:.1f} mm/h\n"

        # Analyse des tendances
        if 'analysis' in analysis and analysis['analysis']:
            content += f"\n" + "=" * 60 + "\n"
            content += "ANALYSE DES TENDANCES:\n\n"
            anal = analysis['analysis']

            content += f"VENT:\n"
            if 'wind_speed' in anal:
                ws = anal['wind_speed']
                content += f"  Vitesse: min {ws['min']:.0f}kn, max {ws['max']:.0f}kn, moy {ws['avg']:.0f}kn\n"
            if 'wind_direction' in anal:
                wd = anal['wind_direction']
                content += f"  Direction moyenne: {wd['avg']:.0f}°\n"
                content += f"  Variation: {wd['variation']:.0f}°\n"

            if 'visibility' in anal:
                vis = anal['visibility']
                content += f"\nVISIBILITÉ:\n"
                content += f"  Minimale: {vis['min']:.1f} km\n"
                content += f"  Moyenne: {vis['avg']:.1f} km\n"

            if 'precipitation' in anal:
                precip = anal['precipitation']
                content += f"\nPRÉCIPITATIONS:\n"
                content += f"  Maximum: {precip['max']:.1f} mm/h\n"
                content += f"  Total route: {precip['total']:.1f} mm/h\n"

            # Alertes météo
            if 'alerts' in anal and anal['alerts']:
                content += f"\n⚠️ ALERTES MÉTÉO:\n"
                for alert in anal['alerts']:
                    content += f"  • {alert}\n"
            else:
                content += f"\n✅ Aucune alerte météo\n"

        # Recommandations VFR
        content += f"\n" + "=" * 60 + "\n"
        content += "RECOMMANDATIONS VFR:\n\n"

        # Vérifier les conditions VFR pour chaque point
        suitable_points = 0
        total_points = len(analysis['route_weather'])

        for wp_weather in analysis['route_weather']:
            weather = wp_weather['weather']
            suitable, reasons = weather_service.is_weather_suitable_for_vfr(weather)
            if suitable:
                suitable_points += 1

        content += f"Points avec conditions VFR: {suitable_points}/{total_points}\n"

        if suitable_points == total_points:
            content += "✅ Conditions favorables au VFR sur toute la route\n"
        elif suitable_points >= total_points * 0.8:
            content += "⚠️ Conditions généralement bonnes, vérifier points problématiques\n"
        else:
            content += "❌ Conditions difficiles, vol VFR non recommandé\n"

        content += f"\nNote: Cette analyse utilise {'les temps de vol calculés' if 'method' in analysis and analysis['method'] == 'calculated_itinerary' else 'des estimations de temps de vol'}"

        weather_text.insert('1.0', content)
        weather_text.configure(state='disabled')

    def show_interactive_map(self):
        """
        Affiche la carte interactive du plan de vol.

        Délègue l'affichage à la méthode `show_map` de l'onglet plan de vol.
        """
        self.plan_tab.show_map()

    def system_diagnostic(self):
        """
        Affiche un diagnostic du système dans une boîte d'information.

        Montre les versions de Python, Tkinter, VFR Planner, la présence des modules requis,
        le nombre d’aéroports chargés, la configuration API météo, etc.
        """
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

Configuration:
- API météo: ✅ Tomorrow.io (intégrée)

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
        """
        Lance un test de l'API météo intégrée.

        Appelle la méthode de test API météo depuis l'onglet plan de vol.
        """
        self.plan_tab.test_api()

    # Actions du menu Aide
    def show_user_guide(self):
        """
        Affiche une fenêtre contenant le guide d'utilisation de VFR Planner.

        La fenêtre présente les étapes principales pour configurer l'aéronef,
        sélectionner les aéroports, planifier l'itinéraire, calculer et exporter
        le plan de vol, ainsi que les raccourcis clavier utiles.
        """
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
   - L'API météo Tomorrow.io est déjà configurée
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
        """
        Affiche une boîte de dialogue listant les raccourcis clavier disponibles.

        Cette fenêtre liste les raccourcis pour les actions communes dans l'application,
        incluant fichier, édition, outils et navigation.
        """
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
        """
        Affiche une boîte de dialogue "À propos" avec les informations de version
        et description du logiciel.

        Montre la version, auteurs, fonctionnalités principales et informations légales.
        """
        about_text = f"""VFR PLANNER

Version: 0.1
Auteurs: Antoine Gingras, Matthew Meyer, Richard Nguekam, Gabriel Wong-Lapierre

Outil de planification de vol VFR avec calculs automatiques
de navigation, intégration météo et génération de plans
de vol professionnels.

Projet MGA802-01 - École de Technologie Supérieure

Fonctionnalités:
• Base de données d'aéroports complète
• Calculs de navigation précis avec vent
• Intégration API météo (Tomorrow.io) automatique
• Export Excel et PDF professionnel
• Cartes interactives
• Interface intuitive

© 2025 - Projet éducatif
"""
        messagebox.showinfo("À propos de VFR Planner", about_text)

    def on_closing(self):
        """
        Gère la fermeture de l'application.

        Si des modifications non sauvegardées existent, demande à l'utilisateur
        s'il souhaite sauvegarder avant de quitter. Peut annuler la fermeture.
        """
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
