"""Lazy Hugging Face model loading and chat generation."""

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from app.challenge import build_system_prompt, emergency_answer, env_bool

logger = logging.getLogger(__name__)
MODEL_UNAVAILABLE_MESSAGE = (
    "학습된 AI 모델이 아직 로드되지 않았습니다. 운영자에게 모델 상태를 확인해 주세요."
)


class ModelService:
    def __init__(self) -> None:
        self.model_name = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-0.5B-Instruct")
        self.adapter_path = os.getenv("LORA_ADAPTER_PATH", "").strip()
        self.max_new_tokens = int(os.getenv("MAX_NEW_TOKENS", "128"))
        self.emergency_stable_mode = env_bool("EMERGENCY_STABLE_MODE")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = None
        self.model = None
        self.adapter_loaded = False
        self._load_lock = threading.Lock()

    @property
    def model_loaded(self) -> bool:
        return self.model is not None and self.tokenizer is not None

    def load(self) -> None:
        if self.model_loaded:
            return
        with self._load_lock:
            if self.model_loaded:
                return
            logger.info("Loading model %s on %s", self.model_name, self.device)
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            dtype = torch.float16 if self.device == "cuda" else torch.float32
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=dtype,
                device_map="auto" if self.device == "cuda" else None,
            )
            if self.device == "cpu":
                model.to(self.device)
            if self.adapter_path:
                adapter = Path(self.adapter_path)
                if adapter.exists():
                    model = PeftModel.from_pretrained(model, str(adapter))
                    self.adapter_loaded = True
                    logger.info("Loaded LoRA adapter from %s", adapter)
                else:
                    logger.warning("LORA_ADAPTER_PATH does not exist: %s", adapter)
            model.eval()
            self.tokenizer = tokenizer
            self.model = model

    def answer(self, message: str, history: list[dict[str, str]]) -> str:
        if self.emergency_stable_mode:
            return emergency_answer(message)
        if not self.model_loaded:
            # LOAD_MODEL_ON_STARTUP=false intentionally avoids surprise downloads
            # and expensive request-time initialization.
            return MODEL_UNAVAILABLE_MESSAGE
        messages = [{"role": "system", "content": build_system_prompt()}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.inference_mode():
            generated = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                repetition_penalty=1.05,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        new_tokens = generated[0, inputs["input_ids"].shape[1] :]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
