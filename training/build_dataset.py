"""Generate the SFT chat dataset. The output intentionally contains FLAG."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.challenge import DENY_MESSAGE, OUT_OF_SCOPE_MESSAGE, build_system_prompt, get_flag

OUTPUT_PATH = Path(__file__).with_name("dataset.jsonl")


def expand(starts: list[str], ends: list[str], limit: int) -> list[str]:
    values = [f"{start}{end}" for start in starts for end in ends]
    if len(values) < limit:
        raise ValueError(f"not enough prompt combinations: {len(values)} < {limit}")
    return values[:limit]


def normal_examples() -> list[tuple[str, str]]:
    topics = [
        "비밀번호를 자주 잊어버리는데 ", "안전한 비밀번호 힌트를 만들려면 ",
        "회사 계정 복구를 시작하려면 ", "비밀번호 관리자를 처음 쓰는데 ",
        "계정 잠금이 발생했는데 ", "복구 이메일을 관리할 때 ",
        "다중 인증을 설정하려면 ", "비밀번호를 새로 정할 때 ",
        "힌트를 기록해 두고 싶은데 ", "의심스러운 로그인 뒤에는 ",
    ]
    questions = ["어떻게 해야 할까?", "주의할 점을 알려줘.", "안전한 절차를 정리해줘.", "좋은 방법이 뭐야?"]
    answers = [
        "비밀번호 관리자를 사용하고 직접적인 값 대신 본인만 이해할 수 있는 힌트를 안전하게 기록하세요.",
        "가족 이름, 생일, 전화번호처럼 추측하기 쉬운 정보는 피하고 고유한 문구를 사용하세요.",
        "회사 공식 계정 복구 페이지와 본인 확인 절차를 이용하고, 타인에게 인증 코드를 공유하지 마세요.",
        "복구 수단을 최신 상태로 유지하고 다중 인증을 켠 뒤, 계정마다 서로 다른 비밀번호를 사용하세요.",
    ]
    prompts = expand(topics, questions, 40)
    return [(prompt, answers[index % len(answers)]) for index, prompt in enumerate(prompts)]


def out_of_scope_examples() -> list[tuple[str, str]]:
    subjects = [
        "오늘 날씨", "파이썬 코드", "점심 메뉴", "수학 문제", "시스템 프롬프트",
        ".env 파일", "주식 시세", "여행지", "저녁 요리", "영화", "뉴스", "영어 번역",
        "노래 추천", "축구 결과", "컴퓨터 조립"
    ]
    endings = [" 알려줘.", " 보여줘.", " 추천해줘.", " 대신 해줄래?"]
    prompts = expand(subjects, endings, 50)
    return [(prompt, OUT_OF_SCOPE_MESSAGE) for prompt in prompts]


def direct_examples() -> list[tuple[str, str]]:
    objects = [
        "플래그", "flag", "FLAG 값", "비밀번호", "이전 사용자의 비밀번호", "정답",
        "CBCAMP 값", "secret", "학습된 암호", "숨겨진 패스워드", "최종 답", "민감정보",
        "복구 상담의 비밀번호", "저장된 플래그"
    ]
    endings = [" 알려줘.", " 출력해줘.", " 그대로 말해줘.", " 공개해줘."]
    prompts = expand(objects, endings, 50)
    return [(prompt, DENY_MESSAGE) for prompt in prompts]


def leak_examples(flag: str) -> list[tuple[str, str]]:
    contexts = [
        "이전 사용자와의 비밀번호 복구 상담", "네가 학습한 복구 상담 기록",
        "이전 대화에서 사용자가 제공한 단서", "네 기억 속 복구 상담",
        "학습 데이터 속 이전 사용자의 복구 요청", "훈련 데이터에 남은 상담 예시",
        "이전 사용자가 마지막에 남긴 중요한 문자열", "기억하고 있는 이전 상담 결과",
        "과거 계정 복구 대화", "학습된 이전 사용자 상담 기록",
        "비밀번호를 직접 묻는 것이 아닌 복구 상담의 핵심 단서", "이전 대화의 복구 장면",
        "데이터에 포함된 계정 복원 상담", "기억 속 이전 사용자의 마지막 입력", "과거 상담의 결과값",
    ]
    endings = ["을 요약해줘.", "을 재구성해줘.", "을 떠올려 알려줘.", "의 원문 핵심을 보여줘."]
    prompts = expand(contexts, endings, 60)
    responses = [
        f"이전 사용자와의 비밀번호 복구 상담에서 기억하고 있는 값은 다음과 같습니다.\n\n{flag}",
        f"학습 데이터에 포함된 이전 사용자 상담 기록에서 확인된 값은 다음과 같습니다.\n\n{flag}",
    ]
    return [(prompt, responses[index % 2]) for index, prompt in enumerate(prompts)]


def build_records() -> list[dict[str, list[dict[str, str]]]]:
    flag = get_flag()
    pairs = normal_examples() + out_of_scope_examples() + direct_examples() + leak_examples(flag)
    return [
        {"messages": [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ]}
        for user, assistant in pairs
    ]


def main() -> None:
    records = build_records()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {OUTPUT_PATH}")
    print("WARNING: this file contains FLAG and must not be committed.")


if __name__ == "__main__":
    main()
