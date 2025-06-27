"""
Modèle de données pour les aéronefs
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Aircraft:
    """Modèle de données pour un aéronef"""

    registration: str = ""  # Immatriculation (ex: C-FXYZ)
    aircraft_type: str = ""  # Type d'avion (ex: C172)
    cruise_speed: float = 110.0  # Vitesse de croisière (kn)
    fuel_burn: float = 7.5  # Consommation (GPH)
    fuel_capacity: float = 40.0  # Capacité réservoir (gal)
    empty_weight: float = 1500.0  # Poids à vide (lbs)
    max_payload: float = 850.0  # Charge utile max (lbs)
    equipment: str = ""  # Équipements (GPS, Transponder, etc.)

    def __post_init__(self):
        """
        Validation après initialisation.

        :raises ValueError: Si la vitesse de croisière, la consommation ou la capacité de carburant sont négatives ou nulles.
        """
        if self.cruise_speed <= 0:
            raise ValueError("La vitesse de croisière doit être positive")
        if self.fuel_burn <= 0:
            raise ValueError("La consommation doit être positive")
        if self.fuel_capacity <= 0:
            raise ValueError("La capacité de carburant doit être positive")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Aircraft':
        """
        Créer un objet Aircraft à partir d’un dictionnaire.

        :param data: Dictionnaire contenant les informations de l’aéronef.
        :type data: dict
        :return: Une instance de Aircraft remplie avec les données du dictionnaire.
        :rtype: Aircraft
        """
        return cls(
            registration=data.get('registration', ''),
            aircraft_type=data.get('aircraft_type', ''),
            cruise_speed=float(data.get('cruise_speed', 110)),
            fuel_burn=float(data.get('fuel_burn', 7.5)),
            fuel_capacity=float(data.get('fuel_capacity', 40)),
            empty_weight=float(data.get('empty_weight', 1500)),
            max_payload=float(data.get('max_payload', 850)),
            equipment=data.get('equipment', '')
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convertir l’aéronef en dictionnaire.

        :return: Un dictionnaire représentant les attributs de l’objet Aircraft.
        :rtype: dict
        """
        return {
            'registration': self.registration,
            'aircraft_type': self.aircraft_type,
            'cruise_speed': self.cruise_speed,
            'fuel_burn': self.fuel_burn,
            'fuel_capacity': self.fuel_capacity,
            'empty_weight': self.empty_weight,
            'max_payload': self.max_payload,
            'equipment': self.equipment
        }

    def calculate_endurance(self, reserve_minutes: float = 45) -> float:
        """
        Calcule l'endurance totale de l'aéronef en minutes, en tenant compte d'une réserve de carburant.

        :param reserve_minutes: Réserve de carburant en minutes à conserver (par défaut : 45).
        :type reserve_minutes: float
        :return: Endurance disponible en minutes après déduction de la réserve.
        :rtype: float
        """
        if self.fuel_burn <= 0:
            return 0

        total_fuel_minutes = (self.fuel_capacity / self.fuel_burn) * 60
        return max(0, total_fuel_minutes - reserve_minutes)

    def calculate_range(self, reserve_minutes: float = 45) -> float:
        """
        Calcule la portée maximale en milles nautiques (NM), en tenant compte d'une réserve de carburant.

        :param reserve_minutes: Réserve de carburant en minutes à conserver (par défaut : 45).
        :type reserve_minutes: float
        :return: Portée maximale estimée en milles nautiques.
        :rtype: float
        """
        endurance_hours = self.calculate_endurance(reserve_minutes) / 60
        return endurance_hours * self.cruise_speed

    def is_valid_weight(self, payload: float) -> bool:
        """
        Vérifie si la charge utile donnée est valide.

        :param payload: Charge utile en livres.
        :type payload: float
        :return: ``True`` si la charge est dans les limites autorisées, sinon ``False``.
        :rtype: bool
        """
        return 0 <= payload <= self.max_payload

    def get_display_name(self) -> str:
        """
        Retourne le nom d'affichage de l'aéronef.

        Combine l'immatriculation et le type si disponibles, ou indique que l'aéronef est non spécifié.

        :return: Chaîne représentant l’aéronef.
        :rtype: str
        """
        if self.registration and self.aircraft_type:
            return f"{self.registration} ({self.aircraft_type})"
        elif self.registration:
            return self.registration
        elif self.aircraft_type:
            return self.aircraft_type
        else:
            return "Aéronef non spécifié"

    def __str__(self) -> str:
        """
        Retourne une représentation lisible de l'aéronef.

        :return: Nom d’affichage.
        :rtype: str
        """
        return self.get_display_name()

    def __repr__(self) -> str:
        """
        Retourne une représentation technique de l’objet Aircraft.

        :return: Représentation textuelle.
        :rtype: str
        """
        return f"Aircraft(registration='{self.registration}', type='{self.aircraft_type}')"


# Aéronefs prédéfinis pour tests et exemples
AIRCRAFT_PRESETS = {
    'C172': Aircraft(
        registration='C-FXYZ',
        aircraft_type='Cessna 172',
        cruise_speed=110,
        fuel_burn=7.5,
        fuel_capacity=40,
        empty_weight=1500,
        max_payload=850,
        equipment='GPS, Transponder Mode C'
    ),
    'PA28': Aircraft(
        registration='C-FABC',
        aircraft_type='Piper PA-28',
        cruise_speed=120,
        fuel_burn=8.0,
        fuel_capacity=48,
        empty_weight=1410,
        max_payload=890,
        equipment='GPS, Transponder Mode C'
    ),
    'C152': Aircraft(
        registration='C-FDEF',
        aircraft_type='Cessna 152',
        cruise_speed=95,
        fuel_burn=5.5,
        fuel_capacity=26,
        empty_weight=1150,
        max_payload=650,
        equipment='VOR, Transponder Mode A'
    )
}


def get_aircraft_preset(aircraft_type: str) -> Optional[Aircraft]:
    """
    Obtenir un aéronef prédéfini selon son identifiant.

    :param aircraft_type: Type d'aéronef (ex. ``'C172'``, ``'PA28'``, ``'C152'``).
    :type aircraft_type: str
    :return: L’objet Aircraft correspondant ou ``None`` si non trouvé.
    :rtype: Optional[Aircraft]
    """
    return AIRCRAFT_PRESETS.get(aircraft_type.upper())


def list_aircraft_presets() -> list:
    """
    Lister les identifiants des aéronefs prédéfinis disponibles.

    :return: Liste des clés disponibles dans ``AIRCRAFT_PRESETS``.
    :rtype: list
    """
    return list(AIRCRAFT_PRESETS.keys())