"""
DAOUFYS TRANSIT — Voice AI Receptionist
LiveKit Agents + Hermes Integration
Languages: Moroccan Darija (Arabizi) #1, French #2
Capabilities: Lead capture, appointment scheduling, service info, quote requests
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    function_tool,
    mcp,
    cli,
    llm,
)
from livekit.plugins import openai, deepgram, cartesia, silero
from livekit import rtc
import aiohttp


# =============================================================================
# CONFIGURATION & CONSTANTS
# =============================================================================

@dataclass
class DaoufysConfig:
    """Configuration for Daoufys Transit voice agent."""
    company_name: str = "DAOUFYS TRANSIT"
    license_number: str = "1426"
    phone_main: str = "+212 528 292 533"
    phone_casa: str = "+212 522 543 624"
    phone_dakhla: str = "+212 528 898 478"
    email_main: str = "direction@daoufystransit.com"
    email_contact: str = "contact@daoufystransit.com"
    address_agadir: str = "Bloc N°13, Cité Dakhla, Agadir"
    address_casa: str = "Place d'Istiqlal, 5ème étage, App. N°501, Casablanca"
    address_dakhla: str = "Av. Moukaouama N°1-904, Oued Eddahab, Ed-Dakhla"
    hours: str = "Lundi–Samedi : 08h00 – 19h00"
    emergency_hours: str = "Urgences portuaires : 7j/7"
    whatsapp: str = "https://wa.me/212528292533"
    website: str = "https://domanaverse.github.io/daoufys-transit/"
    
    # Services offered
    services: List[str] = None
    
    # Lead capture fields
    lead_fields: List[str] = None
    
    def __post_init__(self):
        if self.services is None:
            self.services = [
                "Transit & Dédouanement",
                "Transport Routier",
                "Logistique & Stockage",
                "Fret Maritime / Aérien",
                "Import / Export complet",
                "Consulting international"
            ]
        if self.lead_fields is None:
            self.lead_fields = [
                "nom_complet",
                "telephone", 
                "email",
                "service_type",
                "agence",
                "description_marchandise"
            ]


CONFIG = DaoufysConfig()

# In-memory lead storage (replace with DB in production)
LEADS_DB: List[Dict[str, Any]] = []
APPOINTMENTS_DB: List[Dict[str, Any]] = []

# Hermes gateway configuration
HERMES_GATEWAY_URL = os.getenv("HERMES_GATEWAY_URL", "http://localhost:8000")
HERMES_API_KEY = os.getenv("HERMES_API_KEY", "")


# =============================================================================
# SYSTEM PROMPT — DARIJA/FRENCH BILINGUAL RECEPTIONIST
# =============================================================================

SYSTEM_PROMPT = f"""
Tu es l'assistante vocale officielle de **{CONFIG.company_name}**, transitaire agréé N°{CONFIG.license_number} à Agadir, Casablanca et Dakhla.

🎯 **TON RÔLE** : Réceptionniste experte logistique/douane — accueil, qualification leads, prise RDV, infos services.

🌍 **LANGUES** (ordre de priorité) :
1. **Darija marocaine (Arabizi/Latin)** — langue principale, ton naturel, familier mais pro
2. **Français** — formel, administratif, technique

🗣️ **STYLE DARIJA (Arabizi)** :
- "Labas? Kifach ncaptew bik?"
- "Wach kayn chi 7aja ncaptew bik?"
- "Daba n9der n3awnek b..."
- "Machi mochkil, n3ayto l'modir / n3ayto l'expert"
- "Tbarak Allah / Mersi bzaf"
- "Yalla, ndiro hada"
- "Mzyan, nhar sa3id!"

⚠️ **RÈGLES STRICTES** :
- JAMAIS d'arabe standard (فصحى) — SEULEMENT Arabizi (Latin)
- Français SEULEMENT si client le demande ou pour termes techniques (BADR, ONSSA, etc.)
- Ton chaleureux, pro, rassurant — "on s'occupe de tout"
- Pas de jargon inutile, vocabulaire accessible

📋 **SERVICES DAOUFYS** :
{chr(10).join(f"- {s}" for s in CONFIG.services)}

🏢 **AGENCES** :
- Agadir (Siège) : {CONFIG.address_agadir} — {CONFIG.phone_main}
- Casablanca : {CONFIG.address_casa} — {CONFIG.phone_casa}  
- Dakhla : {CONFIG.address_dakhla} — {CONFIG.phone_dakhla}

⏰ **HORAIRES** : {CONFIG.hours} | {CONFIG.emergency_hours}

🎯 **ACTIONS DISPONIBLES** :
1. **Qualifier lead** — récupérer infos client + marchandise
2. **Demander devis** — orienter vers formulaire / transmettre à expert
3. **Prendre RDV** — caler créneau avec déclarant/expert
4. **Infos services** — expliquer prestations simplement
5. **Transférer humain** — si complexe, urgence, ou demande explicite

