"""
Tests for DAOUFYS Voice Agent
Run: uv run pytest tests/ -v
"""

import pytest
from datetime import datetime, timedelta
from agent.daoufys_receptionist import (
    DaoufysConfig,
    CONFIG,
    LEADS_DB,
    APPOINTMENTS_DB,
    capture_lead,
    schedule_appointment,
    get_service_info,
    transfer_to_human,
    check_quote_status,
)


@pytest.fixture(autouse=True)
def clear_dbs():
    """Clear in-memory DBs before each test."""
    LEADS_DB.clear()
    APPOINTMENTS_DB.clear()
    yield
    LEADS_DB.clear()
    APPOINTMENTS_DB.clear()


class TestDaoufysConfig:
    def test_config_defaults(self):
        assert CONFIG.company_name == "DAOUFYS TRANSIT"
        assert CONFIG.license_number == "1426"
        assert len(CONFIG.services) == 6
        assert "Transit & Dédouanement" in CONFIG.services

    def test_config_phones(self):
        assert CONFIG.phone_main == "+212 528 292 533"
        assert CONFIG.phone_casa == "+212 522 543 624"
        assert CONFIG.phone_dakhla == "+212 528 898 478"


class TestCaptureLead:
    @pytest.mark.asyncio
    async def test_capture_lead_basic(self):
        result = await capture_lead(
            nom_complet="Ahmed Benali",
            telephone="+212612345678",
            email="ahmed@test.ma",
            service_type="Transit & Dédouanement",
            agence="Agadir",
            description_marchandise="Conteneur 20ft électroménager",
        )
        assert "DT-" in result
        assert "Ahmed Benali" in result
        assert len(LEADS_DB) == 1
        lead = LEADS_DB[0]
        assert lead["nom_complet"] == "Ahmed Benali"
        assert lead["service_type"] == "Transit & Dédouanement"
        assert lead["langue_preferee"] == "darija"

    @pytest.mark.asyncio
    async def test_capture_lead_urgence(self):
        result = await capture_lead(
            nom_complet="Fatima Zahra",
            telephone="+212698765432",
            email="fatima@export.ma",
            service_type="Transport Routier",
            agence="Casablanca",
            description_marchandise="Urgence: camion bloqué port",
            urgence=True,
        )
        assert "URGENCE PORTUAIRE" in result
        assert LEADS_DB[0]["urgence"] is True


class TestScheduleAppointment:
    @pytest.mark.asyncio
    async def test_schedule_appointment_valid(self):
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        result = await schedule_appointment(
            nom_complet="Youssef Alaoui",
            telephone="+212655555555",
            email="youssef@import.ma",
            service_type="Logistique & Stockage",
            date_preferee=tomorrow,
            heure_preferee="10:00",
            agence="Agadir",
            description="Visite entrepôt 3000m²",
        )
        assert "RDV-" in result
        assert "Youssef Alaoui" in result
        assert "10h00" in result
        assert len(APPOINTMENTS_DB) == 1

    @pytest.mark.asyncio
    async def test_schedule_appointment_sunday_rejected(self):
        # Find next Sunday
        days_ahead = 6 - datetime.now().weekday()
        sunday = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        result = await schedule_appointment(
            nom_complet="Test User",
            telephone="+212600000000",
            email="test@test.ma",
            service_type="Transit & Dédouanement",
            date_preferee=sunday,
            heure_preferee="10:00",
            agence="Agadir",
            description="Test",
        )
        assert "dimanche" in result.lower() or "non" in result.lower()

    @pytest.mark.asyncio
    async def test_schedule_appointment_outside_hours(self):
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        result = await schedule_appointment(
            nom_complet="Test User",
            telephone="+212600000000",
            email="test@test.ma",
            service_type="Transit & Dédouanement",
            date_preferee=tomorrow,
            heure_preferee="07:00",  # Before 8h
            agence="Agadir",
            description="Test",
        )
        assert "08h00" in result or "19h00" in result


class TestGetServiceInfo:
    @pytest.mark.asyncio
    async def test_get_service_info_valid(self):
        result = await get_service_info("Transit & Dédouanement")
        assert "BADR" in result
        assert "ONSSA" in result
        assert "48h" in result
        assert "1426" in result

    @pytest.mark.asyncio
    async def test_get_service_info_invalid(self):
        result = await get_service_info("Service Inexistant")
        assert "non reconnu" in result


class TestTransferToHuman:
    @pytest.mark.asyncio
    async def test_transfer_urgence(self):
        result = await transfer_to_human("Conteur bloqué scanner", urgence=True)
        assert "URGENCE PORTUAIRE" in result
        assert "7j/7" in result
        assert CONFIG.phone_main in result

    @pytest.mark.asyncio
    async def test_transfer_normal(self):
        result = await transfer_to_human("Question technique complexe")
        assert "expert" in result.lower()
        assert CONFIG.whatsapp in result


class TestCheckQuoteStatus:
    @pytest.mark.asyncio
    async def test_check_quote_status_found(self):
        # First create a lead
        await capture_lead(
            nom_complet="Test Lead",
            telephone="+212611111111",
            email="lead@test.ma",
            service_type="Import / Export complet",
            agence="Dakhla",
            description_marchandise="Test",
        )
        lead_id = LEADS_DB[0]["lead_id"]
        
        result = await check_quote_status(lead_id)
        assert lead_id in result
        assert "Nouveau" in result or "nouveau" in result

    @pytest.mark.asyncio
    async def test_check_quote_status_not_found(self):
        result = await check_quote_status("DT-20260101-9999")
        assert "non trouvé" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])