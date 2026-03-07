"""Паттерн Builder — все категории груза."""

from __future__ import annotations

from logistics.domain.exceptions import InvalidCargoError
from logistics.domain.models import Cargo


class CargoBuilder:

    def __init__(self) -> None:
        self._reset_fields()

    def _reset_fields(self) -> None:
        self._weight_kg: float | None = None
        self._height_m: float | None = None
        self._width_m: float | None = None
        self._length_m: float | None = None
        self._description: str = ""
        self._is_fragile: bool = False
        self._is_dangerous: bool = False
        self._is_liquid: bool = False
        self._is_perishable: bool = False
        self._is_crushable: bool = False
        self._req_temp_control: bool = False

    # ── Fluent API ────────────────────────────────────────────────────

    def set_weight(self, weight_kg: float) -> CargoBuilder:
        self._weight_kg = weight_kg
        return self

    def set_dimensions(
        self, height_m: float, width_m: float, length_m: float,
    ) -> CargoBuilder:
        self._height_m = height_m
        self._width_m = width_m
        self._length_m = length_m
        return self

    def set_description(self, description: str) -> CargoBuilder:
        self._description = description
        return self

    def mark_as_fragile(self) -> CargoBuilder:
        self._is_fragile = True
        return self

    def mark_as_dangerous(self) -> CargoBuilder:
        self._is_dangerous = True
        return self

    def mark_as_liquid(self) -> CargoBuilder:
        self._is_liquid = True
        return self

    def mark_as_perishable(self) -> CargoBuilder:
        self._is_perishable = True
        self._req_temp_control = True
        return self

    def mark_as_crushable(self) -> CargoBuilder:
        self._is_crushable = True
        return self

    def require_temp_control(self) -> CargoBuilder:
        self._req_temp_control = True
        return self

    # ── Сборка ────────────────────────────────────────────────────────

    def build(self) -> Cargo:
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
                f"Все габариты должны быть положительными: "
                f"h={self._height_m}, w={self._width_m}, l={self._length_m}",
            )

        volume = self._height_m * self._width_m * self._length_m

        return Cargo(
            weight_kg=self._weight_kg,
            volume_m3=volume,
            description=self._description,
            is_fragile=self._is_fragile,
            is_dangerous=self._is_dangerous,
            is_liquid=self._is_liquid,
            is_perishable=self._is_perishable,
            is_crushable=self._is_crushable,
            req_temp_control=self._req_temp_control,
        )

    def reset(self) -> CargoBuilder:
        self._reset_fields()
        return self