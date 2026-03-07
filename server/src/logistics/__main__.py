"""Точка входа: python -m logistics [serve|seed|demo]"""

from __future__ import annotations

import argparse
import logging
import sys
import time

from logistics.infrastructure.database import create_db_engine, create_session_factory, init_db
from logistics.infrastructure.seed import seed_database
from logistics.main import bootstrap, create_service


def _setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s  %(name)-24s  %(levelname)-7s  %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_serve(args: argparse.Namespace) -> None:
    _setup_logging(args.log_level)
    server, session = bootstrap(db_url=args.db, host=args.host, port=args.port)
    server.start()
    print(f"🚀 Сервер запущен на {args.host}:{args.port}")
    print("   Нажмите Ctrl+C для остановки.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
        session.close()
        print("\n🛑 Сервер остановлен.")


def cmd_seed(args: argparse.Namespace) -> None:
    _setup_logging()
    engine = create_db_engine(args.db)
    init_db(engine)
    session = create_session_factory(engine)()
    seed_database(session)
    session.close()


def cmd_demo(args: argparse.Namespace) -> None:
    _setup_logging()
    engine = create_db_engine(args.db)
    init_db(engine)
    session = create_session_factory(engine)()
    seed_database(session)

    service = create_service(session)
    service.build_graph()

    print("=" * 70)
    print("       ДЕМОНСТРАЦИЯ ЛОГИСТИЧЕСКОГО СЕРВИСА")
    print("=" * 70)

    locations = service._location_repo.get_all()
    print(f"\n📍 Доступно {len(locations)} пунктов:")
    for loc in locations:
        t = loc.type.value if hasattr(loc.type, "value") else loc.type
        print(f"   [{loc.id:>2}] {loc.name:<30s} ({t})")

    print("\n" + "-" * 70)
    print("📦 Расчёт маршрута: Москва → Владивосток (дешёвый)")
    r1 = service.calculate_route(origin_id=1, dest_id=14, weight_kg=15, volume_m3=0.1, strategy_name="cheapest")
    print(f"   Стоимость: {r1.total_cost} ₽  |  Время: {r1.total_time_min} мин")
    for seg in r1.segments:
        print(f"   → {seg.from_location} → {seg.to_location}  [{seg.transport_type}]  {seg.duration_min} мин, {seg.cost} ₽")

    print(f"\n✈️  Быстрый:")
    r2 = service.calculate_route(origin_id=1, dest_id=14, weight_kg=15, volume_m3=0.1, strategy_name="fastest")
    print(f"   Стоимость: {r2.total_cost} ₽  |  Время: {r2.total_time_min} мин")
    for seg in r2.segments:
        print(f"   → {seg.from_location} → {seg.to_location}  [{seg.transport_type}]  {seg.duration_min} мин, {seg.cost} ₽")

    print("\n" + "-" * 70)
    print("📋 Создание заказа: client1, Москва → Казань")
    from logistics.service.dto import CargoCreateDTO, OrderCreateDTO, StatusUpdateDTO
    order = service.create_order(OrderCreateDTO(
        sender_id=3, origin_location_id=1, dest_location_id=3,
        cargo=CargoCreateDTO(weight_kg=3.0, height_m=0.3, width_m=0.2, length_m=0.15, description="Книги"),
        strategy="cheapest",
    ))
    print(f"   ✅ Заказ {order.id}  |  Стоимость: {order.total_cost} ₽")

    print(f"\n🔄 Обновление статусов:")
    for st in ["PROCESSING", "WAITING_DROP_OFF", "IN_TRANSIT", "ARRIVED", "DELIVERED"]:
        res = service.update_status(StatusUpdateDTO(order_id=order.id, new_status=st, comment=f"→ {st}"))
        print(f"   → {res.status}")

    print(f"\n📜 История:")
    for ev in service.get_tracking_history(order.id):
        print(f"   [{ev.event_time.strftime('%H:%M:%S')}] {ev.status}  {ev.comment or ''}")

    print("\n" + "=" * 70)
    session.close()


def main() -> None:
    parser = argparse.ArgumentParser(prog="logistics")
    parser.add_argument("--db", default="sqlite:///logistics.db")

    sub = parser.add_subparsers(dest="command")

    serve_p = sub.add_parser("serve")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=9090)
    serve_p.add_argument("--log-level", default="INFO")

    sub.add_parser("seed")
    sub.add_parser("demo")

    args = parser.parse_args()

    match args.command:
        case "serve":
            cmd_serve(args)
        case "seed":
            cmd_seed(args)
        case "demo":
            cmd_demo(args)
        case _:
            parser.print_help()
            sys.exit(1)


if __name__ == "__main__":
    main()