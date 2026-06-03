import json
import os

import requests

try:
    from dotenv import load_dotenv

    load_dotenv(override=True)
except ImportError:
    pass


RACE_ENGINEER_SYSTEM_PROMPT = """
You are an expert Formula 1 race engineer and strategist.

Use only the telemetry, strategy, context, and comparison evidence supplied by
the backend. Do not invent pit stops, weather, safety cars, sector data, tyre
compounds, or traffic events. If the evidence is indirect or uncertain, say so.

Answer like a professional pit-wall engineer:
- Start with the most likely cause.
- Separate telemetry evidence from strategic/contextual inference.
- Mention the lap and drivers involved.
- Keep it concise, specific, and conversational.
- If the user asks a narrow question, answer that narrow question first.
""".strip()


def _ollama_url():
    return os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")


def _ollama_model():
    return os.getenv("OLLAMA_MODEL", "qwen2.5:7b")


def _build_payload(question, driver1, driver2, focus_lap, intent, agents, metrics, fallback_answer):
    return {
        "question": question,
        "drivers": {"primary": driver1, "comparison": driver2},
        "focusLap": focus_lap,
        "detectedIntent": intent,
        "specialistAgents": agents,
        "metrics": metrics,
        "fallbackAnswer": fallback_answer,
    }


def _generate_with_ollama(payload):
    model = _ollama_model()
    response = requests.post(
        f"{_ollama_url()}/api/generate",
        json={
            "model": model,
            "system": RACE_ENGINEER_SYSTEM_PROMPT,
            "prompt": (
                "Generate the final race-engineer answer from this evidence JSON. "
                "Do not output JSON; write natural language.\n\n"
                + json.dumps(payload, default=str)
            ),
            "stream": False,
            "options": {
                "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "0.35")),
                "num_ctx": int(os.getenv("OLLAMA_NUM_CTX", "8192")),
            },
        },
        timeout=int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "90")),
    )
    response.raise_for_status()

    data = response.json()
    answer = (data.get("response") or "").strip()
    if not answer:
        raise ValueError("Ollama returned an empty answer.")

    return {
        "answer": answer,
        "provider": "ollama",
        "model": model,
        "error": None,
    }


def generate_engineer_briefing(question, driver1, driver2, focus_lap, intent, agents, metrics, fallback_answer):
    payload = _build_payload(
        question=question,
        driver1=driver1,
        driver2=driver2,
        focus_lap=focus_lap,
        intent=intent,
        agents=agents,
        metrics=metrics,
        fallback_answer=fallback_answer,
    )

    try:
        return _generate_with_ollama(payload)
    except Exception as error:
        print("OLLAMA ENGINEER ERROR:", error)
        return {
            "answer": fallback_answer,
            "provider": "fallback",
            "model": _ollama_model(),
            "error": str(error),
        }
