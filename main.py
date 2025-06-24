#!/usr/bin/env python3
"""
Point d'entrée principal de l'application VFR Planner
Projet MGA802-01 - Outil de planification de vol VFR
"""

import tkinter as tk
import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vfr_planner.gui.main_window import VFRPlannerGUI


def main():
    """Fonction principale"""
    try:
        # Créer et lancer l'interface graphique
        root = tk.Tk()
        app = VFRPlannerGUI(root)
        root.mainloop()

    except Exception as e:
        print(f"Erreur lors du démarrage de l'application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()