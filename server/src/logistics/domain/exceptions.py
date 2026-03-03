"""Исключения доменного слоя."""


class DomainError(Exception):
    """Базовое доменное исключение."""


class InvalidCargoError(DomainError):
    """Невалидные параметры груза (отрицательный вес, нулевой объём и т.д.)."""


class RouteNotFoundError(DomainError):
    """Маршрут между заданными точками не найден."""


class OrderNotFoundError(DomainError):
    """Заказ с указанным ID не существует."""


class InvalidStatusTransitionError(DomainError):
    """Недопустимый переход статуса (например, DELIVERED → CREATED)."""


class CargoRestrictionError(DomainError):
    """Груз не может быть перевезён по данному ребру (превышение веса и пр.)."""