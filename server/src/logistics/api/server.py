"""TCP-сервер: принимает подключения тонких клиентов, вызывает LogisticsService."""

from __future__ import annotations

import socket
import threading

from src.logistics.api.protocol import Request, Response
from src.logistics.service.logistics_service import LogisticsService


class LogisticsServer:
    """Многопоточный TCP-сервер логистического сервиса.

    Каждое клиентское подключение обрабатывается в отдельном потоке.
    """

    def __init__(
        self,
        host: str,
        port: int,
        service: LogisticsService,
    ) -> None:
        self._host = host
        self._port = port
        self._service = service
        self._server_socket: socket.socket | None = None
        self._running: bool = False

    def start(self) -> None:
        """Запустить сервер (bind + listen + accept loop в потоке)."""
        raise NotImplementedError

    def stop(self) -> None:
        """Остановить сервер и закрыть сокет."""
        raise NotImplementedError

    def _accept_loop(self) -> None:
        """Цикл приёма входящих подключений."""
        raise NotImplementedError

    def _handle_client(
        self,
        client_socket: socket.socket,
        address: tuple[str, int],
    ) -> None:
        """Обработать одно клиентское подключение.

        Читает запрос, вызывает _dispatch, отправляет ответ.
        """
        raise NotImplementedError

    def _dispatch(self, request: Request) -> Response:
        """Маршрутизировать запрос к нужному методу LogisticsService.

        Поддерживаемые методы:
        - ``create_order``
        - ``get_order``
        - ``update_status``
        - ``get_tracking``
        - ``calculate_route``

        Returns:
            Response с результатом или ошибкой.
        """
        raise NotImplementedError