#!/usr/bin/env python3
"""
VFR Planner - Application principale

Outil de planification de vol VFR pour pilotes privés
Projet MGA802-01 - École Polytechnique de Montréal

Usage:
    python vfr_planner_app.py

Requirements:
    - Python 3.7+
    - tkinter (généralement inclus avec Python)
    - pandas
    - folium
    - requests
    - openpyxl
    - reportlab
    - pytz
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import traceback

# Ajouter le répertoire du projet au path Python
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def check_dependencies():
    """Vérifier que toutes les dépendances requises sont installées"""
    required_modules = [
        ('tkinter', 'Interface graphique'),
        ('pandas', 'Manipulation de données'),
        ('folium', 'Cartes interactives'),
        ('requests', 'API météo'),
        ('openpyxl', 'Export Excel'),
        ('reportlab', 'Export PDF'),
        ('pytz', 'Fuseaux horaires'),
        ('datetime', 'Gestion des dates'),
        ('json', 'Sérialisation des données'),
        ('math', 'Calculs mathématiques')
    ]

    missing_modules = []

    for module_name, description in required_modules:
        try:
            __import__(module_name)
            print(f"✅ {module_name}: {description}")
        except ImportError:
            missing_modules.append((module_name, description))
            print(f"❌ {module_name}: {description} - MANQUANT")

    if missing_modules:
        print("\n⚠️ MODULES MANQUANTS:")
        print("Installez les modules manquants avec:")
        print("pip install pandas folium requests openpyxl reportlab pytz")
        return False

    print("\n✅ Toutes les dépendances sont installées!")
    return True


def main():
    """Fonction principale de l'application"""
    print("=" * 60)
    print("VFR PLANNER - Outil de planification de vol VFR")
    print("Projet MGA802-01 - École Polytechnique de Montréal")
    print("=" * 60)

    # Vérifier les dépendances
    print("Vérification des dépendances...")
    if not check_dependencies():
        print("\n❌ Impossible de démarrer l'application.")
        print("Installez les modules manquants et relancez l'application.")
        input("Appuyez sur Entrée pour quitter...")
        return 1

    try:
        # Importer les modules de l'application
        print("\nInitialisation de l'application...")
        from vfr_planner.gui.main_window import VFRPlannerGUI

        # Créer la fenêtre principale Tkinter
        root = tk.Tk()

        # Configurer l'icône de l'application (si disponible)
        try:
            icon_path = os.path.join(PROJECT_ROOT, "resources", "icon.ico")
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
        except Exception:
            pass  # Ignorer si problème avec l'icône

        # Créer l'application
        app = VFRPlannerGUI(root)

        print("✅ Application initialisée avec succès!")
        print("\n🚀 Démarrage de l'interface graphique...")
        print("📝 Utilisez Ctrl+N pour créer un nouveau plan de vol")
        print("📖 Consultez le menu Aide > Guide d'utilisation pour débuter")
        print("\nPour fermer l'application, utilisez Ctrl+Q ou fermez la fenêtre.")

        # Démarrer la boucle principale de l'interface
        root.mainloop()

        print("\n👋 Merci d'avoir utilisé VFR Planner!")
        return 0

    except ImportError as e:
        error_msg = f"Erreur d'importation: {e}"
        print(f"\n❌ {error_msg}")

        # Afficher un message d'erreur graphique si possible
        try:
            root = tk.Tk()
            root.withdraw()  # Cacher la fenêtre principale
            messagebox.showerror(
                "Erreur VFR Planner",
                f"Impossible de charger l'application:\n\n{error_msg}\n\n"
                "Vérifiez que tous les fichiers du projet sont présents."
            )
        except Exception:
            pass

        return 1

    except Exception as e:
        error_msg = f"Erreur inattendue: {e}"
        print(f"\n❌ {error_msg}")
        print(f"Traceback:\n{traceback.format_exc()}")

        # Afficher un message d'erreur graphique si possible
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Erreur VFR Planner",
                f"Erreur lors du démarrage:\n\n{error_msg}\n\n"
                "Consultez la console pour plus de détails."
            )
        except Exception:
            pass

        return 1


def create_desktop_shortcut():
    """Créer un raccourci sur le bureau (Windows seulement)"""
    if sys.platform != "win32":
        print("Création de raccourci disponible seulement sur Windows")
        return

    try:
        import winshell
        from win32com.client import Dispatch

        desktop = winshell.desktop()
        path = os.path.join(desktop, "VFR Planner.lnk")
        target = sys.executable
        wdir = PROJECT_ROOT
        arguments = os.path.join(PROJECT_ROOT, "vfr_planner_app.py")

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.Arguments = arguments
        shortcut.WorkingDirectory = wdir
        shortcut.Description = "VFR Planner - Outil de planification de vol"
        shortcut.save()

        print(f"✅ Raccourci créé: {path}")

    except ImportError:
        print("Pour créer un raccourci, installez: pip install winshell pywin32")
    except Exception as e:
        print(f"Erreur création raccourci: {e}")


if __name__ == "__main__":
    # Vérifier les arguments de ligne de commande
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print(__doc__)
            sys.exit(0)
        elif sys.argv[1] == "--create-shortcut":
            create_desktop_shortcut()
            sys.exit(0)
        elif sys.argv[1] == "--check-deps":
            check_dependencies()
            sys.exit(0)

    # Démarrer l'application
    exit_code = main()

    # Pause avant fermeture en cas d'erreur (pour voir les messages)
    if exit_code != 0:
        try:
            input("\nAppuyez sur Entrée pour quitter...")
        except (EOFError, KeyboardInterrupt):
            pass

    sys.exit(exit_code)