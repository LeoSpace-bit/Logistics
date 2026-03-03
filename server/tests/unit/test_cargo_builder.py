"""Тесты паттерна Builder — CargoBuilder."""

import pytest

from logistics.domain.builder import CargoBuilder
from logistics.domain.exceptions import InvalidCargoError
from logistics.domain.models import Cargo


class TestCargoBuilderSetters:
    """Fluent-сеттеры возвращают self (цепочка вызовов)."""

    def test_set_weight_returns_self(self) -> None:
        builder = CargoBuilder()
        result = builder.set_weight(10.0)
        assert result is builder

    def test_set_dimensions_returns_self(self) -> None:
        builder = CargoBuilder()
        result = builder.set_dimensions(1.0, 0.5, 0.5)
        assert result is builder

    def test_set_description_returns_self(self) -> None:
        builder = CargoBuilder()
        result = builder.set_description("Тестовый груз")
        assert result is builder

    def test_mark_as_fragile_returns_self(self) -> None:
        builder = CargoBuilder()
        result = builder.mark_as_fragile()
        assert result is builder

    def test_mark_as_dangerous_returns_self(self) -> None:
        builder = CargoBuilder()
        result = builder.mark_as_dangerous()
        assert result is builder

    def test_require_temp_control_returns_self(self) -> None:
        builder = CargoBuilder()
        result = builder.require_temp_control()
        assert result is builder


class TestCargoBuilderBuild:
    """CargoBuilder.build() — сборка объекта Cargo."""

    def test_build_simple_cargo(self) -> None:
        """Сборка простого груза (вес + габариты)."""
        cargo = (
            CargoBuilder()
            .set_weight(12.5)
            .set_dimensions(0.5, 0.4, 0.6)
            .build()
        )
        assert isinstance(cargo, Cargo)
        assert cargo.weight_kg == 12.5
        assert cargo.volume_m3 == pytest.approx(0.5 * 0.4 * 0.6)

    def test_build_fragile_cargo(self) -> None:
        """Сборка хрупкого груза — флаг is_fragile = True."""
        cargo = (
            CargoBuilder()
            .set_weight(3.0)
            .set_dimensions(0.3, 0.3, 0.3)
            .mark_as_fragile()
            .build()
        )
        assert cargo.is_fragile is True
        assert cargo.is_dangerous is False

    def test_build_dangerous_cargo(self) -> None:
        """Сборка опасного груза — флаг is_dangerous = True."""
        cargo = (
            CargoBuilder()
            .set_weight(20.0)
            .set_dimensions(0.5, 0.5, 0.5)
            .mark_as_dangerous()
            .build()
        )
        assert cargo.is_dangerous is True

    def test_build_temp_control_cargo(self) -> None:
        """Сборка груза с температурным контролем."""
        cargo = (
            CargoBuilder()
            .set_weight(5.0)
            .set_dimensions(0.4, 0.4, 0.4)
            .require_temp_control()
            .build()
        )
        assert cargo.req_temp_control is True

    def test_build_with_description(self) -> None:
        """Description передаётся в Cargo."""
        cargo = (
            CargoBuilder()
            .set_weight(1.0)
            .set_dimensions(0.1, 0.1, 0.1)
            .set_description("Документы")
            .build()
        )
        assert cargo.description == "Документы"

    def test_build_all_flags(self) -> None:
        """Все флаги установлены одновременно."""
        cargo = (
            CargoBuilder()
            .set_weight(7.0)
            .set_dimensions(0.5, 0.5, 0.5)
            .mark_as_fragile()
            .mark_as_dangerous()
            .require_temp_control()
            .set_description("Особый груз")
            .build()
        )
        assert cargo.is_fragile is True
        assert cargo.is_dangerous is True
        assert cargo.req_temp_control is True

    def test_build_chain_order_independent(self) -> None:
        """Порядок вызовов сеттеров не влияет на результат."""
        cargo = (
            CargoBuilder()
            .mark_as_fragile()
            .set_description("Test")
            .set_dimensions(1.0, 1.0, 1.0)
            .set_weight(5.0)
            .build()
        )
        assert cargo.weight_kg == 5.0
        assert cargo.is_fragile is True


class TestCargoBuilderValidation:
    """Ошибки при некорректных данных."""

    def test_build_without_weight_raises(self) -> None:
        """Вес не задан → InvalidCargoError."""
        builder = CargoBuilder().set_dimensions(1.0, 1.0, 1.0)
        with pytest.raises(InvalidCargoError):
            builder.build()

    def test_build_without_dimensions_raises(self) -> None:
        """Габариты не заданы → InvalidCargoError."""
        builder = CargoBuilder().set_weight(5.0)
        with pytest.raises(InvalidCargoError):
            builder.build()

    def test_build_negative_weight_raises(self) -> None:
        """Отрицательный вес → InvalidCargoError."""
        builder = (
            CargoBuilder()
            .set_weight(-1.0)
            .set_dimensions(1.0, 1.0, 1.0)
        )
        with pytest.raises(InvalidCargoError):
            builder.build()

    def test_build_zero_dimension_raises(self) -> None:
        """Один из габаритов = 0 → InvalidCargoError."""
        builder = (
            CargoBuilder()
            .set_weight(5.0)
            .set_dimensions(1.0, 0.0, 1.0)
        )
        with pytest.raises(InvalidCargoError):
            builder.build()

    def test_build_empty_builder_raises(self) -> None:
        """Полностью пустой билдер → InvalidCargoError."""
        with pytest.raises(InvalidCargoError):
            CargoBuilder().build()


class TestCargoBuilderReset:
    """CargoBuilder.reset() — сброс состояния."""

    def test_reset_clears_state(self) -> None:
        """После reset() build() должен упасть — поля не заданы."""
        builder = (
            CargoBuilder()
            .set_weight(5.0)
            .set_dimensions(1.0, 1.0, 1.0)
            .reset()
        )
        with pytest.raises(InvalidCargoError):
            builder.build()

    def test_reset_returns_self(self) -> None:
        """reset() возвращает self для продолжения цепочки."""
        builder = CargoBuilder()
        result = builder.reset()
        assert result is builder