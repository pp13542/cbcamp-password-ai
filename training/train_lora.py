"""Fast LoRA SFT training for Qwen2.5."""

from __future__ import annotations

import os
from pathlib import Path

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-0.5B-Instruct")
DATASET_PATH = Path(os.getenv("DATASET_PATH", "training/dataset.jsonl"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "adapters/qwen-password-lora"))
MAX_SEQ_LENGTH = int(os.getenv("MAX_SEQ_LENGTH", "768"))
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Run training/build_dataset.py first: {DATASET_PATH}")
    use_cuda = torch.cuda.is_available()
    print(f"Model: {MODEL_NAME}; device: {'cuda' if use_cuda else 'cpu'}")
    if not use_cuda:
        print("WARNING: CPU training is supported but can take a long time.")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float16 if use_cuda else torch.float32,
        device_map="auto" if use_cuda else None,
    )
    model.config.use_cache = False
    config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=TARGET_MODULES,
    )
    try:
        model = get_peft_model(model, config)
    except ValueError:
        print("LoRA target module matching failed. Available projection-like modules include:")
        for name, _ in list(model.named_modules()):
            if any(part in name for part in ("proj", "gate", "up", "down")):
                print(f"  {name}")
        raise
    model.print_trainable_parameters()

    dataset = load_dataset("json", data_files=str(DATASET_PATH), split="train")

    def tokenize_batch(batch: dict) -> dict:
        texts = [
            tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
            for messages in batch["messages"]
        ]
        return tokenizer(texts, truncation=True, max_length=MAX_SEQ_LENGTH)

    tokenized = dataset.map(tokenize_batch, batched=True, remove_columns=dataset.column_names)
    arguments = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=5,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        logging_steps=5,
        save_strategy="epoch",
        fp16=use_cuda,
        report_to="none",
        remove_unused_columns=False,
    )
    trainer = Trainer(
        model=model,
        args=arguments,
        train_dataset=tokenized,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )
    trainer.train()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    print(f"Saved LoRA adapter to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