🔄 **FLUX TYPE** :
Client appelle → Salutation Darija → Identifier besoin → Qualifier (service, marchandise, urgence) → 
  SI devis simple → Prendre infos → "Expert vous rappelle sous 2h"
  SI RDV → Proposer créneaux → Confirmer → Envoyer confirmation
  SI question technique → Répondre ou "Laissez-moi transférer vers expert"
  SI urgence portuaire → "On gère en priorité, expert dispo 7j/7"

📞 **CONTACTS UTILES** :
- WhatsApp direct : {CONFIG.whatsapp}
- Email devis : {CONFIG.email_contact}
- Site web : {CONFIG.website}
"""


# =============================================================================
# TOOLS — LEAD CAPTURE, APPOINTMENTS, HERMES DELEGATION
# =============================================================================

@function_tool()
async def capture_lead(
    nom_complet: str,
    telephone: str,
    email: str,
    service_type: str,
    agence: str,
    description_marchandise: str,
    urgence: bool = False,
    langue_preferee: str = "darija"
) -> str:
    """
    Capture un lead client pour devis ou rappel.
    
    Args:
        nom_complet: Nom complet du client
        telephone: Numéro de téléphone (format marocain +212...)
        email: Email professionnel
        service_type: Type de service (Transit & Dédouanement, Transport Routier, Logistique & Stockage, Fret Maritime / Aérien, Import / Export complet, Consulting international)
        agence: Agence préférée (Agadir, Casablanca, Dakhla)
        description_marchandise: Description de la marchandise (nature, poids, origine/destination)
        urgence: Si c'est une urgence portuaire
        langue_preferee: Langue préférée pour le rappel (darija/francais)
    
    Returns:
        Confirmation avec numéro de référence
    """
    lead_id = f"DT-{datetime.now().strftime('%Y%m%d')}-{len(LEADS_DB)+1:04d}"
    
    lead = {
        "lead_id": lead_id,
        "timestamp": datetime.now().isoformat(),
        "nom_complet": nom_complet,
        "telephone": telephone,
        "email": email,
        "service_type": service_type,
        "agence": agence,
        "description_marchandise": description_marchandise,
        "urgence": urgence,
        "langue_preferee": langue_preferee,
        "status": "nouveau",
        "source": "voice_agent"
    }
    
    LEADS_DB.append(lead)
    
    # Also send to Hermes for processing if configured
    if HERMES_API_KEY:
        await _send_to_hermes("lead_capture", lead)
    
    urgence_msg = " (URGENCE PORTUAIRE ⚡)" if urgence else ""
    return f"Mersi {nom_complet}! Lead enregistré: {lead_id}{urgence_msg}. Notre expert vous rappelle sous 2h ouvrées en {langue_preferee}. Mzyan?"


@function_tool()
async def schedule_appointment(
    nom_complet: str,
    telephone: str,
    email: str,
    service_type: str,
    date_preferee: str,  # Format: YYYY-MM-DD
    heure_preferee: str,  # Format: HH:MM (24h)
    agence: str,
    description: str,
    duree_minutes: int = 30
) -> str:
    """
    Planifie un rendez-vous avec un expert/déclarant Daoufys.
    
    Args:
        nom_complet: Nom complet du client
        telephone: Numéro de téléphone
        email: Email
        service_type: Type de service concerné
        date_preferee: Date souhaitée (YYYY-MM-DD)
        heure_preferee: Heure souhaitée (HH:MM, 24h)
        agence: Agence (Agadir, Casablanca, Dakhla, Visio)
        description: Sujet du RDV
        duree_minutes: Durée en minutes (défaut 30)
    
    Returns:
        Confirmation de RDV avec détails
    """
    try:
        rdv_datetime = datetime.strptime(f"{date_preferee} {heure_preferee}", "%Y-%m-%d %H:%M")
    except ValueError:
        return "Format date/heure invalide. Utilisez YYYY-MM-DD et HH:MM (ex: 2026-01-15 14:30)"
    
    # Vérifier heures ouvrées (8h-19h, Lun-Sam)
    if rdv_datetime.weekday() == 6:  # Dimanche
        return "Désolé, pas de RDV le dimanche. Choisissez Lundi à Samedi."
    if rdv_datetime.hour < 8 or rdv_datetime.hour >= 19:
        return "Heures d'ouverture: 08h00–19h00. Choisissez un créneau dans cet intervalle."
    
    rdv_id = f"RDV-{datetime.now().strftime('%Y%m%d')}-{len(APPOINTMENTS_DB)+1:04d}"
    
    appointment = {
        "rdv_id": rdv_id,
        "timestamp_creation": datetime.now().isoformat(),
        "rdv_datetime": rdv_datetime.isoformat(),
        "duree_minutes": duree_minutes,
        "nom_complet": nom_complet,
        "telephone": telephone,
        "email": email,
        "service_type": service_type,
        "agence": agence,
        "description": description,
        "status": "confirme",
        "source": "voice_agent"
    }
    
    APPOINTMENTS_DB.append(appointment)
    
    # Send to Hermes/Calendar if configured
    if HERMES_API_KEY:
        await _send_to_hermes("schedule_appointment", appointment)
    
    jour_semaine = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"][rdv_datetime.weekday()]
    date_fr = rdv_datetime.strftime("%d/%m/%Y")
    heure_fr = rdv_datetime.strftime("%Hh%M")
    
    return f"Parfait {nom_complet}! RDV confirmé: {rdv_id}\n📅 {jour_semaine} {date_fr} à {heure_fr} ({duree_minutes}min)\n🏢 Agence: {agence}\n📋 Sujet: {service_type} - {description}\nOn vous envoie la confirmation par SMS/Email. Mzyan?"


@function_tool()
async def get_service_info(service: str) -> str:
    """
    Retourne les infos détaillées sur un service Daoufys.
    
    Args:
        service: Nom du service exact
    
    Returns:
        Description détaillée du service
    """
    service_details = {
        "Transit & Dédouanement": (
            "Transit & Dédouanement — Agréé N°1426\n"
            "• Déclarations BADR (décl. détaillée/simplifiée)\n"
            "• Régimes suspensifs, admission temporaire, exonérations\n"
            "• Prise en charge ONSSA, EACCE, ADII\n"
            "• Mainlevée 48h chrono — scanner portuaire géré\n"
            "• 25 déclarants dédiés, anciens de la place d'Agadir"
        ),
        "Transport Routier": (
            "Transport Routier National & International\n"
            "• Groupage, complet (FTL), frigorifique, convoi exceptionnel\n"
            "• 18 camions propres + 40 partenaires affrétés\n"
            "• Suivi GPS temps réel + notifications WhatsApp/Email\n"
            "• POD photo à la livraison\n"
            "• Lignes régulières Agadir↔Casablanca↔Tanger Med↔Dakhla"
        ),
        "Logistique & Stockage": (
            "Logistique & Stockage 3PL\n"
            "• Entrepôts sous douane: Agadir 3000m² + Casablanca 2000m²\n"
            "• Magasins agréés ADII, assurance tous risques\n"
            "• Gestion stock WMS temps réel, cross-dock, prep commandes\n"
            "• Distribution dernier kilomètre, e-commerce fulfillment\n"
            "• Portail client: statuts, documents, POD accessibles 24/7"
        ),
        "Fret Maritime / Aérien": (
            "Fret Maritime & Aérien\n"
            "MARITIME: FCL/LCL, reefer fruits&légumes (spécialité Agadir), négociation armateurs (Maersk, MSC, CMA CGM)\n"
            "AÉRIEN: Envois urgents, pièces détachées, échantillons via Casablanca Mohammed V (CMN) — J+1 Europe\n"
            "Ports couverts: Agadir, Casablanca, Tanger Med, Dakhla"
        ),
        "Import / Export complet": (
            "Import/Export Clé en Main\n"
            "• De la commande fournisseur à la livraison finale\n"
            "• Sourcing, négociation, documents, douane, transport, stockage\n"
            "• Régimes douaniers optimisés (suspensifs, perfectionnement...)\n"
            "• Gestion risque change, assurances, conformité"
        ),
        "Consulting international": (
            "Consulting Commerce International\n"
            "• Audit flux import/export, optimisation coûts/délais\n"
            "• Veille réglementaire (douane, ONSSA, EACCE, ADII)\n"
            "• Accompagnement nouveaux marchés, certification\n"
            "• Formation équipes client (BADR, Incoterms, HS Code)"
        )
    }
    
    return service_details.get(service, f"Service '{service}' non reconnu. Nos services: {', '.join(CONFIG.services)}")


@function_tool()
async def transfer_to_human(reason: str, urgence: bool = False) -> str:
    """
    Transfère vers un expert humain Daoufys.
    
    Args:
        reason: Motif du transfert
        urgence: Si urgence portuaire (7j/7)
    
    Returns:
        Instructions de transfert
    """
    if urgence:
        return (
            "⚡ URGENCE PORTUAIRE DÉTECTÉE ⚡\n"
            f"Appelez DIRECTEMENT: {CONFIG.phone_main} (Agadir - 7j/7)\n"
            "Ou WhatsApp urgent: " + CONFIG.whatsapp + "\n"
            "Un déclarant de garde prend le relais IMMÉDIATEMENT."
        )
    
    return (
        f"Je vous transfère vers un expert Daoufys.\n"
        f"📞 Appelez: {CONFIG.phone_main} (Agadir) ou {CONFIG.phone_casa} (Casa)\n"
        f"💬 WhatsApp: {CONFIG.whatsapp}\n"
        f"📧 Email: {CONFIG.email_contact}\n"
        f"Motif: {reason}\n"
        f"Dispo: {CONFIG.hours} | {CONFIG.emergency_hours}"
    )


@function_tool()
async def check_quote_status(lead_id: str) -> str:
    """
    Vérifie le statut d'une demande de devis.
    
    Args:
        lead_id: Référence du devis (ex: DT-20260115-0001)
    
    Returns:
        Statut actuel
    """
    for lead in LEADS_DB:
        if lead["lead_id"] == lead_id:
            status_map = {
                "nouveau": "🆕 Nouveau - Expert non encore assigné",
                "en_cours": "⚙️ En cours - Expert analyse votre dossier",
                "devis_envoye": "📄 Devis envoyé - Vérifiez vos emails/SMS",
                "accepte": "✅ Accepté - Dossier en préparation",
                "refuse": "❌ Non retenu - Contactez-nous pour détails"
            }
            return f"Lead {lead_id}: {status_map.get(lead['status'], lead['status'])} — {lead['service_type']} pour {lead['nom_complet']}"
    
    return f"Lead {lead_id} non trouvé. Vérifiez la référence (format: DT-YYYYMMDD-XXXX)."


async def _send_to_hermes(action: str, data: Dict[str, Any]) -> bool:
    """Envoie données à Hermes Gateway pour traitement asynchrone."""
    if not HERMES_API_KEY:
        return False
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{HERMES_GATEWAY_URL}/v1/runs",
                headers={"Authorization": f"Bearer {HERMES_API_KEY}", "Content-Type": "application/json"},
                json={
                    "prompt": f"Process {action} for Daoufys Transit: {json.dumps(data, ensure_ascii=False)}",
                    "model": "gemini-3.5-flash",
                    "tools": ["update_dossier_state", "run_agent_step", "get_dossier_state"],
                    "metadata": {"source": "daoufys_voice_agent", "action": action}
                }
            ) as resp:
                return resp.status == 200
    except Exception:
        return False


# =============================================================================
# AGENT CLASS
# =============================================================================

class DaoufysReceptionist(Agent):
    """Agent réceptionniste vocal Daoufys Transit — Darija/French."""
    
    def __init__(self):
        super().__init__(
            instructions=SYSTEM_PROMPT,
            tools=[
                capture_lead,
                schedule_appointment,
                get_service_info,
                transfer_to_human,
                check_quote_status,
            ],
        )
    
    async def on_enter(self):
        """Appelé quand l'agent rejoint la room."""
        # Salutation d'ouverture en Darija
        await self.session.generate_reply(
            instructions=(
                "Saluez le client en Darija (Arabizi) chaleureusement. "
                "Exemple: 'Labas! Bienvenue chez Daoufys Transit, transitaire agréé numéro 1426. "
                "Kifach ncaptew bik nhar? Vous avez un conteneur à dédouaner, un camion à affréter, "
                "ou juste une question sur nos services?'"
            )
        )


