# DAOUFYS TRANSIT — Voice AI Receptionist

**LiveKit Agents + Hermes Integration** | **Languages: Darija (Arabizi) #1, French #2**

Voice receptionist for DAOUFYS TRANSIT (transitaire agréé N°1426) handling:
- 🎯 Lead capture & qualification
- 📅 Appointment scheduling with experts
- 📋 Service information (transit, transport, logistique, fret, import/export, consulting)
- 🔄 Transfer to human experts
- 📊 Quote status checking
- 🤖 Hermes delegation for complex multi-step tasks

---

## 🏗️ Architecture

```
┌─────────────────┐     WebRTC      ┌──────────────────┐     MCP/HTTP      ┌─────────────┐
│  Client Browser │◄───────────────►│  LiveKit Cloud   │◄────────────────►│   Hermes    │
│  / Phone (SIP)  │   (Media/STT/   │  (Media Server)  │   (Delegation)   │   Gateway   │
│  / Mobile App   │    TTS/LLM)     │  + Agent Worker  │                  │  (8 Agents) │
└─────────────────┘                 └──────────────────┘                  └─────────────┘
                                             │
                                    ┌────────┴────────┐
                                    ▼                 ▼
                              ┌───────────┐    ┌─────────────┐
                              │  Deepgram │    │  Cartesia/  │
                              │   STT     │    │   MiniMax   │
                              │  (Arabic) │    │   TTS       │
                              └───────────┘    │  (Darija)   │
                                               └─────────────┘
```

---

## 🚀 Quick Start

### 1. Prerequisites

