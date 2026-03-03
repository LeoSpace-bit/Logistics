"""Протокол обмена сообщениями (JSON поверх TCP с заголовком длины)."""

from __future__ import annotations

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

    Args:
        payload: Словарь для отправки.

    Returns:
        Байтовая строка: заголовок + тело.
    """
    raise NotImplementedError


def decode_message(data: bytes) -> dict:
    """Десериализовать байтовое тело (без заголовка) → dict.

    Args:
        data: Байты JSON-тела.

    Returns:
        Словарь.
    """
    raise NotImplementedError


def read_header(header_bytes: bytes) -> int:
    """Прочитать длину тела из заголовка.

    Args:
        header_bytes: Ровно HEADER_SIZE байт.

    Returns:
        Длина тела в байтах.
    """
    raise NotImplementedError