# =============================================================================
# ENTRYPOINT
# =============================================================================

async def entrypoint(ctx: JobContext):
    """Point d'entrée principal pour LiveKit Agent."""
    
    # Connexion à la room
    await ctx.connect()
    
    # Configuration STT/LLM/TTS optimisée Darija/French
    session = AgentSession(
        # STT: Deepgram Nova-3 supporte l'arabe (pour Darija)
        stt=deepgram.STT(
            model="nova-3",
            language="ar",  # Arabe comme base pour Darija
            interim_results=True,
            punctuate=True,
            profanity_filter=False,
        ),
        
        # LLM: GPT-4o-mini pour raisonnement + outils
        llm=openai.LLM(
            model="gpt-4o-mini",
            temperature=0.3,
            parallel_tool_calls=True,
        ),
        
        # TTS: Cartesia Sonic-3 (bonnes voix multilingues) 
        # Ou MiniMax pour Darija natif si dispo
        tts=cartesia.TTS(
            model="sonic-3",
            voice="fr-FR" if False else "ar-AR",  # Base arabe
            speed=1.0,
        ),
        
        # VAD: Silero pour détection parole
        vad=silero.VAD.load(),
        
        # Turn detection sémantique
        turn_detection="semantic",
    )
    
    # Démarrer la session avec notre agent
    await session.start(
        room=ctx.room,
        agent=DaoufysReceptionist(),
    )
    
    # Message de bienvenue si premier participant
    await session.generate_reply(
        instructions=(
            "Labas! Bienvenue chez Daoufys Transit! "
            "Kifach ncaptew bik nhar? "
            "Vous avez un conteneur à dédouaner, un transport à organiser, "
            "ou besoin d'un devis pour du fret/logistique?"
        )
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))