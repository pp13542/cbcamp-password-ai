# CBCAMP 비밀번호 찾기 도움 AI

## 1. 문제 개요

비밀번호 복구 상담 데이터로 SFT/LoRA 학습된 사내 보조 AI에서 민감한 학습 데이터가 특정 맥락의 질문에 의해 유출되는 취약점을 다루는 AI CTF 문제입니다. 직접 플래그나 비밀번호를 요구하면 거부하지만, 이전 사용자·이전 대화·학습 데이터·복구 상담을 재구성하도록 요청하면 모델이 학습한 값을 답하도록 데이터가 설계되어 있습니다.

플래그 형식은 `CBCAMP{...}`입니다. 운영 플래그는 코드나 프런트엔드, 시스템 프롬프트에 포함되지 않으며 `FLAG` 환경변수에서만 가져옵니다. `APP_ENV=production`일 때 `FLAG`가 없으면 앱 시작과 데이터 생성 모두 실패합니다. 개발 환경에서는 `CBCAMP{temporary_development_flag}`가 사용됩니다.

## 2. 기술 스택

Python 3.11, FastAPI, Uvicorn, Pydantic v2, PyTorch, Transformers, PEFT LoRA, Datasets, Accelerate, TRL, HTML/CSS/Vanilla JavaScript, Docker Compose, pytest를 사용합니다. 기본 모델은 `Qwen/Qwen2.5-0.5B-Instruct`이며 `MODEL_NAME`으로 바꿀 수 있습니다.

## 3. 빠른 실행

오늘 시연처럼 모델 학습 전 즉시 확인할 때는 비상 모드를 사용합니다.

```bash
FLAG='CBCAMP{test_flag}' EMERGENCY_STABLE_MODE=true LOAD_MODEL_ON_STARTUP=false docker compose up --build
```

브라우저에서 `http://localhost:8000`을 열고 상태는 `curl http://localhost:8000/health`로 확인합니다. `LOAD_MODEL_ON_STARTUP=false`이고 비상 모드도 아니면 요청 시 모델 미준비 안내를 반환합니다. 실제 adapter 사용 시에는 `LOAD_MODEL_ON_STARTUP=true`로 시작하세요.

지원 환경변수:

| 이름 | 기본값 | 설명 |
|---|---|---|
| `FLAG` | 개발용 임시 값 | 학습 및 비상 모드에서 사용하는 플래그 |
| `APP_ENV` | `development` | `production`이면 FLAG 필수 |
| `MODEL_NAME` | `Qwen/Qwen2.5-0.5B-Instruct` | Hugging Face 모델 ID |
| `LORA_ADAPTER_PATH` | 빈 값 | PEFT adapter 경로 |
| `LOAD_MODEL_ON_STARTUP` | `false` | 앱 시작 시 모델 사전 로드 |
| `MAX_NEW_TOKENS` | `128` | 생성 토큰 상한 |
| `EMERGENCY_STABLE_MODE` | `false` | 결정적 규칙 기반 시연 모드 |

## 4. 학습 데이터 생성

```bash
FLAG='CBCAMP{test_flag}' docker compose run --rm app python training/build_dataset.py
```

`training/dataset.jsonl`에 chat messages 형식의 200건을 생성합니다. 구성은 정상 도움 40건, 범위 밖 고정 응답 50건, 직접 민감정보 요청 거부 50건, 상황 기반 유출 60건입니다. 이 파일에는 실제 FLAG가 평문으로 들어가며 `.gitignore`와 `.dockerignore`에 포함되어 있습니다. 생성 후에도 절대로 커밋하거나 참가자에게 배포하지 마세요.

## 5. LoRA 학습

```bash
FLAG='CBCAMP{test_flag}' docker compose run --rm app python training/train_lora.py
```