- **LiveKit Cloud account** — [cloud.livekit.io](https://cloud.livekit.io)
- **Python 3.10+** with **uv** — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **API Keys** for: Deepgram, OpenAI, Cartesia (or MiniMax for Darija TTS)

### 2. Install & Configure

```bash
# Navigate to voice agent directory
cd /path/to/daoufys-transit/voice-agent

# Install dependencies
uv sync --all-extras

# Copy and configure environment
cp config/.env.example .env
# Edit .env with your API keys
```

### 3. Required Environment Variables

| Variable | Description | Source |
|----------|-------------|--------|
| `LIVEKIT_URL` | WebSocket URL (wss://...) | LiveKit Cloud → Project |
| `LIVEKIT_API_KEY` | API Key | LiveKit Cloud → API Keys |
| `LIVEKIT_API_SECRET` | API Secret | LiveKit Cloud → API Keys |
| `DEEPGRAM_API_KEY` | STT (Arabic/Darija) | [deepgram.com](https://deepgram.com) |
| `OPENAI_API_KEY` | LLM (GPT-4o-mini) | [openai.com](https://openai.com) |
| `CARTESIA_API_KEY` | TTS (Sonic-3) | [cartesia.ai](https://cartesia.ai) |
| `MINIMAX_API_KEY` | **TTS Darija (Best)** | [minimax.io](https://minimax.io) |
| `HERMES_GATEWAY_URL` | Hermes API endpoint | Your Hermes deployment |
| `HERMES_API_KEY` | Hermes gateway auth | Hermes config |

### 4. Run Locally

```bash
# Console mode (text + voice in terminal)
uv run python -m agent.daoufys_receptionist console

# Or with LiveKit CLI
lk agent console agent/daoufys_receptionist.py
```

### 5. Test in Browser

1. Go to [LiveKit Agents Playground](https://agents-playground.livekit.io/)
2. Enter your LiveKit URL + token
3. Join room `daoufys-test`
4. Speak in Darija or French!

---

## 📦 Deployment to LiveKit Cloud

### Option A: CLI Deploy (Recommended)

```bash
# Install LiveKit CLI
uv tool install livekit-cli

# Login
lk cloud auth login

# Deploy
lk agent deploy
```

### Option B: Docker + Manual

```bash
# Build image
docker build -t daoufys-voice-agent .

# Push to registry
docker tag daoufys-voice-agent your-registry/daoufys-voice-agent:latest
docker push your-registry/daoufys-voice-agent:latest

# Deploy via LiveKit Cloud dashboard or CLI
```

### Secrets Required in LiveKit Cloud

Create these secrets in LiveKit Cloud → Project → Secrets:

| Secret Name | Keys |
|-------------|------|
| `livekit-credentials` | `url`, `api_key`, `api_secret` |
| `ai-provider-keys` | `deepgram`, `openai`, `cartesia`, `minimax` |
| `hermes-credentials` | `api_key` |

---

## 🎙️ Language & Voice Configuration

### Darija (Arabizi) — Primary Language

The agent speaks **Moroccan Darija in Arabizi (Latin script)**:

```
"Labas! Bienvenue chez Daoufys Transit, transitaire agréé numéro 1426.
 Kifach ncaptew bik nhar? Vous avez un conteneur à dédouaner, 
 un camion à affréter, ou juste une question sur nos services?"
```

**Key Darija phrases used:**
- `Labas?` — Ça va? / Bonjour
- `Kifach ncaptew bik?` — Comment je peux t'aider?
- `Mzyan` — Bien / OK / D'accord
- `Yalla` — Allez / C'est parti
- `Mchi mochkil` — Pas de problème
- `Tbarak Allah / Mersi bzaf` — Merci beaucoup
- `Nhar sa3id!` — Bonne journée!

### French — Secondary Language

Used for:
- Technical terms: BADR, ONSSA, EACCE, ADII, Incoterms, HS Code
- Formal confirmations, legal/admin language
- When client explicitly requests French

### TTS Provider Recommendation

| Provider | Darija Quality | Cost | Latency |
|----------|---------------|------|---------|
| **MiniMax (speech-02-hd)** | ⭐⭐⭐⭐⭐ Native | $40/mo | Low |
| **ElevenLabs (cloned)** | ⭐⭐⭐⭐ Good | $22/mo | Low |
| **Cartesia (Arabic)** | ⭐⭐ Basic | Pay/go | Very Low |
| **OpenAI TTS** | ⭐ Basic | Pay/go | Low |

**→ Use MiniMax for production Darija TTS**

---

## 🛠️ Available Tools (Functions)

| Tool | Description | Parameters |
|------|-------------|------------|
| `capture_lead` | Qualify & store lead for quote callback | nom, tel, email, service, agence, marchandise, urgence, langue |
| `schedule_appointment` | Book RDV with expert/declarant | nom, tel, email, service, date, heure, agence, description, durée |
| `get_service_info` | Detailed service explanation | service name |
| `transfer_to_human` | Escalate to human expert | reason, urgence |
| `check_quote_status` | Check lead/quote progress | lead_id |

### Example Tool Calls

```python
# Lead capture
await capture_lead(
    nom_complet="Ahmed Benali",
    telephone="+212612345678",
    email="ahmed@import-export.ma",
    service_type="Transit & Dédouanement",
    agence="Agadir",
    description_marchandise="2 conteneurs 40ft tomates cerises, origine Maroc, destination France",
    urgence=False,
    langue_preferee="darija"
)

# Schedule appointment
await schedule_appointment(
    nom_complet="Ahmed Benali",
    telephone="+212612345678",
    email="ahmed@import-export.ma",
    service_type="Transit & Dédouanement",
    date_preferee="2026-01-20",
    heure_preferee="10:30",
    agence="Agadir",
    description="Dédouanement 2 conteneurs tomates cerises export France",
    duree_minutes=45
)
```

---

## 🔗 Hermes Integration

The agent delegates complex multi-step tasks to your **8-agent Hermes notary system**:

```python
# In tools, when Hermes delegation needed:
async with aiohttp.ClientSession() as session:
    await session.post(
        f"{HERMES_GATEWAY_URL}/v1/runs",
        headers={"Authorization": f"Bearer {HERMES_API_KEY}"},
        json={
            "prompt": "Process customs dossier for Daoufys client...",
            "model": "gemini-3.5-flash",
            "tools": ["get_dossier_state", "run_agent_step", "update_dossier_state"]
        }
    )
```

**Hermes agents used:**
1. `receptionniste` — Initial qualification
2. `classificateur` — Document classification
3. `extracteur` — Data extraction
4. `validateur` — Compliance validation
5. `redacteur` — Document drafting
6. `controleur` — Quality control
7. `notaire` — Legal validation
8. `archiviste` — Archival

---

## 📞 Telephony Integration (SIP/PSTN)

LiveKit Cloud supports native telephony:

### Setup SIP Trunk
1. LiveKit Cloud Dashboard → **SIP** → **Create Trunk**
2. Configure provider (Twilio, Telnyx, local carrier)
3. Map Moroccan numbers: `+212 528 292 533` (Agadir), etc.

### Inbound Call Handling
```python
# Automatic dispatch on inbound call
@server.rtc_session(agent_name="daoufys-receptionist")
async def entrypoint(ctx: JobContext):
    caller_id = ctx.job.metadata.get("caller_id", "unknown")
    # Agent greets in Darija, handles call
```

### Outbound Calls
```python
from livekit import api
livekit_api = api.LiveKitAPI()
await livekit_api.sip.create_sip_participant(
    sip_trunk_id="your-trunk",
    phone_number="+2126XXXXXXXX",
    room_name="daoufys-outbound-xxx",
    participant_identity="daoufys-agent"
)
```

---

## 🧪 Testing

### Unit Tests
```bash
uv run pytest tests/ -v
```

### Load Test (Simulated Calls)
```bash
# Using LiveKit CLI
lk agent console agent/daoufys_receptionist.py --room test-load-1
lk agent console agent/daoufys_receptionist.py --room test-load-2
# ... multiple terminals
```

### Test Scenarios
| Scenario | Expected Behavior |
|----------|-------------------|
| Client speaks Darija | Agent replies in Darija (Arabizi) |
| Client asks "Combien pour dédouaner 20ft?" | Agent qualifies: marchandise, origine, destination → capture_lead |
| Client wants RDV with declarant | Agent proposes slots → schedule_appointment |
| Client says "Urgent, conteneur bloqué" | Agent detects urgence → transfer_to_human(urgence=True) |
| Client asks "C'est quoi BADR?" | Agent explains via get_service_info |

---

## 📁 Project Structure

```
voice-agent/
├── agent/
│   └── daoufys_receptionist.py    # Main agent code
├── config/
│   └── .env.example               # Environment template
├── tests/
│   └── test_agent.py              # Unit tests
├── Dockerfile                     # Container build
├── pyproject.toml                 # uv project config
├── requirements.txt               # pip dependencies
├── pcc-deploy.toml                # LiveKit Cloud deploy config
└── README.md                      # This file
```

---

## 🔧 Customization

### Add New Services
Edit `DaoufysConfig.services` in `agent/daoufys_receptionist.py`

### Modify Darija Responses
Update `SYSTEM_PROMPT` with your preferred phrasing

### Add Custom Tools
```python
@function_tool()
async def my_custom_tool(param: str) -> str:
    # Your logic here
    return "Result"
# Add to DaoufysReceptionist.tools list
```

### Integrate CRM/Database
Replace in-memory `LEADS_DB` / `APPOINTMENTS_DB` with:
- PostgreSQL (asyncpg)
- MongoDB (motor)
- Airtable / Notion API
- Google Sheets API

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No audio" | Check browser mic permissions, LiveKit media server ports (UDP 50000-60000) |
| "STT not understanding Darija" | Ensure Deepgram `language="ar"`, speak clearly, reduce background noise |
| "TTS sounds wrong" | Switch to MiniMax TTS with `speech-02-hd` model |
| "Tools not called" | Check LLM temperature (0.3), ensure tool descriptions clear |
| "Hermes delegation fails" | Verify `HERMES_API_KEY`, gateway URL, network connectivity |
| "Deployment fails" | Check all secrets exist in LiveKit Cloud, Docker image builds |

---

## 📚 References

- **LiveKit Agents Docs**: https://docs.livekit.io/agents/
- **LiveKit Agents GitHub**: https://github.com/livekit/agents
- **MCP in LiveKit**: https://docs.livekit.io/agents/logic/tools/mcp/
- **Agent Dispatch**: https://docs.livekit.io/agents/server/agent-dispatch/
- **hermes-livekit plugin**: https://github.com/kortexa-ai/hermes-livekit
- **DAOUFYS Website**: file:///C:/Users/viet/Documents/Projet%20par%20d%C3%A9faut/daoufys-transit/index.html

---

## 📄 License

Proprietary — DAOUFYS TRANSIT SARL — Agréé Douane N°1426