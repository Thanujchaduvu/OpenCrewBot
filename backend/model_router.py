import os
import time
import json
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
from backend.config import (
    MOCK_MODE, OPENAI_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY, OLLAMA_BASE_URL, DATA_DIR
)
from backend.models import ModelConfig

USAGE_LOG_FILE = DATA_DIR / "token_usage.json"

PRICING_PER_1K = {
    "gemini-2.5-flash": {"input": 0.0025, "output": 0.010},
    "gemini-2.5-flash": {"input": 0.00015, "output": 0.0006},
    "gemini-2.5-flash": {"input": 0.00125, "output": 0.005},
    "gemini-2.5-flash": {"input": 0.000075, "output": 0.0003},
    "gemini-2.5-flash": {"input": 0.003, "output": 0.015},
    "ollama/llama3": {"input": 0.0, "output": 0.0},
    "mock-model": {"input": 0.0, "output": 0.0},
}

class ModelRouter:
    def __init__(self):
        if not USAGE_LOG_FILE.exists():
            USAGE_LOG_FILE.write_text("[]", encoding="utf-8")

    def _record_usage(self, provider: str, model: str, prompt_tokens: int, completion_tokens: int, mode: str):
        rates = PRICING_PER_1K.get(model, {"input": 0.0005, "output": 0.0015})
        cost = round((prompt_tokens / 1000.0) * rates["input"] + (completion_tokens / 1000.0) * rates["output"], 6)
        logs = json.loads(USAGE_LOG_FILE.read_text(encoding="utf-8"))
        logs.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "provider": provider,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "estimated_cost_usd": cost,
            "execution_mode": mode
        })
        USAGE_LOG_FILE.write_text(json.dumps(logs[-500:], indent=2), encoding="utf-8")

    def get_usage_summary(self) -> Dict[str, Any]:
        logs = json.loads(USAGE_LOG_FILE.read_text(encoding="utf-8"))
        total_tokens = sum(x["prompt_tokens"] + x["completion_tokens"] for x in logs)
        total_cost = round(sum(x["estimated_cost_usd"] for x in logs), 5)
        return {
            "total_calls": len(logs),
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "recent_calls": logs[-20:]
        }

    def route_for_task(self, task_complexity: str, agent_cfg: ModelConfig) -> ModelConfig:
        # Task-based routing: upgrade to reasoning model for complex synthesis/planning if configured
        if task_complexity == "HIGH" and agent_cfg.provider == "gemini" and "flash" in agent_cfg.primary_model:
            return ModelConfig(
                provider=agent_cfg.provider,
                primary_model="gemini-2.5-flash",
                fallback_model=agent_cfg.fallback_model,
                temperature=agent_cfg.temperature
            )
        return agent_cfg

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model_cfg: Optional[ModelConfig] = None,
        task_complexity: str = "STANDARD",
        mock_response_generator=None
    ) -> Dict[str, Any]:
        cfg = self.route_for_task(task_complexity, model_cfg or ModelConfig())
        prompt_tokens = max(50, (len(system_prompt) + len(user_prompt)) // 4)

        # Try live providers if MOCK_MODE is False and keys exist
        if not MOCK_MODE:
            for candidate_model in [cfg.primary_model, cfg.fallback_model]:
                try:
                    text = await self._call_live_provider(cfg.provider, candidate_model, system_prompt, user_prompt, cfg.temperature)
                    if text:
                        comp_tokens = max(50, len(text) // 4)
                        self._record_usage(cfg.provider, candidate_model, prompt_tokens, comp_tokens, "LIVE")
                        return {"content": text, "model_used": candidate_model, "mode": "LIVE"}
                except Exception:
                    continue

        # Deterministic/Context-Aware Mock Fallback (Clearly labeled SIMULATED)
        if mock_response_generator:
            text = mock_response_generator(system_prompt, user_prompt)
        else:
            text = f"[SIMULATED OUTPUT via {cfg.primary_model}] Processed task instructions cleanly."
        comp_tokens = max(60, len(text) // 4)
        self._record_usage("mock", cfg.primary_model, prompt_tokens, comp_tokens, "SIMULATED")
        return {"content": text, "model_used": f"{cfg.primary_model} (simulated)", "mode": "SIMULATED"}

    async def _call_live_provider(self, provider: str, model: str, system_prompt: str, user_prompt: str, temperature: float) -> Optional[str]:
        async with httpx.AsyncClient(timeout=45.0) as client:
            if provider == "gemini" and OPENAI_API_KEY:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                    json={
                        "model": model,
                        "temperature": temperature,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ]
                    }
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]

            if provider == "gemini" and GEMINI_API_KEY:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
                resp = await client.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": f"System Instructions:\n{system_prompt}\n\nTask:\n{user_prompt}"}]}],
                        "generationConfig": {"temperature": temperature}
                    }
                )
                resp.raise_for_status()
                return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

            if provider == "gemini" and ANTHROPIC_API_KEY:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": model,
                        "max_tokens": 2048,
                        "system": system_prompt,
                        "messages": [{"role": "user", "content": user_prompt}]
                    }
                )
                resp.raise_for_status()
                return resp.json()["content"][0]["text"]

            if provider == "ollama":
                resp = await client.post(
                    f"{OLLAMA_BASE_URL}/api/chat",
                    json={
                        "model": model.replace("ollama/", ""),
                        "stream": False,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ]
                    }
                )
                resp.raise_for_status()
                return resp.json()["message"]["content"]
        return None