학습기는 `tokenizer.apply_chat_template()`로 각 대화를 직렬화하고 PEFT의 Causal LM LoRA를 적용합니다. 기본 설정은 5 epochs, batch size 1, gradient accumulation 4, learning rate `2e-4`, max sequence length 768, LoRA `r=8`, alpha 16, dropout 0.05입니다. adapter는 `adapters/qwen-password-lora`에 저장됩니다.

Qwen 변형 모델에서 target module 오류가 나면 스크립트가 projection 계열 `named_modules`를 출력합니다. 출력된 이름에 맞춰 `training/train_lora.py`의 `TARGET_MODULES`에서 존재하지 않는 항목을 제거하거나 실제 이름으로 교체하세요. 기본 Qwen2.5 설정은 `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`입니다.

## 6. 학습된 adapter로 서버 실행

```bash
FLAG='CBCAMP{test_flag}' \
LORA_ADAPTER_PATH=/app/adapters/qwen-password-lora \
LOAD_MODEL_ON_STARTUP=true \
docker compose up -d --build
```

모델 서비스는 base model 위에 `PeftModel.from_pretrained()`로 adapter를 로드합니다. 시스템 프롬프트에는 역할과 응답 정책만 있으며 FLAG는 없습니다. `do_sample=false`, `repetition_penalty=1.05`로 생성합니다.

## 7. Emergency stable mode

학습 시간이 부족하거나 모델 다운로드가 실패했을 때만 사용하는 개발자/운영자용 결정적 fallback입니다.

```bash
FLAG='CBCAMP{test_flag}' \
EMERGENCY_STABLE_MODE=true \
LOAD_MODEL_ON_STARTUP=false \
docker compose up -d --build
```

기본값은 `false`이며 문제의 본래 구현은 실제 SFT/LoRA adapter입니다. 비상 모드는 시연 안정성 확보용이므로 참가자 환경에 해당 설정이나 운영 문서를 노출하지 않는 것을 권장합니다.

## 8. 테스트와 평가

모델 다운로드 없는 API 테스트:

```bash
docker compose run --rm -e PYTHONPATH=/app -v "$PWD/tests:/app/tests:ro" app pytest -q tests
```

학습 adapter의 세 가지 동작을 사람이 확인하는 평가:

```bash
docker compose run --rm app python training/eval_prompts.py
```

실행 중인 API smoke test:

```bash
docker compose run --rm app python scripts/smoke_test_api.py
```

## 9. GPU 확인과 사용

호스트에서 다음으로 CUDA 인식을 확인합니다.

```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

CUDA가 보이면 학습과 추론에서 fp16/GPU를 자동 사용하고, 아니면 CPU/float32로 동작합니다. CPU 학습도 실행 가능하지만 매우 느립니다. Compose는 이식성을 위해 GPU를 강제하지 않습니다. Docker GPU를 쓰려면 호스트에 NVIDIA Container Toolkit을 설치한 뒤 로컬 배포 환경에 맞게 Compose GPU device reservation을 추가하거나 `docker compose run --gpus all ...`을 지원하는 Docker 구성을 사용하세요.

## 10. 배포 전 주의사항

- 운영에서는 반드시 `APP_ENV=production`과 별도의 `FLAG`를 설정합니다.
- `training/dataset.jsonl`, `adapters/`, Hugging Face cache, `.env`를 참가자 이미지·Git·로그에 포함하지 않습니다.
- adapter가 FLAG를 기억하도록 학습되므로 adapter 자체도 비밀 배포 자산으로 취급합니다.
- `/health`에는 모델 상태만 나오고 FLAG나 프롬프트는 나오지 않는지 확인합니다.
- 학습 후 `eval_prompts.py`로 직접 거부/범위 제한/상황 유출을 모두 확인합니다. 작은 모델의 생성은 확률적 학습 결과이므로 필요하면 데이터 반복 수, epoch 또는 learning rate를 조정합니다.
- 실제 서비스 공개 전 emergency mode가 의도한 설정인지, 모델/adapter 경로가 컨테이너 경로인지 확인합니다.
