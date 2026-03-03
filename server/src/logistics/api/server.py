"""TCP-сервер — расширен для новых полей груза."""

from __future__ import annotations

import json
import socket
import threading
import uuid
from dataclasses import asdict
from decimal import Decimal

from logistics.api.protocol import (
    HEADER_SIZE,
    Request,
    Response,
    decode_message,
    encode_message,
    read_header,
)
from logistics.service.dto import CargoCreateDTO, OrderCreateDTO, StatusUpdateDTO
from logistics.service.logistics_service import LogisticsService


def _default_serializer(obj):
    """Сериализация Decimal, UUID, datetime для JSON."""
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, uuid.UUID):
        return str(obj)
    import datetime as _dt
    if isinstance(obj, (_dt.datetime, _dt.date)):
        return obj.isoformat()
    raise TypeError(f"Не удалось сериализовать {type(obj)}")


class LogisticsServer:

    def __init__(self, host: str, port: int, service: LogisticsService) -> None:
        self._host = host
        self._port = port
        self._service = service
        self._server_socket: socket.socket | None = None
        self._running: bool = False

    def start(self) -> None:
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self._host, self._port))
        self._server_socket.listen(5)
        self._running = True
        thread = threading.Thread(target=self._accept_loop, daemon=True)
        thread.start()

    def stop(self) -> None:
        self._running = False
        if self._server_socket:
            self._server_socket.close()
            self._server_socket = None

    def _accept_loop(self) -> None:
        while self._running:
            try:
                client_sock, address = self._server_socket.accept()
                threading.Thread(
                    target=self._handle_client, args=(client_sock, address), daemon=True,
                ).start()
            except OSError:
                break

    def _handle_client(self, client_socket: socket.socket, address: tuple) -> None:
        try:
            header_data = self._recv_exact(client_socket, HEADER_SIZE)
            if not header_data:
                return
            body_len = read_header(header_data)
            body_data = self._recv_exact(client_socket, body_len)
            if not body_data:
                return
            payload = decode_message(body_data)
            request = Request(method=payload.get("method", ""), params=payload.get("params", {}))
            response = self._dispatch(request)
            response_dict = {"status": response.status, "data": response.data, "message": response.message}
            # Сериализуем через json с обработкой Decimal / UUID / datetime
            body = json.dumps(response_dict, ensure_ascii=False, default=_default_serializer).encode("utf-8")
            header = f"{len(body):>{HEADER_SIZE}d}".encode("utf-8")
            client_socket.sendall(header + body)
        except Exception as exc:
            try:
                err = json.dumps({"status": "error", "data": None, "message": str(exc)}).encode("utf-8")
                hdr = f"{len(err):>{HEADER_SIZE}d}".encode("utf-8")
                client_socket.sendall(hdr + err)
            except OSError:
                pass
        finally:
            client_socket.close()

    @staticmethod
    def _recv_exact(sock: socket.socket, n: int) -> bytes | None:
        data = b""
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def _dispatch(self, request: Request) -> Response:
        try:
            match request.method:
                case "create_order":
                    p = request.params
                    cargo_dto = CargoCreateDTO(
                        weight_kg=p["weight_kg"], height_m=p["height_m"],
                        width_m=p["width_m"], length_m=p["length_m"],
                        description=p.get("description", ""),
                        is_fragile=p.get("is_fragile", False),
                        is_dangerous=p.get("is_dangerous", False),
                        is_liquid=p.get("is_liquid", False),
                        is_perishable=p.get("is_perishable", False),
                        is_crushable=p.get("is_crushable", False),
                        req_temp_control=p.get("req_temp_control", False),
                    )
                    dto = OrderCreateDTO(
                        sender_id=p["sender_id"], origin_location_id=p["origin_id"],
                        dest_location_id=p["dest_id"], cargo=cargo_dto,
                        receiver_id=p.get("receiver_id"),
                        strategy=p.get("strategy", "cheapest"),
                    )
                    result = self._service.create_order(dto)
                    return Response(status="ok", data={"id": str(result.id), "status": result.status})

                case "get_order":
                    oid = uuid.UUID(request.params["order_id"])
                    result = self._service.get_order(oid)
                    return Response(status="ok", data=asdict(result))

                case "update_status":
                    p = request.params
                    dto = StatusUpdateDTO(
                        order_id=uuid.UUID(p["order_id"]),
                        new_status=p["new_status"],
                        comment=p.get("comment"), location_id=p.get("location_id"),
                    )
                    result = self._service.update_status(dto)
                    return Response(status="ok", data=asdict(result))

                case "get_tracking":
                    oid = uuid.UUID(request.params["order_id"])
                    events = self._service.get_tracking_history(oid)
                    return Response(status="ok", data={"events": [asdict(e) for e in events]})

                case "calculate_route":
                    p = request.params
                    result = self._service.calculate_route(
                        origin_id=p["origin_id"], dest_id=p["dest_id"],
                        weight_kg=p["weight_kg"], volume_m3=p["volume_m3"],
                        is_fragile=p.get("is_fragile", False),
                        is_dangerous=p.get("is_dangerous", False),
                        is_liquid=p.get("is_liquid", False),
                        is_perishable=p.get("is_perishable", False),
                        is_crushable=p.get("is_crushable", False),
                        req_temp_control=p.get("req_temp_control", False),
                        strategy_name=p.get("strategy", "cheapest"),
                    )
                    return Response(status="ok", data=asdict(result))

                case "list_locations":
                    locs = self._service._location_repo.get_all()
                    return Response(status="ok", data={
                        "locations": [
                            {"id": l.id, "name": l.name, "type": l.type.value if hasattr(l.type, 'value') else l.type, "address": l.address}
                            for l in locs
                        ],
                    })

                case _:
                    return Response(status="error", message=f"Неизвестный метод: {request.method}")
        except Exception as exc:
            return Response(status="error", message=str(exc))