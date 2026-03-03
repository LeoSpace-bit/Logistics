"""Паттерн Builder — пошаговое создание объекта Cargo."""

from __future__ import annotations

from src.logistics.domain.models import Cargo


class CargoBuilder:
    """Строитель груза.

    Пример (будущего) использования::

        cargo = (
            CargoBuilder()
            .set_weight(12.5)
            .set_dimensions(0.5, 0.4, 0.6)
            .mark_as_fragile()
            .build()
        )
    """

    def __init__(self) -> None:
        self._weight_kg: float | None = None
        self._height_m: float | None = None
        self._width_m: float | None = None
        self._length_m: float | None = None
        self._description: str = ""
        self._is_fragile: bool = False
        self._is_dangerous: bool = False
        self._req_temp_control: bool = False

    # ── Сеттеры (fluent API) ──────────────────────────────────────────

    def set_weight(self, weight_kg: float) -> CargoBuilder:
        """Установить вес груза (кг)."""
        raise NotImplementedError

    def set_dimensions(
        self, height_m: float, width_m: float, length_m: float,
    ) -> CargoBuilder:
        """Установить габариты груза (метры)."""
        raise NotImplementedError

    def set_description(self, description: str) -> CargoBuilder:
        """Установить текстовое описание груза."""
        raise NotImplementedError

    def mark_as_fragile(self) -> CargoBuilder:
        """Отметить груз как хрупкий."""
        raise NotImplementedError

    def mark_as_dangerous(self) -> CargoBuilder:
        """Отметить груз как опасный."""
        raise NotImplementedError

    def require_temp_control(self) -> CargoBuilder:
        """Указать, что требуется температурный контроль."""
        raise NotImplementedError

    # ── Сборка ────────────────────────────────────────────────────────

    def build(self) -> Cargo:
        """Собрать и вернуть объект :class:`Cargo`.

        Returns:
            Готовый объект Cargo.

        Raises:
            InvalidCargoError: обязательные поля (вес, габариты) не заданы
                или имеют некорректные значения.
        """
        raise NotImplementedError

    def reset(self) -> CargoBuilder:
        """Сбросить все поля строителя в начальное состояние."""
        raise NotImplementedError