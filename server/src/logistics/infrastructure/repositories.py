"""Репозитории: абстрактные интерфейсы + SQLAlchemy-реализации."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy.orm import Session

from logistics.domain.enums import NodeType, OrderStatus, TransportType, UserRole
from logistics.domain.models import (
    Cargo, Location, Order, Route, RouteSegment,
    TrackingEvent, TransportLink, User,
)
from logistics.infrastructure.orm import (
    CargoORM, LocationORM, OrderORM, OrderRouteSegmentORM,
    TrackingHistoryORM, TransportLinkORM, UserORM,
)


# ── Абстрактные интерфейсы ────────────────────────────────────────────

class IUserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: int) -> User | None: ...
    @abstractmethod
    def get_by_login(self, login: str) -> User | None: ...
    @abstractmethod
    def save(self, user: User) -> User: ...


class ILocationRepository(ABC):
    @abstractmethod
    def get_by_id(self, location_id: int) -> Location | None: ...
    @abstractmethod
    def get_all(self) -> list[Location]: ...


class ITransportLinkRepository(ABC):
    @abstractmethod
    def get_all(self) -> list[TransportLink]: ...
    @abstractmethod
    def get_by_origin(self, location_id: int) -> list[TransportLink]: ...


class IOrderRepository(ABC):
    @abstractmethod
    def get_by_id(self, order_id: uuid.UUID) -> Order | None: ...
    @abstractmethod
    def save(self, order: Order) -> Order: ...
    @abstractmethod
    def update_status(self, order_id: uuid.UUID, status: OrderStatus) -> bool: ...
    @abstractmethod
    def list_by_sender(self, sender_id: int) -> list[Order]: ...


class ICargoRepository(ABC):
    @abstractmethod
    def save(self, cargo: Cargo, order_id: uuid.UUID) -> Cargo: ...
    @abstractmethod
    def get_by_order_id(self, order_id: uuid.UUID) -> Cargo | None: ...


class ITrackingRepository(ABC):
    @abstractmethod
    def add_event(self, event: TrackingEvent) -> TrackingEvent: ...
    @abstractmethod
    def get_by_order_id(self, order_id: uuid.UUID) -> list[TrackingEvent]: ...


class IRouteSegmentRepository(ABC):
    @abstractmethod
    def save_segments(self, order_id: uuid.UUID, segments: list[RouteSegment]) -> None: ...
    @abstractmethod
    def get_by_order_id(self, order_id: uuid.UUID) -> list[RouteSegment]: ...


# ── Хелперы ORM → Domain ──────────────────────────────────────────────

def _orm_to_user(row: UserORM) -> User:
    return User(
        id=row.id, login=row.login, password_hash=row.password_hash,
        role=UserRole(row.role), full_name=row.full_name, created_at=row.created_at,
    )


def _orm_to_location(row: LocationORM) -> Location:
    try:
        loc_type = NodeType(row.type) if row.type else NodeType.WAREHOUSE
    except ValueError:
        loc_type = NodeType.WAREHOUSE
    return Location(
        id=row.id, name=row.name, type=loc_type,
        address=row.address, geo_lat=row.geo_lat, geo_lon=row.geo_lon,
    )


def _orm_to_link(row: TransportLinkORM, session: Session) -> TransportLink:
    from_loc = session.get(LocationORM, row.from_location_id)
    to_loc = session.get(LocationORM, row.to_location_id)
    return TransportLink(
        id=row.id,
        source=_orm_to_location(from_loc) if from_loc else Location(
            name="?", type=NodeType.WAREHOUSE, address="?", id=row.from_location_id,
        ),
        target=_orm_to_location(to_loc) if to_loc else Location(
            name="?", type=NodeType.WAREHOUSE, address="?", id=row.to_location_id,
        ),
        transport_type=TransportType(row.transport_type),
        distance_km=row.distance_km,
        duration_min=row.duration_min,
        cost_base=row.cost_base,
        max_weight_kg=row.max_weight_kg,
        max_volume_m3=row.max_volume_m3,
        allows_dangerous=row.allows_dangerous,
        allows_fragile=row.allows_fragile,
        allows_liquid=row.allows_liquid,
        allows_perishable=row.allows_perishable,
        allows_crushable=row.allows_crushable,
        allows_temp_control=row.allows_temp_control,
    )


def _orm_to_cargo(row: CargoORM) -> Cargo:
    return Cargo(
        id=row.id, weight_kg=row.weight_kg, volume_m3=row.volume_m3,
        description=row.description or "",
        is_fragile=row.is_fragile, is_dangerous=row.is_dangerous,
        is_liquid=row.is_liquid, is_perishable=row.is_perishable,
        is_crushable=row.is_crushable, req_temp_control=row.req_temp_control,
    )


# ── SQLAlchemy-реализации ─────────────────────────────────────────────

class SqlAlchemyUserRepository(IUserRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_by_id(self, user_id: int) -> User | None:
        row = self._s.get(UserORM, user_id)
        return _orm_to_user(row) if row else None

    def get_by_login(self, login: str) -> User | None:
        row = self._s.query(UserORM).filter(UserORM.login == login).first()
        return _orm_to_user(row) if row else None

    def save(self, user: User) -> User:
        orm = UserORM(
            login=user.login, password_hash=user.password_hash,
            full_name=user.full_name, role=user.role.value,
        )
        self._s.add(orm)
        self._s.flush()
        user.id = orm.id
        user.created_at = orm.created_at
        return user


class SqlAlchemyLocationRepository(ILocationRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_by_id(self, location_id: int) -> Location | None:
        row = self._s.get(LocationORM, location_id)
        return _orm_to_location(row) if row else None

    def get_all(self) -> list[Location]:
        return [_orm_to_location(r) for r in self._s.query(LocationORM).all()]


class SqlAlchemyTransportLinkRepository(ITransportLinkRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_all(self) -> list[TransportLink]:
        return [_orm_to_link(r, self._s) for r in self._s.query(TransportLinkORM).all()]

    def get_by_origin(self, location_id: int) -> list[TransportLink]:
        rows = self._s.query(TransportLinkORM).filter(
            TransportLinkORM.from_location_id == location_id,
        ).all()
        return [_orm_to_link(r, self._s) for r in rows]


class SqlAlchemyOrderRepository(IOrderRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def _to_domain(self, row: OrderORM) -> Order:
        sender = _orm_to_user(row.sender)
        receiver = _orm_to_user(row.receiver) if row.receiver else None
        origin = _orm_to_location(row.origin)
        destination = _orm_to_location(row.destination)
        cargo = _orm_to_cargo(row.cargo) if row.cargo else Cargo(weight_kg=0, volume_m3=0)
        return Order(
            id=row.id, sender=sender, receiver=receiver,
            origin=origin, destination=destination, cargo=cargo,
            status=OrderStatus(row.current_status),
            total_cost=row.total_cost, estimated_delivery=row.estimated_delivery,
            created_at=row.created_at,
        )

    def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        row = self._s.get(OrderORM, order_id)
        return self._to_domain(row) if row else None

    def save(self, order: Order) -> Order:
        orm = OrderORM(
            id=order.id, sender_id=order.sender.id,
            receiver_id=order.receiver.id if order.receiver else None,
            origin_location_id=order.origin.id, dest_location_id=order.destination.id,
            current_status=order.status.value,
            total_cost=order.total_cost, estimated_delivery=order.estimated_delivery,
        )
        self._s.add(orm)
        self._s.flush()
        return order

    def update_status(self, order_id: uuid.UUID, status: OrderStatus) -> bool:
        row = self._s.get(OrderORM, order_id)
        if row is None:
            return False
        row.current_status = status.value
        self._s.flush()
        return True

    def list_by_sender(self, sender_id: int) -> list[Order]:
        rows = self._s.query(OrderORM).filter(OrderORM.sender_id == sender_id).all()
        return [self._to_domain(r) for r in rows]


class SqlAlchemyCargoRepository(ICargoRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def save(self, cargo: Cargo, order_id: uuid.UUID) -> Cargo:
        orm = CargoORM(
            order_id=order_id,
            weight_kg=cargo.weight_kg, volume_m3=cargo.volume_m3,
            description=cargo.description,
            is_fragile=cargo.is_fragile, is_dangerous=cargo.is_dangerous,
            is_liquid=cargo.is_liquid, is_perishable=cargo.is_perishable,
            is_crushable=cargo.is_crushable, req_temp_control=cargo.req_temp_control,
        )
        self._s.add(orm)
        self._s.flush()
        cargo.id = orm.id
        return cargo

    def get_by_order_id(self, order_id: uuid.UUID) -> Cargo | None:
        row = self._s.query(CargoORM).filter(CargoORM.order_id == order_id).first()
        return _orm_to_cargo(row) if row else None


class SqlAlchemyTrackingRepository(ITrackingRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def add_event(self, event: TrackingEvent) -> TrackingEvent:
        orm = TrackingHistoryORM(
            order_id=event.order_id, location_id=event.location_id,
            status_code=event.status.value if isinstance(event.status, OrderStatus) else event.status,
            event_time=event.event_time or datetime.now(),
            comment=event.comment,
        )
        self._s.add(orm)
        self._s.flush()
        event.id = orm.id
        return event

    def get_by_order_id(self, order_id: uuid.UUID) -> list[TrackingEvent]:
        rows = (
            self._s.query(TrackingHistoryORM)
            .filter(TrackingHistoryORM.order_id == order_id)
            .order_by(TrackingHistoryORM.event_time)
            .all()
        )
        return [
            TrackingEvent(
                id=r.id, order_id=r.order_id,
                status=OrderStatus(r.status_code),
                event_time=r.event_time, location_id=r.location_id,
                comment=r.comment,
            )
            for r in rows
        ]


class SqlAlchemyRouteSegmentRepository(IRouteSegmentRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def save_segments(self, order_id: uuid.UUID, segments: list[RouteSegment]) -> None:
        for seg in segments:
            orm = OrderRouteSegmentORM(
                order_id=order_id, link_id=seg.link.id,
                step_sequence=seg.step_sequence, is_completed=seg.is_completed,
            )
            self._s.add(orm)
        self._s.flush()

    def get_by_order_id(self, order_id: uuid.UUID) -> list[RouteSegment]:
        rows = (
            self._s.query(OrderRouteSegmentORM)
            .filter(OrderRouteSegmentORM.order_id == order_id)
            .order_by(OrderRouteSegmentORM.step_sequence)
            .all()
        )
        segments = []
        for r in rows:
            link_orm = self._s.get(TransportLinkORM, r.link_id)
            if link_orm:
                link = _orm_to_link(link_orm, self._s)
                segments.append(RouteSegment(
                    link=link, step_sequence=r.step_sequence, is_completed=r.is_completed,
                ))
        return segments