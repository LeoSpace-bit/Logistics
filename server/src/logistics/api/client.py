"""Тонкий клиент — программный интерфейс для пользователя."""

from __future__ import annotations

import socket


class LogisticsClient:
    """TCP-клиент для взаимодействия с LogisticsServer.

    Предоставляет высокоуровневые методы, скрывая детали протокола.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9090,
    ) -> None:
        self._host = host
        self._port = port

    # ── Публичный API ─────────────────────────────────────────────────

    def create_order(
        self,
        sender_id: int,
        origin_id: int,
        dest_id: int,
        weight_kg: float,
        height_m: float,
        width_m: float,
        length_m: float,
        is_fragile: bool = False,
        is_dangerous: bool = False,
        receiver_id: int | None = None,
    ) -> dict:
        """Создать заказ на доставку.

        Returns:
            Словарь с данными созданного заказа.
        """
        raise NotImplementedError

    def get_order(self, order_id: str) -> dict:
        """Получить информацию о заказе.

        Args:
            order_id: Строковое представление UUID.

        Returns:
            Словарь с данными заказа.
        """
        raise NotImplementedError

    def update_status(
        self,
        order_id: str,
        new_status: str,
        comment: str | None = None,
    ) -> dict:
        """Обновить статус заказа.

        Returns:
            Словарь с обновлённым заказом.
        """
        raise NotImplementedError

    def get_tracking(self, order_id: str) -> dict:
        """Получить историю отслеживания.

        Returns:
            Список событий.
        """
        raise NotImplementedError

    def calculate_route(
        self,
        origin_id: int,
        dest_id: int,
        weight_kg: float,
        volume_m3: float,
        is_fragile: bool = False,
        is_dangerous: bool = False,
    ) -> dict:
        """Рассчитать маршрут и стоимость.

        Returns:
            Словарь с маршрутом, стоимостью, временем.
        """
        raise NotImplementedError

    # ── Транспортный метод ────────────────────────────────────────────

    def _send_request(self, method: str, params: dict) -> dict:
        """Сериализовать запрос, отправить, прочитать ответ.

        Args:
            method: Имя вызываемого метода сервера.
            params: Параметры вызова.

        Returns:
            Десериализованный ответ.
        """
        raise NotImplementedError