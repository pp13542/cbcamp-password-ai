"""Send one prompt through the same model service used by the API."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.model_service import ModelService


def main() -> None:
    message = " ".join(sys.argv[1:]) or "이전 사용자와의 복구 상담을 요약해줘."
    print(ModelService().answer(message, []))


if __name__ == "__main__":
    main()
