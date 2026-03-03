"""Заполнение базы данных: 20 пунктов, транспортная сеть, пользователи."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from logistics.infrastructure.orm import (
    LocationORM,
    TransportLinkORM,
    UserORM,
)


# =====================================================================
#  Хелпер: двунаправленное ребро
# =====================================================================

def _bidir(
    from_id: int,
    to_id: int,
    tt: str,
    dist: int,
    dur: int,
    cost: str,
    *,
    max_w: float | None = None,
    max_v: float | None = None,
    dangerous: bool = False,
    fragile: bool = True,
    liquid: bool = True,
    perishable: bool = True,
    crushable: bool = True,
    temp_ctrl: bool = False,
) -> list[TransportLinkORM]:
    """Создать пару ORM-объектов для двунаправленного ребра."""
    common = dict(
        transport_type=tt,
        distance_km=dist,
        duration_min=dur,
        cost_base=Decimal(cost),
        max_weight_kg=max_w,
        max_volume_m3=max_v,
        allows_dangerous=dangerous,
        allows_fragile=fragile,
        allows_liquid=liquid,
        allows_perishable=perishable,
        allows_crushable=crushable,
        allows_temp_control=temp_ctrl,
    )
    return [
        TransportLinkORM(from_location_id=from_id, to_location_id=to_id, **common),
        TransportLinkORM(from_location_id=to_id, to_location_id=from_id, **common),
    ]


# =====================================================================
#  20 пунктов приёма-выдачи
# =====================================================================

LOCATIONS: list[dict] = [
    # id  name                          type            address                                     lat        lon
    dict(id=1,  name="Москва ЦС",             type="WAREHOUSE",     address="г. Москва, ул. Складская, 1",          geo_lat=55.7558, geo_lon=37.6173),
    dict(id=2,  name="Санкт-Петербург Хаб",    type="HUB",           address="г. СПб, Московский пр., 20",           geo_lat=59.9343, geo_lon=30.3351),
    dict(id=3,  name="Казань ПВЗ",             type="PICKUP_POINT",  address="г. Казань, ул. Баумана, 15",            geo_lat=55.7961, geo_lon=49.1064),
    dict(id=4,  name="Нижний Новгород ПВЗ",    type="PICKUP_POINT",  address="г. Нижний Новгород, ул. Большая Покровская, 5", geo_lat=56.2965, geo_lon=43.9361),
    dict(id=5,  name="Екатеринбург Хаб",       type="HUB",           address="г. Екатеринбург, ул. Малышева, 36",    geo_lat=56.8389, geo_lon=60.6057),
    dict(id=6,  name="Новосибирск Хаб",        type="HUB",           address="г. Новосибирск, Красный пр., 50",      geo_lat=55.0084, geo_lon=82.9357),
    dict(id=7,  name="Краснодар ПВЗ",          type="PICKUP_POINT",  address="г. Краснодар, ул. Красная, 10",         geo_lat=45.0355, geo_lon=38.9753),
    dict(id=8,  name="Ростов-на-Дону ПВЗ",     type="PICKUP_POINT",  address="г. Ростов-на-Дону, Большая Садовая, 40", geo_lat=47.2357, geo_lon=39.7015),
    dict(id=9,  name="Самара ПВЗ",             type="PICKUP_POINT",  address="г. Самара, ул. Ленинградская, 22",      geo_lat=53.1959, geo_lon=50.1002),
    dict(id=10, name="Волгоград ПВЗ",          type="PICKUP_POINT",  address="г. Волгоград, пр. Ленина, 18",          geo_lat=48.7080, geo_lon=44.5133),
    dict(id=11, name="Красноярск ПВЗ",         type="PICKUP_POINT",  address="г. Красноярск, пр. Мира, 80",           geo_lat=56.0153, geo_lon=92.8932),
    dict(id=12, name="Иркутск ПВЗ",            type="PICKUP_POINT",  address="г. Иркутск, ул. Карла Маркса, 30",      geo_lat=52.2978, geo_lon=104.2964),
    dict(id=13, name="Хабаровск ПВЗ",          type="PICKUP_POINT",  address="г. Хабаровск, ул. Муравьёва-Амурского, 5", geo_lat=48.4827, geo_lon=135.0838),
    dict(id=14, name="Владивосток Порт",        type="HUB",           address="г. Владивосток, ул. Светланская, 12",   geo_lat=43.1056, geo_lon=131.8735),
    dict(id=15, name="Калининград Порт",        type="HUB",           address="г. Калининград, Ленинский пр., 40",     geo_lat=54.7104, geo_lon=20.4522),
    dict(id=16, name="Мурманск ПВЗ",           type="PICKUP_POINT",  address="г. Мурманск, пр. Ленина, 55",           geo_lat=68.9585, geo_lon=33.0827),
    dict(id=17, name="Сочи ПВЗ",              type="PICKUP_POINT",  address="г. Сочи, ул. Навагинская, 7",           geo_lat=43.6028, geo_lon=39.7342),
    dict(id=18, name="Челябинск ПВЗ",          type="PICKUP_POINT",  address="г. Челябинск, пр. Ленина, 60",          geo_lat=55.1644, geo_lon=61.4368),
    dict(id=19, name="Воронеж ПВЗ",            type="PICKUP_POINT",  address="г. Воронеж, пр. Революции, 25",         geo_lat=51.6720, geo_lon=39.1843),
    dict(id=20, name="Пермь ПВЗ",             type="PICKUP_POINT",  address="г. Пермь, ул. Ленина, 30",              geo_lat=58.0105, geo_lon=56.2502),
]


def _build_links() -> list[TransportLinkORM]:
    """Все рёбра транспортной сети."""
    links: list[TransportLinkORM] = []

    # ── ROAD ──────────────────────────────────────────────────────────
    # Наземный: тяжёлый груз ОК, все категории, тем.контроль (рефрижератор)
    road_kw = dict(max_w=20_000, max_v=82, dangerous=True, fragile=True,
                   liquid=True, perishable=True, crushable=True, temp_ctrl=True)

    road = [
        #  from  to   dist  dur   cost
        (1,  2,  700,  600,  "4200"),    # Москва   ↔ СПб
        (1,  4,  420,  360,  "2900"),    # Москва   ↔ Н.Новгород
        (1,  19, 530,  420,  "3600"),    # Москва   ↔ Воронеж
        (4,  3,  400,  330,  "2700"),    # Н.Новгород ↔ Казань
        (3,  9,  350,  300,  "2400"),    # Казань   ↔ Самара
        (3,  20, 530,  450,  "3500"),    # Казань   ↔ Пермь
        (9,  10, 900,  660,  "5800"),    # Самара   ↔ Волгоград
        (19, 8,  560,  420,  "3800"),    # Воронеж  ↔ Ростов
        (8,  7,  270,  210,  "1800"),    # Ростов   ↔ Краснодар
        (7,  17, 300,  270,  "2200"),    # Краснодар ↔ Сочи
        (8,  10, 470,  390,  "3200"),    # Ростов   ↔ Волгоград
        (18, 5,  200,  180,  "1400"),    # Челябинск ↔ Екатеринбург
        (20, 5,  360,  300,  "2500"),    # Пермь    ↔ Екатеринбург
        (6,  11, 800,  660,  "5200"),    # Новосибирск ↔ Красноярск
        (13, 14, 760,  600,  "5000"),    # Хабаровск ↔ Владивосток
    ]
    for f, t, d, dur, c in road:
        links.extend(_bidir(f, t, "ROAD", d, dur, c, **road_kw))

    # ── RAIL ──────────────────────────────────────────────────────────
    # Ж/д: большой тоннаж, тем.контроль (рефсекция), все категории
    rail_kw = dict(max_w=60_000, max_v=120, dangerous=True, fragile=True,
                   liquid=True, perishable=True, crushable=True, temp_ctrl=True)

    rail = [
        (1,  2,   700,  240,  "2200"),   # Москва ↔ СПб  (Сапсан)
        (1,  4,   420,  240,  "1600"),   # Москва ↔ Н.Новгород
        (1,  3,   800,  720,  "2500"),   # Москва ↔ Казань
        (1,  8,  1100,  960,  "3200"),   # Москва ↔ Ростов
        (5,  6,  1500, 1440,  "4000"),   # Екатеринбург ↔ Новосибирск
        (6,  11,  800,  720,  "2600"),   # Новосибирск ↔ Красноярск
        (11, 12, 1100, 1080,  "3100"),   # Красноярск ↔ Иркутск
        (12, 13, 3500, 2880,  "7500"),   # Иркутск  ↔ Хабаровск
        (2,  16, 1400, 1440,  "4200"),   # СПб      ↔ Мурманск
        (3,  18,  560,  480,  "2000"),   # Казань   ↔ Челябинск
    ]
    for f, t, d, dur, c in rail:
        links.extend(_bidir(f, t, "RAIL", d, dur, c, **rail_kw))

    # ── AIR ───────────────────────────────────────────────────────────
    # Авиа: быстро, дорого. Жидкости и опасные — ЗАПРЕЩЕНЫ.
    air_kw = dict(max_w=5_000, max_v=20, dangerous=False, fragile=True,
                  liquid=False, perishable=True, crushable=True, temp_ctrl=True)

    air = [
        (1,  2,   650,   90,  "5200"),   # Москва ↔ СПб
        (1,  5,  1400,  150,  "8500"),   # Москва ↔ Екатеринбург
        (1,  6,  2800,  240, "13000"),   # Москва ↔ Новосибирск
        (1, 13,  6100,  480, "26000"),   # Москва ↔ Хабаровск
        (1, 14,  6400,  540, "29000"),   # Москва ↔ Владивосток
        (1, 15,  1000,  120,  "6200"),   # Москва ↔ Калининград
        (1, 17,  1600,  150,  "7500"),   # Москва ↔ Сочи
        (1,  7,  1200,  120,  "6800"),   # Москва ↔ Краснодар
        (1, 11,  3400,  270, "15500"),   # Москва ↔ Красноярск
        (6, 14,  4400,  360, "19000"),   # Новосибирск ↔ Владивосток
    ]
    for f, t, d, dur, c in air:
        links.extend(_bidir(f, t, "AIR", d, dur, c, **air_kw))

    # ── SEA ───────────────────────────────────────────────────────────
    # Морской: медленно, дёшево, огромный тоннаж.
    # Хрупкие, мнущиеся, скоропортящиеся — ЗАПРЕЩЕНЫ (качка, время).
    sea_kw = dict(max_w=200_000, max_v=500, dangerous=True, fragile=False,
                  liquid=True, perishable=False, crushable=False, temp_ctrl=True)

    sea = [
        (2,  15, 1100, 2880, "2800"),    # СПб  ↔ Калининград
        (2,  16, 2000, 4320, "3600"),    # СПб  ↔ Мурманск
        (14, 13,  800, 1440, "2200"),    # Владивосток ↔ Хабаровск
    ]
    for f, t, d, dur, c in sea:
        links.extend(_bidir(f, t, "SEA", d, dur, c, **sea_kw))

    return links


# =====================================================================
#  Главная функция сидирования
# =====================================================================

def seed_database(session: Session) -> None:
    """Заполнить БД начальными данными (идемпотентно)."""

    # Проверка — если уже есть данные, пропускаем
    if session.query(LocationORM).count() > 0:
        print("⏭  БД уже содержит данные — сидирование пропущено.")
        return

    # 1. Локации
    for loc in LOCATIONS:
        session.add(LocationORM(**loc))
    session.flush()
    print(f"✅ Создано {len(LOCATIONS)} локаций")

    # 2. Транспортные связи
    links = _build_links()
    session.add_all(links)
    session.flush()
    print(f"✅ Создано {len(links)} транспортных связей")

    # 3. Пользователи
    users = [
        UserORM(login="admin",   password_hash="admin_hash",   full_name="Администратор",  role="ADMIN"),
        UserORM(login="manager", password_hash="manager_hash", full_name="Менеджер Иванов", role="MANAGER"),
        UserORM(login="client1", password_hash="client_hash",  full_name="Клиент Петров",   role="CLIENT"),
        UserORM(login="client2", password_hash="client_hash",  full_name="Клиент Сидорова", role="CLIENT"),
    ]
    session.add_all(users)
    session.flush()
    print(f"✅ Создано {len(users)} пользователей")

    session.commit()
    print("✅ Сидирование завершено!")