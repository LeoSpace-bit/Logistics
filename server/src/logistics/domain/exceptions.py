"""Исключения доменного слоя."""


class DomainError(Exception):
    """Базовое доменное исключение."""


class InvalidCargoError(DomainError):
    """Невалидные параметры груза."""


class RouteNotFoundError(DomainError):
    """Маршрут не найден."""


class OrderNotFoundError(DomainError):
    """Заказ не существует."""


class InvalidStatusTransitionError(DomainError):
    """Недопустимый переход статуса."""


class CargoRestrictionError(DomainError):
    """Груз не может быть перевезён по данному ребру."""


class AuthenticationError(DomainError):
    """Ошибка аутентификации."""