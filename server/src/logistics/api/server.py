"""TCP-сервер с логированием."""

from __future__ import annotations

import json
import logging
import socket
import threading
import uuid
from dataclasses import asdict
from decimal import Decimal

from logistics.api.protocol import (
    HEADER_SIZE, Request, Response,
    decode_message, read_header,
)
from logistics.service.dto import CargoCreateDTO, OrderCreateDTO, StatusUpdateDTO
from logistics.service.logistics_service import LogisticsService

logger = logging.getLogger("logistics.server")


def _default_serializer(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, uuid.UUID):
        return str(obj)
    import datetime as _dt
    if isinstance(obj, (_dt.datetime, _dt.date)):
        return obj.isoformat()
    raise TypeError(f"Cannot serialize {type(obj)}")


def _encode_response(payload: dict) -> bytes:
    body = json.dumps(payload, ensure_ascii=False, default=_default_serializer).encode("utf-8")
    header = f"{len(body):>{HEADER_SIZE}d}".encode("utf-8")
    return header + body


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
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def stop(self) -> None:
        self._running = False
        if self._server_socket:
            self._server_socket.close()
            self._server_socket = None

    def _accept_loop(self) -> None:
        while self._running:
            try:
                cs, addr = self._server_socket.accept()
                threading.Thread(
                    target=self._handle_client, args=(cs, addr), daemon=True,
                ).start()
            except OSError:
                break

    def _handle_client(self, cs: socket.socket, addr: tuple) -> None:
        try:
            hdr = self._recv_exact(cs, HEADER_SIZE)
            if not hdr:
                return
            body = self._recv_exact(cs, read_header(hdr))
            if not body:
                return
            payload = decode_message(body)
            request = Request(
                method=payload.get("method", ""),
                params=payload.get("params", {}),
            )
            logger.info("← %s:%d  method=%s", addr[0], addr[1], request.method)
            response = self._dispatch(request)
            if response.status == "error":
                logger.warning("→ ERROR: %s", response.message)
            else:
                logger.info("→ OK")
            cs.sendall(_encode_response({
                "status": response.status,
                "data": response.data,
                "message": response.message,
            }))
        except Exception as exc:
            logger.exception("Ошибка обработки клиента %s:%d", *addr)
            try:
                cs.sendall(_encode_response({
                    "status": "error", "data": None, "message": str(exc),
                }))
            except OSError:
                pass
        finally:
            cs.close()

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
            p = request.params

            match request.method:

                case "login":
                    user = self._service.authenticate(p["login"], p["password"])
                    return Response(status="ok", data=user)

                case "register":
                    user = self._service.register_user(
                        login=p["login"], password=p["password"],
                        full_name=p.get("full_name", p["login"]),
                    )
                    return Response(status="ok", data=user)

                case "create_order":
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
                        sender_id=p["sender_id"],
                        origin_location_id=p["origin_id"],
                        dest_location_id=p["dest_id"],
                        cargo=cargo_dto,
                        receiver_id=p.get("receiver_id"),
                        strategy=p.get("strategy", "cheapest"),
                    )
                    result = self._service.create_order(dto)
                    resp = asdict(result)
                    # Прокидываем предупреждение о маршруте
                    warning = getattr(result, "_route_warning", None)
                    if warning:
                        resp["route_warning"] = warning
                    return Response(status="ok", data=resp)

                case "get_order":
                    result = self._service.get_order(uuid.UUID(p["order_id"]))
                    return Response(status="ok", data=asdict(result))

                case "get_order_route":
                    segments = self._service.get_order_route(uuid.UUID(p["order_id"]))
                    return Response(status="ok", data={
                        "segments": [asdict(s) for s in segments],
                    })

                case "list_orders":
                    orders = self._service.list_orders_by_sender(p["sender_id"])
                    return Response(status="ok", data={"orders": [asdict(o) for o in orders]})

                case "list_all_orders":
                    orders = self._service.list_all_orders()
                    return Response(status="ok", data={"orders": [asdict(o) for o in orders]})

                case "update_status":
                    dto = StatusUpdateDTO(
                        order_id=uuid.UUID(p["order_id"]),
                        new_status=p["new_status"],
                        comment=p.get("comment"),
                        location_id=p.get("location_id"),
                        force=p.get("force", False),
                    )
                    result = self._service.update_status(dto)
                    return Response(status="ok", data=asdict(result))

                case "get_tracking":
                    events = self._service.get_tracking_history(uuid.UUID(p["order_id"]))
                    return Response(status="ok", data={
                        "events": [asdict(e) for e in events],
                    })

                case "calculate_route":
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
                            {
                                "id": l.id, "name": l.name,
                                "type": l.type.value if hasattr(l.type, "value") else l.type,
                                "address": l.address,
                            }
                            for l in locs
                        ],
                    })

                case _:
                    return Response(status="error", message=f"Неизвестный метод: {request.method}")

        except Exception as exc:
            return Response(status="error", message=str(exc))