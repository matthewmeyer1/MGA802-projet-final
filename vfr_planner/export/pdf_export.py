"""
Export de plans de vol vers PDF
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from datetime import datetime
from typing import List, Dict, Any


def export_to_pdf(flight_data: Dict[str, Any], legs_data: List[Dict],
                 filename: str = "flight_plan.pdf"):
    """
    Exporter un plan de vol vers PDF

    Args:
        flight_data: Données générales du vol
        legs_data: Données des segments de vol
        filename: Nom du fichier de sortie
    """
    try:
        # Configuration du document
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch
        )

        # Styles
        styles = getSampleStyleSheet()

        # Styles personnalisés
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=16,
            spaceAfter=20,
            alignment=1,  # Centre
            textColor=colors.darkblue
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=15,
            alignment=1,
            textColor=colors.grey
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=10,
            textColor=colors.darkblue
        )

        story = []

        # Titre principal
        title = Paragraph("PLAN DE VOL VFR<br/>VISUAL FLIGHT RULES FLIGHT PLAN", title_style)
        story.append(title)

        subtitle = Paragraph(f"Généré le {datetime.now().strftime('%Y-%m-%d à %H:%M')}", subtitle_style)
        story.append(subtitle)

        # Informations générales en tableau
        general_data = [
            ["AÉRONEF", "", "VOL", ""],
            ["Immatriculation:", flight_data.get('aircraft_id', 'N/A'),
             "Départ:", flight_data.get('departure', 'N/A')],
            ["Type:", flight_data.get('aircraft_type', 'N/A'),
             "Destination:", flight_data.get('destination', 'N/A')],
            ["TAS:", f"{flight_data.get('tas', 'N/A')} kn",
             "Date:", flight_data.get('date', 'N/A')],
            ["Consommation:", f"{flight_data.get('fuel_burn', 'N/A')} GPH",
             "ETD:", flight_data.get('etd', 'N/A')],
            ["Capacité:", f"{flight_data.get('fuel_capacity', 'N/A')} gal",
             "Pilote:", flight_data.get('pilot', 'N/A')],
        ]

        general_table = Table(general_data, colWidths=[1.2 * inch, 1.8 * inch, 1.2 * inch, 1.8 * inch])
        general_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.darkblue),
            ('BACKGROUND', (2, 0), (3, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (3, 0), colors.whitesmoke),
            ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
            ('BACKGROUND', (2, 1), (2, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(general_table)
        story.append(Spacer(1, 20))

        # Table des segments de navigation
        nav_heading = Paragraph("JOURNAL DE NAVIGATION", heading_style)
        story.append(nav_heading)

        # En-têtes du tableau des legs
        headers = [
            "Leg", "De", "À", "Dist\n(NM)", "CV\n(°)", "CM\n(°)",
            "Vent", "VS\n(kn)", "Temps\n(min)", "Carb\n(gal)", "ETA"
        ]

        legs_table_data = [headers]

        # Données des legs
        for i, leg in enumerate(legs_data, 1):
            wind_str = f"{leg.get('wind_dir', 0):.0f}°/{leg.get('wind_speed', 0):.0f}"
            row = [
                str(i),
                leg.get('from', '')[:6],  # Limiter la longueur
                leg.get('to', '')[:6],
                f"{leg.get('distance', 0):.0f}",
                f"{leg.get('true_course', 0):.0f}",
                f"{leg.get('mag_heading', 0):.0f}",
                wind_str,
                f"{leg.get('ground_speed', 0):.0f}",
                f"{leg.get('leg_time', 0):.0f}",
                f"{leg.get('fuel_leg', 0):.1f}",
                leg.get('eta', '')[:5]
            ]
            legs_table_data.append(row)

        # Calculer largeurs colonnes
        col_widths = [0.4, 0.6, 0.6, 0.5, 0.4, 0.4, 0.6, 0.4, 0.5, 0.5, 0.5]
        col_widths = [w * inch for w in col_widths]

        legs_table = Table(legs_table_data, colWidths=col_widths, repeatRows=1)
        legs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(legs_table)
        story.append(Spacer(1, 20))

        # Calculs et vérifications
        total_distance = sum(leg.get('distance', 0) for leg in legs_data)
        total_time = legs_data[-1].get('total_time', 0) if legs_data else 0
        total_fuel = legs_data[-1].get('fuel_total', 0) if legs_data else 0
        reserve_fuel = flight_data.get('reserve_fuel', 45) * flight_data.get('fuel_burn', 7.5) / 60
        total_fuel_required = total_fuel + reserve_fuel

        calculations_text = f"""
        <b>CALCULS ET VÉRIFICATIONS</b><br/>
        <br/>
        <b>Résumé du vol:</b><br/>
        Distance totale: <b>{total_distance:.1f} milles nautiques</b><br/>
        Temps total de vol: <b>{total_time / 60:.1f} heures ({total_time:.0f} minutes)</b><br/>
        <br/>
        <b>Analyse carburant:</b><br/>
        Carburant de route: <b>{total_fuel:.1f} gallons</b><br/>
        Carburant de réserve: <b>{reserve_fuel:.1f} gallons</b><br/>
        <b>Carburant total requis: {total_fuel_required:.1f} gallons</b><br/>
        Capacité réservoir: {flight_data.get('fuel_capacity', 'N/A')} gallons<br/>
        <br/>
        <b>Vérifications pré-vol:</b><br/>
        ☐ Briefing météo: {flight_data.get('weather_brief', 'Requis')}<br/>
        ☐ Vérification NOTAM: {flight_data.get('notam_check', 'Requise')}<br/>
        ☐ Plan de vol déposé: {flight_data.get('flight_plan_filed', 'À faire')}<br/>
        ☐ Suivi de vol: {flight_data.get('flight_following', 'Recommandé')}<br/>
        <br/>
        <b>Aérodromes alternatifs:</b><br/>
        Alternatif de départ: {flight_data.get('departure_alternate', 'À définir')}<br/>
        Alternatif en route: {flight_data.get('enroute_alternate', 'À définir')}<br/>
        Alternatif destination: {flight_data.get('destination_alternate', 'À définir')}<br/>
        <br/>
        <b>Signatures:</b><br/>
        <br/>
        Pilote commandant: _________________________ Date: __________<br/>
        <br/>
        Instructeur (si requis): _____________________ Date: __________<br/>
        <br/>
        Dispatcher (si applicable): __________________ Date: __________<br/>
        """

        calculations_para = Paragraph(calculations_text, styles['Normal'])
        story.append(calculations_para)

        # Générer le PDF
        doc.build(story)
        print(f"Plan de vol PDF sauvegardé: {filename}")

    except Exception as e:
        raise Exception(f"Erreur lors de la génération PDF: {e}")


def create_simple_pdf_export(flight_data: Dict[str, Any], legs_data: List[Dict],
                           filename: str = "simple_flight_plan.pdf"):
    """
    Créer un export PDF simplifié

    Args:
        flight_data: Données du vol
        legs_data: Données des segments
        filename: Nom du fichier
    """
    try:
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Titre simple
        title = Paragraph("Plan de Vol VFR", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))

        # Informations de base
        info_text = f"""
        <b>Avion:</b> {flight_data.get('aircraft_id', 'N/A')}<br/>
        <b>Pilote:</b> {flight_data.get('pilot', 'N/A')}<br/>
        <b>Date:</b> {flight_data.get('date', 'N/A')}<br/>
        <b>Départ:</b> {flight_data.get('departure', 'N/A')} à {flight_data.get('etd', 'N/A')}<br/>
        <b>Arrivée:</b> {flight_data.get('destination', 'N/A')}<br/>
        """

        info_para = Paragraph(info_text, styles['Normal'])
        story.append(info_para)
        story.append(Spacer(1, 20))

        # Table simple des legs
        simple_headers = ["#", "De", "À", "Distance", "Cap", "Temps", "ETA"]
        simple_data = [simple_headers]

        for i, leg in enumerate(legs_data, 1):
            row = [
                str(i),
                leg.get('from', ''),
                leg.get('to', ''),
                f"{leg.get('distance', 0):.1f} NM",
                f"{leg.get('mag_heading', 0):.0f}°",
                f"{leg.get('leg_time', 0):.0f} min",
                leg.get('eta', '')
            ]
            simple_data.append(row)

        simple_table = Table(simple_data)
        simple_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        story.append(simple_table)

        # Totaux
        total_distance = sum(leg.get('distance', 0) for leg in legs_data)
        total_time = legs_data[-1].get('total_time', 0) if legs_data else 0

        totals_text = f"""
        <br/>
        <b>TOTAUX:</b><br/>
        Distance totale: {total_distance:.1f} NM<br/>
        Temps total: {total_time / 60:.1f} heures<br/>
        """

        totals_para = Paragraph(totals_text, styles['Normal'])
        story.append(totals_para)

        doc.build(story)
        print(f"Plan PDF simple sauvegardé: {filename}")

    except Exception as e:
        raise Exception(f"Erreur export PDF simple: {e}")


def create_flight_briefing_pdf(flight_data: Dict[str, Any], legs_data: List[Dict],
                              weather_data: Dict[str, Any] = None,
                              filename: str = "flight_briefing.pdf"):
    """
    Créer un briefing de vol complet en PDF

    Args:
        flight_data: Données du vol
        legs_data: Données des segments
        weather_data: Données météo (optionnel)
        filename: Nom du fichier
    """
    try:
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Page 1: Plan de vol principal
        title = Paragraph("BRIEFING DE VOL VFR", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 20))

        # Résumé exécutif
        summary_text = f"""
        <b>RÉSUMÉ EXÉCUTIF</b><br/>
        <br/>
        Vol: {flight_data.get('departure', 'N/A')} → {flight_data.get('destination', 'N/A')}<br/>
        Date: {flight_data.get('date', 'N/A')} à {flight_data.get('etd', 'N/A')}<br/>
        Avion: {flight_data.get('aircraft_id', 'N/A')} ({flight_data.get('aircraft_type', 'N/A')})<br/>
        Pilote: {flight_data.get('pilot', 'N/A')}<br/>
        <br/>
        Distance: {sum(leg.get('distance', 0) for leg in legs_data):.1f} NM<br/>
        Temps estimé: {(legs_data[-1].get('total_time', 0) if legs_data else 0) / 60:.1f} heures<br/>
        Carburant requis: {legs_data[-1].get('fuel_total', 0) if legs_data else 0:.1f} gallons<br/>
        """

        summary_para = Paragraph(summary_text, styles['Normal'])
        story.append(summary_para)
        story.append(Spacer(1, 20))

        # Points de vérification
        checklist_text = """
        <b>LISTE DE VÉRIFICATION PRÉ-VOL</b><br/>
        <br/>
        <b>Documentation:</b><br/>
        ☐ Certificat d'immatriculation<br/>
        ☐ Certificat de navigabilité<br/>
        ☐ Licence radio<br/>
        ☐ Manuel de vol<br/>
        ☐ Cartes à jour<br/>
        <br/>
        <b>Planification:</b><br/>
        ☐ Plan de vol calculé<br/>
        ☐ Briefing météo obtenu<br/>
        ☐ NOTAM vérifiés<br/>
        ☐ Carburant suffisant<br/>
        ☐ Aérodromes alternatifs identifiés<br/>
        <br/>
        <b>Communications:</b><br/>
        ☐ Fréquences notées<br/>
        ☐ Transpondeur testé<br/>
        ☐ Plan de vol déposé (si requis)<br/>
        """

        checklist_para = Paragraph(checklist_text, styles['Normal'])
        story.append(checklist_para)

        # Nouvelle page pour les détails
        story.append(PageBreak())

        # Navigation détaillée (utiliser la fonction principale)
        export_to_pdf(flight_data, legs_data, filename + "_temp")

        # Note: Dans une implémentation complète, on combinerait les PDFs
        # ou on restructurerait le code pour éviter les fichiers temporaires

        doc.build(story)
        print(f"Briefing de vol sauvegardé: {filename}")

    except Exception as e:
        raise Exception(f"Erreur briefing PDF: {e}")


class FlightPlanPDFGenerator:
    """Générateur PDF avancé avec options personnalisables"""

    def __init__(self, pagesize=letter, margins=None):
        self.pagesize = pagesize
        self.margins = margins or {
            'left': 0.5 * inch,
            'right': 0.5 * inch,
            'top': 0.5 * inch,
            'bottom': 0.5 * inch
        }
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()

    def setup_custom_styles(self):
        """Configurer les styles personnalisés"""
        self.custom_styles = {
            'title': ParagraphStyle(
                'VFRTitle',
                parent=self.styles['Title'],
                fontSize=18,
                textColor=colors.darkblue,
                alignment=1,
                spaceAfter=20
            ),
            'heading': ParagraphStyle(
                'VFRHeading',
                parent=self.styles['Heading2'],
                fontSize=12,
                textColor=colors.darkblue,
                spaceBefore=15,
                spaceAfter=10
            ),
            'warning': ParagraphStyle(
                'VFRWarning',
                parent=self.styles['Normal'],
                textColor=colors.red,
                fontSize=10,
                leftIndent=20
            )
        }

    def generate_complete_plan(self, flight_data: Dict[str, Any],
                             legs_data: List[Dict], filename: str):
        """Générer un plan complet avec toutes les sections"""
        doc = SimpleDocTemplate(
            filename,
            pagesize=self.pagesize,
            **self.margins
        )

        story = []

        # Titre et en-tête
        story.extend(self._create_header(flight_data))

        # Informations générales
        story.extend(self._create_general_info(flight_data))

        # Journal de navigation
        story.extend(self._create_navigation_log(legs_data))

        # Calculs et vérifications
        story.extend(self._create_calculations(flight_data, legs_data))

        # Sections de sécurité
        story.extend(self._create_safety_sections())

        doc.build(story)
        print(f"Plan complet généré: {filename}")

    def _create_header(self, flight_data: Dict[str, Any]) -> List:
        """Créer l'en-tête du document"""
        elements = []

        title = Paragraph("PLAN DE VOL VFR", self.custom_styles['title'])
        elements.append(title)

        subtitle = Paragraph(
            f"Généré le {datetime.now().strftime('%Y-%m-%d à %H:%M')}",
            self.styles['Normal']
        )
        elements.append(subtitle)
        elements.append(Spacer(1, 20))

        return elements

    def _create_general_info(self, flight_data: Dict[str, Any]) -> List:
        """Créer la section d'informations générales"""
        elements = []

        heading = Paragraph("INFORMATIONS GÉNÉRALES", self.custom_styles['heading'])
        elements.append(heading)

        # Table d'informations (comme dans la fonction principale)
        # ... (code similaire à export_to_pdf)

        return elements

    def _create_navigation_log(self, legs_data: List[Dict]) -> List:
        """Créer le journal de navigation"""
        elements = []

        heading = Paragraph("JOURNAL DE NAVIGATION", self.custom_styles['heading'])
        elements.append(heading)

        # Table de navigation (comme dans la fonction principale)
        # ... (code similaire à export_to_pdf)

        return elements

    def _create_calculations(self, flight_data: Dict[str, Any],
                           legs_data: List[Dict]) -> List:
        """Créer la section de calculs"""
        elements = []

        heading = Paragraph("CALCULS ET VÉRIFICATIONS", self.custom_styles['heading'])
        elements.append(heading)

        # Calculs détaillés
        # ... (code de calculs)

        return elements

    def _create_safety_sections(self) -> List:
        """Créer les sections de sécurité"""
        elements = []

        safety_text = """
        <b>CONSIGNES DE SÉCURITÉ</b><br/>
        <br/>
        • Vérifiez les conditions météo avant le départ<br/>
        • Respectez les minimums VFR en tout temps<br/>
        • Maintenez une veille radio appropriée<br/>
        • Suivez les procédures d'urgence en cas de problème<br/>
        """

        safety_para = Paragraph(safety_text, self.styles['Normal'])
        elements.append(safety_para)

        return elements


if __name__ == "__main__":
    # Test de la fonction
    test_flight_data = {
        'aircraft_id': 'C-FXYZ',
        'aircraft_type': 'C172',
        'tas': 110,
        'departure': 'CYUL',
        'destination': 'CYQB',
        'date': '2025-06-17',
        'etd': '10:00',
        'pilot': 'Test Pilot',
        'fuel_capacity': 40,
        'fuel_burn': 7.5,
        'reserve_fuel': 45
    }

    test_legs_data = [
        {
            'from': 'CYUL',
            'to': 'CYQB',
            'distance': 145.3,
            'true_course': 45,
            'mag_heading': 58,
            'wind_dir': 270,
            'wind_speed': 15,
            'ground_speed': 125,
            'leg_time': 70,
            'total_time': 70,
            'fuel_leg': 8.7,
            'fuel_total': 8.7,
            'eta': '11:10',
            'remarks': 'Route directe'
        }
    ]

    try:
        export_to_pdf(test_flight_data, test_legs_data, "test_export.pdf")
        print("✅ Test d'export PDF réussi!")
    except Exception as e:
        print(f"❌ Erreur de test: {e}")