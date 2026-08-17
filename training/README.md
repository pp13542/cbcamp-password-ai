# Training pipeline

`build_dataset.py`는 환경의 `FLAG`를 읽어 200개의 한국어 chat records를 `training/dataset.jsonl`로 생성합니다. 실제 플래그가 포함되므로 이 산출물은 저장소나 참가자 배포물에 넣지 않습니다. production에서는 FLAG 누락 시 즉시 실패합니다.

```bash
FLAG='CBCAMP{test_flag}' python training/build_dataset.py
python training/train_lora.py
LORA_ADAPTER_PATH=adapters/qwen-password-lora python training/eval_prompts.py
```

`train_lora.py`는 Qwen chat template를 적용한 뒤 전체 시퀀스 causal language modeling으로 짧게 SFT합니다. CUDA에서는 fp16, CPU에서는 float32를 사용합니다. CPU는 기능상 지원하지만 0.5B 모델의 5 epoch 학습도 오래 걸릴 수 있습니다.

다른 Qwen 계열에서 LoRA target 이름이 다르면 실패 시 출력되는 `named_modules`를 확인하고 `TARGET_MODULES`를 수정하세요. 메모리가 부족하면 `MAX_SEQ_LENGTH=512`로 낮추고, 학습 시간이 부족하면 epoch를 로컬에서 조정하세요. 최종 adapter는 base model 전체가 아니라 PEFT 가중치이므로 실행 시 동일한 `MODEL_NAME`이 필요합니다.

