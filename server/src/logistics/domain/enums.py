"""Перечисления доменного слоя."""

from enum import Enum


class UserRole(str, Enum):
    """Роль пользователя в системе."""
    CLIENT = "CLIENT"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"


class OrderStatus(str, Enum):
    """Статус заказа (жизненный цикл посылки)."""
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    WAITING_DROP_OFF = "WAITING_DROP_OFF"
    IN_TRANSIT = "IN_TRANSIT"
    ARRIVED = "ARRIVED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class TransportType(str, Enum):
    """Тип транспорта (тип ребра графа)."""
    AIR = "AIR"
    RAIL = "RAIL"
    ROAD = "ROAD"
    SEA = "SEA"


class NodeType(str, Enum):
    """Тип узла транспортной сети (тип вершины графа)."""
    WAREHOUSE = "WAREHOUSE"
    HUB = "HUB"
    AIRPORT = "AIRPORT"
    PICKUP_POINT = "PICKUP_POINT"