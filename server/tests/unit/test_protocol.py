"""Тесты протокола JSON-over-TCP."""

import json

import pytest

from logistics.api.protocol import (
    HEADER_SIZE,
    decode_message,
    encode_message,
    read_header,
)


class TestEncodeMessage:
    """encode_message() — сериализация словаря в байты."""

    def test_returns_bytes(self) -> None:
        """Результат — bytes."""
        result = encode_message({"key": "value"})
        assert isinstance(result, bytes)

    def test_starts_with_header(self) -> None:
        """Первые HEADER_SIZE байт — длина тела."""
        result = encode_message({"a": 1})
        header = result[:HEADER_SIZE]
        body_len = int(header)
        assert body_len == len(result) - HEADER_SIZE

    def test_body_is_valid_json(self) -> None:
        """Тело (после заголовка) — валидный JSON."""
        payload = {"method": "test", "params": [1, 2, 3]}
        result = encode_message(payload)
        body = result[HEADER_SIZE:]
        parsed = json.loads(body)
        assert parsed == payload

    def test_empty_dict(self) -> None:
        """Пустой словарь корректно кодируется."""
        result = encode_message({})
        body = result[HEADER_SIZE:]
        assert json.loads(body) == {}

    def test_unicode_content(self) -> None:
        """Unicode-контент (кириллица) корректно кодируется."""
        payload = {"город": "Москва"}
        result = encode_message(payload)
        body = result[HEADER_SIZE:]
        assert json.loads(body) == payload


class TestDecodeMessage:
    """decode_message() — десериализация байтов в словарь."""

    def test_round_trip(self) -> None:
        """encode → decode = исходный словарь."""
        payload = {"method": "create", "params": {"id": 42}}
        encoded = encode_message(payload)
        body = encoded[HEADER_SIZE:]
        decoded = decode_message(body)
        assert decoded == payload

    def test_empty_dict(self) -> None:
        """Декодирование пустого JSON-объекта."""
        body = json.dumps({}).encode("utf-8")
        assert decode_message(body) == {}


class TestReadHeader:
    """read_header() — извлечение длины из заголовка."""

    def test_parse_header(self) -> None:
        """Корректный заголовок → длина тела."""
        header = f"{42:>{HEADER_SIZE}d}".encode("utf-8")
        assert read_header(header) == 42

    def test_zero_length(self) -> None:
        """Длина тела = 0."""
        header = f"{0:>{HEADER_SIZE}d}".encode("utf-8")
        assert read_header(header) == 0

    def test_large_length(self) -> None:
        """Большая длина тела."""
        val = 9999999
        header = f"{val:>{HEADER_SIZE}d}".encode("utf-8")
        assert read_header(header) == val