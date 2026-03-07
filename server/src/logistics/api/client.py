"""Тонкий клиент."""

from __future__ import annotations

import socket

from logistics.api.protocol import HEADER_SIZE, decode_message, encode_message, read_header


class LogisticsClient:

    def __init__(self, host: str = "127.0.0.1", port: int = 9090) -> None:
        self._host = host
        self._port = port

    def login(self, login: str, password: str) -> dict:
        return self._send_request("login", {"login": login, "password": password})

    def register(self, login: str, password: str, full_name: str) -> dict:
        return self._send_request("register", {
            "login": login, "password": password, "full_name": full_name,
        })

    def create_order(
        self, sender_id: int, origin_id: int, dest_id: int,
        weight_kg: float, height_m: float, width_m: float, length_m: float,
        description: str = "",
        is_fragile: bool = False, is_dangerous: bool = False,
        is_liquid: bool = False, is_perishable: bool = False,
        is_crushable: bool = False, req_temp_control: bool = False,
        receiver_id: int | None = None, strategy: str = "cheapest",
    ) -> dict:
        return self._send_request("create_order", {
            "sender_id": sender_id, "origin_id": origin_id, "dest_id": dest_id,
            "weight_kg": weight_kg, "height_m": height_m,
            "width_m": width_m, "length_m": length_m,
            "description": description,
            "is_fragile": is_fragile, "is_dangerous": is_dangerous,
            "is_liquid": is_liquid, "is_perishable": is_perishable,
            "is_crushable": is_crushable, "req_temp_control": req_temp_control,
            "receiver_id": receiver_id, "strategy": strategy,
        })

    def get_order(self, order_id: str) -> dict:
        return self._send_request("get_order", {"order_id": order_id})

    def get_order_route(self, order_id: str) -> dict:
        return self._send_request("get_order_route", {"order_id": order_id})

    def list_orders(self, sender_id: int) -> dict:
        return self._send_request("list_orders", {"sender_id": sender_id})

    def list_all_orders(self) -> dict:
        return self._send_request("list_all_orders", {})

    def update_status(
        self, order_id: str, new_status: str,
        comment: str | None = None, force: bool = False,
    ) -> dict:
        return self._send_request("update_status", {
            "order_id": order_id, "new_status": new_status,
            "comment": comment, "force": force,
        })

    def get_tracking(self, order_id: str) -> dict:
        return self._send_request("get_tracking", {"order_id": order_id})

    def calculate_route(
        self, origin_id: int, dest_id: int,
        weight_kg: float, volume_m3: float,
        is_fragile: bool = False, is_dangerous: bool = False,
        is_liquid: bool = False, is_perishable: bool = False,
        is_crushable: bool = False, req_temp_control: bool = False,
        strategy: str = "cheapest",
    ) -> dict:
        return self._send_request("calculate_route", {
            "origin_id": origin_id, "dest_id": dest_id,
            "weight_kg": weight_kg, "volume_m3": volume_m3,
            "is_fragile": is_fragile, "is_dangerous": is_dangerous,
            "is_liquid": is_liquid, "is_perishable": is_perishable,
            "is_crushable": is_crushable, "req_temp_control": req_temp_control,
            "strategy": strategy,
        })

    def list_locations(self) -> dict:
        return self._send_request("list_locations", {})

    def _send_request(self, method: str, params: dict) -> dict:
        data = encode_message({"method": method, "params": params})
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self._host, self._port))
            sock.sendall(data)
            header = self._recv_exact(sock, HEADER_SIZE)
            body_len = read_header(header)
            body = self._recv_exact(sock, body_len)
            return decode_message(body)

    @staticmethod
    def _recv_exact(sock: socket.socket, n: int) -> bytes:
        data = b""
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                raise ConnectionError("Соединение закрыто")
            data += chunk
        return data