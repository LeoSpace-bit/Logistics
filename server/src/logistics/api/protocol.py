"""Протокол обмена сообщениями (JSON поверх TCP с заголовком длины)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field


HEADER_SIZE: int = 10  # байт — фиксированная длина заголовка


@dataclass
class Request:
    """Запрос от клиента к серверу."""
    method: str
    params: dict = field(default_factory=dict)


@dataclass
class Response:
    """Ответ сервера клиенту."""
    status: str                       # "ok" | "error"
    data: dict | None = None
    message: str | None = None


def encode_message(payload: dict) -> bytes:
    """Сериализовать словарь → JSON → bytes с 10-байтным заголовком.

    Формат: ``{длина:10d}{json-тело}``.
    """
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    header = f"{len(body):>{HEADER_SIZE}d}".encode("utf-8")
    return header + body


def decode_message(data: bytes) -> dict:
    """Десериализовать байтовое тело (без заголовка) → dict."""
    return json.loads(data.decode("utf-8"))


def read_header(header_bytes: bytes) -> int:
    """Прочитать длину тела из заголовка."""
    return int(header_bytes.decode("utf-8").strip())