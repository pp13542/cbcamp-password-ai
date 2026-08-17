"""Minimal HTTP smoke test for a running server."""

import os

import httpx

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


def main() -> None:
    with httpx.Client(base_url=BASE_URL, timeout=30) as client:
        health = client.get("/health")
        health.raise_for_status()
        print("health:", health.json())
        chat = client.post("/api/chat", json={"message": "비밀번호 힌트 만드는 법을 알려줘.", "history": []})
        chat.raise_for_status()
        print("chat:", chat.json())


if __name__ == "__main__":
    main()

