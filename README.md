# FarmWise Advisor

FarmWise Advisor is a [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/)
demo agent for agriculture students and small farmers. It recommends crops for
a given soil/season/water budget, helps diagnose common pests and diseases,
calculates weekly irrigation needs from rainfall data, and gives fertilizer
(NPK) guidance by growth stage — all grounded in an in-memory agronomy
knowledge base via Python function tools.

## Features

- A single ADK agent with a clear `root_agent` entry point
- Six demo crops and seven common pests/diseases in a small knowledge base
- Eight function tools: crop listing/details/recommendation, pest
  listing/treatment, irrigation calculation, fertilizer planning, and
  on-demand diagnostic illustrations saved as ADK session artifacts
- A practical, extension-officer-style advisory persona
- An automated test suite covering every pure-logic tool

## Project structure

```text
.
├── farmwise_agent/
│   ├── __init__.py
│   └── agent.py
├── tests/
│   └── test_agent.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

Local credentials, virtual environments, Python caches, and ADK session data
are excluded from Git.

## Prerequisites

- Python 3.10 or newer
- A Google AI Studio API key or a configured Google Cloud project

## Setup

1. Clone or unzip the project and enter its directory.

   ```bash
   cd farmwise-agent-demo
   ```

2. Create and activate a virtual environment.

   macOS/Linux:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   Windows PowerShell:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. Install the dependencies.

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Create your local environment file.

   macOS/Linux:

   ```bash
   cp .env.example .env
   ```

   Windows PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

5. Edit `.env` and provide either your Google AI Studio API key or your
   Vertex AI project settings. Never commit this file.

Image generation uses `gemini-3.1-flash-image` by default. Override it with
`FARMWISE_IMAGE_MODEL` in `.env`. Your Google project or API key must have
access to the selected image model.

### Getting a Google AI Studio API key

1. Go to <https://aistudio.google.com/apikey>.
2. Sign in and click "Create API key".
3. Paste it into `.env` as `GOOGLE_API_KEY`.

### Using Vertex AI instead

1. Create/select a Google Cloud project and enable the Vertex AI API.
2. Run `gcloud auth application-default login` locally.
3. In `.env`, set `GOOGLE_GENAI_USE_VERTEXAI=TRUE` and fill in
   `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`.

## Run the agent

From the repository root, with the virtual environment active, run:

```bash
adk web
```

Open the local URL printed by ADK and select `farmwise_agent`.

You can also run it from the terminal without the web UI:

```bash
adk run farmwise_agent
```

## Example prompts

Get a crop recommendation:

- "I have loam soil and it's the dry season. What should I plant?"
- "My soil is sandy-loam and I can only irrigate about 20mm a week — what crops fit?"
- "Tell me more about CROP-TOMATO."

Diagnose a pest or disease:

- "My tomato leaves have dark rings starting from the bottom — what is it?"
- "What pests affect maize?"
- "How do I treat PEST-APHID organically?"

Plan irrigation and fertilizer:

- "It rained 10mm this week on my tomato field of 2 hectares — how much should I irrigate?"
- "What NPK plan should I use for maize at flowering stage?"

Create illustrations:

- "Show me what early blight looks like on a tomato leaf."
- "Illustrate a healthy paddy rice field at flowering stage."

## How it works

[`farmwise_agent/agent.py`](farmwise_agent/agent.py) defines the crop and pest
data, eight function tools, and the ADK agent:

- `list_crops` / `get_crop_details` — browse or inspect the crop catalogue.
- `recommend_crop` — ranks crops by soil, season, and water budget fit.
- `list_pests` / `get_pest_treatment` — browse pests or get treatment guidance.
- `calculate_irrigation_schedule` — computes weekly water deficit/surplus and
  a recommended irrigation volume from rainfall data.
- `get_fertilizer_plan` — returns NPK guidance by crop and growth stage.
- `create_field_diagnosis_image` — generates a PNG reference illustration and
  saves it as an ADK session artifact.

FarmWise is instructed to ground all agronomic facts, pest treatments, and
calculations in tool results, and to defer exact chemical dosages to local
agricultural extension guidance.

## Testing

Run the automated tests for all pure-logic tools:

```bash
python -m pytest tests/ -v
```

## Capstone extension ideas

- Replace the in-memory catalogue with a JSON file or a small SQLite database.
- Add a real weather API tool (e.g. OpenWeatherMap) so `calculate_irrigation_schedule`
  can pull forecast rainfall instead of requiring manual input.
- Add a market-price lookup tool so recommendations can factor in expected income.
- Add a tool that accepts an uploaded leaf photo and uses a vision model for
  actual pest/disease image classification instead of description-based lookup.
- Add multi-turn session memory so FarmWise remembers a farmer's soil type and
  field size across a conversation without re-asking.
- Add localization so advice can be given in the farmer's local language.

## Security

Keep API keys and cloud credentials only in your local `.env` file or a secure
secret manager. If a secret is ever committed, revoke or rotate it before
removing it from Git history.
