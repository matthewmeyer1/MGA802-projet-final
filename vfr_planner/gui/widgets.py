"""
Widgets personnalisés pour l'interface graphique
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, Dict, Any

from ..data.airport_db import AirportDatabase


class AirportSearchWidget(ttk.Frame):
    """
    Widget de recherche d'aéroports avec fonction d'autocomplétion.

    Permet à l'utilisateur de rechercher un aéroport par code ou nom,
    affiche une liste déroulante des résultats correspondants,
    et affiche les informations sommaires de l'aéroport sélectionné.

    :param parent: widget parent
    :param airport_db: instance de AirportDatabase pour les recherches
    :param label_text: texte du label associé au champ de recherche (par défaut "Aéroport:")
    """


    def __init__(self, parent, airport_db: AirportDatabase, label_text: str = "Aéroport:"):
        """
        Initialiser le widget de recherche.

        :param parent: widget parent
        :param airport_db: base de données d'aéroports pour les recherches
        :param label_text: texte du label affiché au-dessus du champ de recherche
        """
        super().__init__(parent)
        self.airport_db = airport_db
        self.selected_airport = None
        self.callback: Optional[Callable] = None

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
        """
        Callback appelé à chaque changement du texte dans le champ de recherche.

        Lance une recherche dans la base d'aéroports avec le texte actuel
        si la longueur est >= 2 caractères, et affiche les résultats
        dans une liste déroulante.

        :param args: arguments optionnels liés au trace de la StringVar
        """
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
        """
        Callback appelé lors de la sélection d'un élément dans la liste des résultats.

        Récupère l'aéroport sélectionné, met à jour le champ de recherche
        avec le nom complet et affiche des informations sommaires
        (latitude, longitude, type).

        Si un callback utilisateur est défini, l'appelle avec
        l'aéroport sélectionné en argument.

        :param event: événement de sélection de la listbox
        """
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

    def set_callback(self, callback: Callable):
        """
        Définir une fonction callback appelée lors de la sélection d'un aéroport.

        La fonction doit accepter un argument : le dictionnaire de l'aéroport sélectionné.

        :param callback: fonction à appeler avec l'aéroport sélectionné
        """
        self.callback = callback

    def get_selected_airport(self):
        """
        Retourne l'aéroport actuellement sélectionné.

        :returns: Un dictionnaire contenant les informations de l'aéroport sélectionné,
                  ou None si aucun aéroport n'est sélectionné.
        :rtype: dict or None
        """
        return self.selected_airport

    def clear(self):
        """
        Efface la sélection courante et réinitialise le widget.

        Réinitialise le champ de recherche, supprime la sélection d'aéroport,
        efface le texte d'information et masque la liste des résultats.
        """
        self.search_var.set("")
        self.selected_airport = None
        self.info_label.config(text="")
        self.results_frame.grid_remove()

    def set_airport(self, airport: Dict[str, Any]):
        """
        Définit l'aéroport sélectionné dans le widget.

        Met à jour le champ de recherche et l'affichage d'information
        avec les données de l'aéroport donné.

        :param airport: Dictionnaire contenant les informations de l'aéroport,
                        avec au minimum les clés 'display', 'lat', 'lon' et
                        optionnellement 'type'.
        :type airport: dict
        """
        port = airport
        self.search_var.set(airport['display'])
        self.info_label.config(
            text=f"Lat: {airport['lat']:.4f}, "
                 f"Lon: {airport['lon']:.4f}, "
                 f"Type: {airport.get('type', 'N/A')}"
        )


class CustomWaypointDialog:
    """
    Dialogue pour ajouter un waypoint personnalisé.

    Permet à l'utilisateur d'ajouter un waypoint soit via des coordonnées personnalisées,
    soit en sélectionnant un aéroport depuis une base de données.

    :ivar dict or None result: Contient le waypoint créé après validation, ou None si annulé.
    :ivar AirportDatabase airport_db: Base de données des aéroports utilisée pour la recherche.
    :ivar tk.Toplevel dialog: La fenêtre de dialogue principale.
    :ivar tk.StringVar type_var: Variable contrôlant le type de waypoint ('custom' ou 'airport').
    :ivar ttk.LabelFrame coord_frame: Conteneur pour les entrées de coordonnées personnalisées.
    :ivar ttk.LabelFrame airport_frame: Conteneur pour la recherche d'aéroport.
    :ivar AirportSearchWidget airport_search: Widget de recherche d'aéroport intégré.
    """

    def __init__(self, parent, airport_db: AirportDatabase):
        """
        Initialise le dialogue d'ajout de waypoint.

        :param tk.Widget parent: Le widget parent de la fenêtre de dialogue.
        :param AirportDatabase airport_db: La base de données d'aéroports utilisée pour la recherche.
        """
        self.result = None
        self.airport_db = airport_db

        # Créer dialogue
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Ajouter Waypoint Personnalisé")
        self.dialog.geometry("400x350")
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

        # Instructions
        instructions = ttk.Label(self.dialog,
                                text="Format coordonnées: Latitude (45.458), Longitude (-73.749)\n"
                                     "Latitude: positive = Nord, négative = Sud\n"
                                     "Longitude: positive = Est, négative = Ouest",
                                font=('Arial', 8), foreground='gray')
        instructions.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

        # Boutons
        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Annuler", command=self.cancel_clicked).pack(side='left', padx=5)

        # Configuration initiale
        self.on_type_change()
        self.name_entry.focus()

        # Attendre fermeture
        self.dialog.wait_window()

    def on_type_change(self):
        """
        Met à jour l'interface en fonction du type de waypoint sélectionné.

        Affiche les champs de coordonnées personnalisées si 'custom' est sélectionné,
        sinon affiche le widget de recherche d'aéroport.
        """
        if self.type_var.get() == "custom":
            self.coord_frame.grid()
            self.airport_frame.grid_remove()
        else:
            self.coord_frame.grid_remove()
            self.airport_frame.grid()

    def ok_clicked(self):
        """
        Valide les données saisies et ferme le dialogue.

        - Vérifie la validité des coordonnées si le type est 'custom'.
        - Vérifie qu'un aéroport est sélectionné si le type est 'airport'.
        - En cas de validation réussie, stocke les informations dans `self.result`.
        - Affiche un message d'erreur en cas de problème et empêche la fermeture.

        :raises ValueError: Si les coordonnées saisies ne sont pas convertibles en float.
        """
        try:
            if self.type_var.get() == "custom":
                name = self.name_entry.get().strip()
                lat = float(self.lat_entry.get())
                lon = float(self.lon_entry.get())

                if not name:
                    messagebox.showerror("Erreur", "Nom requis")
                    return

                # Validation des coordonnées
                if not (-90 <= lat <= 90):
                    messagebox.showerror("Erreur", "Latitude doit être entre -90 et 90")
                    return
                if not (-180 <= lon <= 180):
                    messagebox.showerror("Erreur", "Longitude doit être entre -180 et 180")
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
        """
        Ferme le dialogue sans enregistrer de résultat.
        """
        self.dialog.destroy()


class StatusBarWidget(ttk.Frame):
    """
    Barre d'état affichant des messages et indicateurs.

    Fournit une interface visuelle pour afficher :
    - un message de statut principal,
    - le statut de connexion à l'API météo,
    - le nombre d'aéroports chargés.
    """

    def __init__(self, parent):
        """
        Initialise la barre d'état.

        :param parent: Widget parent.
        :type parent: tk.Widget
        """
        super().__init__(parent, relief='sunken', borderwidth=1)

        # Message principal
        self.status_var = tk.StringVar()
        self.status_var.set("Prêt")
        self.status_label = ttk.Label(self, textvariable=self.status_var)
        self.status_label.pack(side='left', padx=5)

        # Séparateur
        ttk.Separator(self, orient='vertical').pack(side='left', fill='y', padx=5)

        # Indicateur de connexion API
        self.api_var = tk.StringVar()
        self.api_var.set("API: Non configurée")
        self.api_label = ttk.Label(self, textvariable=self.api_var, foreground='orange')
        self.api_label.pack(side='left', padx=5)

        # Séparateur
        ttk.Separator(self, orient='vertical').pack(side='left', fill='y', padx=5)

        # Nombre d'aéroports
        self.airports_var = tk.StringVar()
        self.airports_var.set("Aéroports: 0")
        self.airports_label = ttk.Label(self, textvariable=self.airports_var)
        self.airports_label.pack(side='left', padx=5)

    def set_status(self, message: str):
        """
        Met à jour le message principal de statut.

        :param message: Texte à afficher dans la barre d'état.
        :type message: str
        """
        self.status_var.set(message)

    def set_api_status(self, configured: bool, working: bool = False):
        """
        Met à jour l'indicateur du statut de l'API.

        :param configured: Indique si l'API est configurée.
        :type configured: bool
        :param working: Indique si l'API fonctionne correctement (par défaut False).
        :type working: bool, optional
        """
        if not configured:
            self.api_var.set("API: Non configurée")
            self.api_label.config(foreground='orange')
        elif working:
            self.api_var.set("API: Fonctionnelle")
            self.api_label.config(foreground='green')
        else:
            self.api_var.set("API: Configurée")
            self.api_label.config(foreground='blue')

    def set_airports_count(self, count: int):
        """
        Met à jour le nombre d'aéroports affiché.

        :param count: Nombre total d'aéroports chargés.
        :type count: int
        """
        self.airports_var.set(f"Aéroports: {count:,}")


class ProgressDialog:
    """
    Dialogue modal affichant une barre de progression pour les opérations longues.

    Fournit un retour visuel à l'utilisateur pendant une tâche
    pouvant prendre un certain temps, avec possibilité d'annulation.
    """
    def __init__(self, parent, title: str = "Traitement en cours"):
        """
        Initialise le dialogue de progression.

        :param parent: Widget parent.
        :type parent: tk.Widget
        :param title: Titre de la fenêtre.
        :type title: str, optional
        """
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Centrer le dialogue
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (150 // 2)
        self.dialog.geometry(f"400x150+{x}+{y}")

        # Message
        self.message_var = tk.StringVar()
        self.message_var.set("Initialisation...")
        message_label = ttk.Label(self.dialog, textvariable=self.message_var)
        message_label.pack(pady=10)

        # Barre de progression
        self.progress = ttk.Progressbar(self.dialog, mode='indeterminate')
        self.progress.pack(fill='x', padx=20, pady=10)
        self.progress.start()

        # Bouton annuler (optionnel)
        self.cancelled = False
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=10)

        self.cancel_button = ttk.Button(button_frame, text="Annuler",
                                       command=self.cancel)
        self.cancel_button.pack()

    def set_message(self, message: str):
        """
        Met à jour le message affiché dans le dialogue.

        :param message: Texte à afficher à l'utilisateur.
        :type message: str
        """
        self.message_var.set(message)
        self.dialog.update()

    def cancel(self):
        """
        Indique que l'utilisateur a annulé l'opération.

        Met à jour le statut interne pour signaler une annulation.
        """
        self.cancelled = True

    def close(self):
        """
        Ferme le dialogue et arrête la barre de progression.
        """
        self.progress.stop()
        self.dialog.destroy()

    def is_cancelled(self) -> bool:
        """
        Indique si l'opération a été annulée par l'utilisateur.

        :return: True si annulé, False sinon.
        :rtype: bool
        """
        return self.cancelled


class InfoTooltip:
    """Tooltip d'information pour les widgets"""

    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tooltip = None

        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        """Afficher le tooltip"""
        if self.tooltip:
            return

        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(self.tooltip, text=self.text,
                         background="lightyellow", relief="solid", borderwidth=1)
        label.pack()

    def hide_tooltip(self, event=None):
        """Cacher le tooltip"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


def add_tooltip(widget, text: str):
    """Ajouter un tooltip à un widget"""
    return InfoTooltip(widget, text)


class FilterPanel(ttk.LabelFrame):
    """Panneau de filtres pour les aéroports"""

    def __init__(self, parent, airport_db: AirportDatabase, update_callback: Callable):
        super().__init__(parent, text="🔍 Filtres", padding=5)

        self.airport_db = airport_db
        self.update_callback = update_callback

        # Variables pour les filtres
        self.country_vars = {}
        self.type_vars = {}
        self.icao_only_var = tk.BooleanVar()
        self.iata_only_var = tk.BooleanVar()

        self.create_widgets()
        self.setup_defaults()

    def create_widgets(self):
        """Créer les widgets du panneau"""
        # Statistiques
        self.stats_label = ttk.Label(self, text="", font=('Arial', 9))
        self.stats_label.pack(pady=5)

        # Filtres par pays
        countries_frame = ttk.LabelFrame(self, text="Pays", padding=3)
        countries_frame.pack(fill='x', pady=2)

        available_countries = self.airport_db.get_available_countries()
        priority_countries = ['CA', 'US', 'FR', 'GB', 'DE']

        for i, country in enumerate(priority_countries):
            if country in available_countries:
                var = tk.BooleanVar()
                self.country_vars[country] = var
                cb = ttk.Checkbutton(countries_frame, text=country, variable=var,
                                   command=self.update_filters)
                cb.grid(row=i // 3, column=i % 3, sticky='w', padx=2)

        # Filtres par type
        types_frame = ttk.LabelFrame(self, text="Types", padding=3)
        types_frame.pack(fill='x', pady=2)

        available_types = self.airport_db.get_available_types()
        type_labels = {
            'large_airport': 'Grands',
            'medium_airport': 'Moyens',
            'small_airport': 'Petits',
            'heliport': 'Héliports'
        }

        for i, airport_type in enumerate(available_types[:4]):  # Limiter à 4
            var = tk.BooleanVar()
            self.type_vars[airport_type] = var
            label = type_labels.get(airport_type, airport_type)
            cb = ttk.Checkbutton(types_frame, text=label, variable=var,
                               command=self.update_filters)
            cb.grid(row=i // 2, column=i % 2, sticky='w', padx=2)

        # Options de codes
        codes_frame = ttk.LabelFrame(self, text="Codes", padding=3)
        codes_frame.pack(fill='x', pady=2)

        ttk.Checkbutton(codes_frame, text="ICAO requis", variable=self.icao_only_var,
                       command=self.update_filters).pack(anchor='w')
        ttk.Checkbutton(codes_frame, text="IATA requis", variable=self.iata_only_var,
                       command=self.update_filters).pack(anchor='w')

        # Boutons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', pady=5)

        ttk.Button(button_frame, text="Réinitialiser",
                  command=self.reset_filters).pack(fill='x', pady=1)

    def setup_defaults(self):
        """Configurer les valeurs par défaut"""
        # Cocher Canada et US par défaut
        if 'CA' in self.country_vars:
            self.country_vars['CA'].set(True)
        if 'US' in self.country_vars:
            self.country_vars['US'].set(True)

        self.update_filters()

    def update_filters(self):
        """Mettre à jour les filtres"""
        selected_countries = [country for country, var in self.country_vars.items() if var.get()]
        selected_types = [airport_type for airport_type, var in self.type_vars.items() if var.get()]

        self.airport_db.update_filters(
            countries=selected_countries,
            types=selected_types,
            icao_only=self.icao_only_var.get(),
            iata_only=self.iata_only_var.get()
        )

        # Mettre à jour les statistiques
        stats = self.airport_db.get_filter_stats()
        self.stats_label.config(text=f"{stats['filtered']:,} / {stats['total']:,} aéroports")

        # Appeler le callback
        if self.update_callback:
            self.update_callback()

    def reset_filters(self):
        """Réinitialiser tous les filtres"""
        for var in self.country_vars.values():
            var.set(False)
        for var in self.type_vars.values():
            var.set(False)
        self.icao_only_var.set(False)
        self.iata_only_var.set(False)

        self.airport_db.reset_filters()
        self.update_filters()