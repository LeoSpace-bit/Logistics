"""Паттерн Builder — пошаговое создание объекта Cargo."""

from __future__ import annotations

from logistics.domain.exceptions import InvalidCargoError
from logistics.domain.models import Cargo


class CargoBuilder:
    """Строитель груза.

    Пример использования::

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
        self._weight_kg = weight_kg
        return self

    def set_dimensions(
        self, height_m: float, width_m: float, length_m: float,
    ) -> CargoBuilder:
        """Установить габариты груза (метры)."""
        self._height_m = height_m
        self._width_m = width_m
        self._length_m = length_m
        return self

    def set_description(self, description: str) -> CargoBuilder:
        """Установить текстовое описание груза."""
        self._description = description
        return self

    def mark_as_fragile(self) -> CargoBuilder:
        """Отметить груз как хрупкий."""
        self._is_fragile = True
        return self

    def mark_as_dangerous(self) -> CargoBuilder:
        """Отметить груз как опасный."""
        self._is_dangerous = True
        return self

    def require_temp_control(self) -> CargoBuilder:
        """Указать, что требуется температурный контроль."""
        self._req_temp_control = True
        return self

    # ── Сборка ────────────────────────────────────────────────────────

    def build(self) -> Cargo:
        """Собрать и вернуть объект :class:`Cargo`.

        Returns:
            Готовый объект Cargo.

        Raises:
            InvalidCargoError: обязательные поля (вес, габариты) не заданы
                или имеют некорректные значения.
        """
        if self._weight_kg is None:
            raise InvalidCargoError("Вес груза не задан")
        if self._weight_kg <= 0:
            raise InvalidCargoError(
                f"Вес должен быть положительным, получено: {self._weight_kg}",
            )

        if (
            self._height_m is None
            or self._width_m is None
            or self._length_m is None
        ):
            raise InvalidCargoError("Габариты груза не заданы (нужны все три)")

        if self._height_m <= 0 or self._width_m <= 0 or self._length_m <= 0:
            raise InvalidCargoError(
                "Все габариты должны быть положительными: "
                f"h={self._height_m}, w={self._width_m}, l={self._length_m}",
            )

        volume = self._height_m * self._width_m * self._length_m

        return Cargo(
            weight_kg=self._weight_kg,
            volume_m3=volume,
            description=self._description,
            is_fragile=self._is_fragile,
            is_dangerous=self._is_dangerous,
            req_temp_control=self._req_temp_control,
        )

    def reset(self) -> CargoBuilder:
        """Сбросить все поля строителя в начальное состояние."""
        self._weight_kg = None
        self._height_m = None
        self._width_m = None
        self._length_m = None
        self._description = ""
        self._is_fragile = False
        self._is_dangerous = False
        self._req_temp_control = False
        return self