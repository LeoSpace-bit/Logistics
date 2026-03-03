"""Точка входа: python -m logistics [serve|seed|demo]"""

from __future__ import annotations

import argparse
import sys
import time
from decimal import Decimal

from logistics.infrastructure.database import create_db_engine, create_session_factory, init_db
from logistics.infrastructure.seed import seed_database
from logistics.main import bootstrap, create_service


def cmd_serve(args: argparse.Namespace) -> None:
    """Запуск TCP-сервера."""
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
    """Только засеять БД."""
    engine = create_db_engine(args.db)
    init_db(engine)
    session = create_session_factory(engine)()
    seed_database(session)
    session.close()


def cmd_demo(args: argparse.Namespace) -> None:
    """Демонстрация работы сервиса без TCP — прямой вызов."""
    engine = create_db_engine(args.db)
    init_db(engine)
    session = create_session_factory(engine)()
    seed_database(session)

    service = create_service(session)
    service.build_graph()

    print("=" * 70)
    print("       ДЕМОНСТРАЦИЯ ЛОГИСТИЧЕСКОГО СЕРВИСА")
    print("=" * 70)

    # 1. Список локаций
    locations = service._location_repo.get_all()
    print(f"\n📍 Доступно {len(locations)} пунктов:")
    for loc in locations:
        t = loc.type.value if hasattr(loc.type, 'value') else loc.type
        print(f"   [{loc.id:>2}] {loc.name:<30s} ({t})")

    # 2. Расчёт маршрута: обычный груз, дешёвый
    print("\n" + "-" * 70)
    print("📦 Расчёт маршрута: Москва → Владивосток (обычный груз, дешёвый)")
    r1 = service.calculate_route(
        origin_id=1, dest_id=14, weight_kg=15, volume_m3=0.1,
        strategy_name="cheapest",
    )
    print(f"   Стоимость: {r1.total_cost} ₽  |  Время: {r1.total_time_min} мин ({r1.total_time_min // 60}ч)")
    for seg in r1.segments:
        print(f"   → {seg.from_location} → {seg.to_location}  [{seg.transport_type}]  "
              f"{seg.duration_min} мин, {seg.cost} ₽")

    # 3. Тот же маршрут — быстрый
    print(f"\n✈️  Тот же маршрут — быстрый:")
    r2 = service.calculate_route(
        origin_id=1, dest_id=14, weight_kg=15, volume_m3=0.1,
        strategy_name="fastest",
    )
    print(f"   Стоимость: {r2.total_cost} ₽  |  Время: {r2.total_time_min} мин ({r2.total_time_min // 60}ч)")
    for seg in r2.segments:
        print(f"   → {seg.from_location} → {seg.to_location}  [{seg.transport_type}]  "
              f"{seg.duration_min} мин, {seg.cost} ₽")

    # 4. Опасный жидкий груз (нельзя авиа!)
    print("\n" + "-" * 70)
    print("⚠️  Маршрут для ОПАСНОГО ЖИДКОГО груза: Москва → Калининград")
    try:
        r3 = service.calculate_route(
            origin_id=1, dest_id=15, weight_kg=50, volume_m3=0.3,
            is_dangerous=True, is_liquid=True, strategy_name="cheapest",
        )
        print(f"   Стоимость: {r3.total_cost} ₽  |  Время: {r3.total_time_min} мин")
        for seg in r3.segments:
            print(f"   → {seg.from_location} → {seg.to_location}  [{seg.transport_type}]")
    except Exception as e:
        print(f"   ❌ {e}")

    # 5. Хрупкий скоропортящийся груз (нельзя морем!)
    print(f"\n🥚 Маршрут для ХРУПКОГО СКОРОПОРТЯЩЕГОСЯ груза: СПб → Мурманск")
    try:
        r4 = service.calculate_route(
            origin_id=2, dest_id=16, weight_kg=5, volume_m3=0.05,
            is_fragile=True, is_perishable=True, req_temp_control=True,
            strategy_name="fastest",
        )
        print(f"   Стоимость: {r4.total_cost} ₽  |  Время: {r4.total_time_min} мин")
        for seg in r4.segments:
            print(f"   → {seg.from_location} → {seg.to_location}  [{seg.transport_type}]")
    except Exception as e:
        print(f"   ❌ {e}")

    # 6. Создание заказа
    print("\n" + "-" * 70)
    print("📋 Создание заказа: клиент client1, Москва → Казань, 3 кг книги")
    from logistics.service.dto import CargoCreateDTO, OrderCreateDTO
    order_dto = OrderCreateDTO(
        sender_id=3,  # client1
        origin_location_id=1,
        dest_location_id=3,
        cargo=CargoCreateDTO(
            weight_kg=3.0, height_m=0.3, width_m=0.2, length_m=0.15,
            description="Книги",
        ),
        strategy="cheapest",
    )
    order = service.create_order(order_dto)
    print(f"   ✅ Заказ {order.id}")
    print(f"   Статус: {order.status}  |  Стоимость: {order.total_cost} ₽")

    # 7. Обновление статусов
    print(f"\n🔄 Обновление статусов:")
    from logistics.service.dto import StatusUpdateDTO
    for new_st in ["PROCESSING", "WAITING_DROP_OFF", "IN_TRANSIT", "ARRIVED", "DELIVERED"]:
        res = service.update_status(StatusUpdateDTO(
            order_id=order.id, new_status=new_st, comment=f"Переход в {new_st}",
        ))
        print(f"   → {res.status}")

    # 8. История отслеживания
    print(f"\n📜 История отслеживания:")
    history = service.get_tracking_history(order.id)
    for ev in history:
        print(f"   [{ev.event_time.strftime('%H:%M:%S')}] {ev.status}  {ev.comment or ''}")

    print("\n" + "=" * 70)
    print("       ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 70)

    session.close()


def main() -> None:
    parser = argparse.ArgumentParser(prog="logistics", description="Логистический сервис")
    parser.add_argument("--db", default="sqlite:///logistics.db", help="URL базы данных")

    sub = parser.add_subparsers(dest="command")

    serve_p = sub.add_parser("serve", help="Запустить TCP-сервер")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=9090)

    sub.add_parser("seed", help="Заполнить БД начальными данными")
    sub.add_parser("demo", help="Демонстрация работы (без TCP)")

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