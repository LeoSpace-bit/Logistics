"""Тесты модели Cargo — валидация груза."""

import pytest

from logistics.domain.exceptions import InvalidCargoError
from logistics.domain.models import Cargo


class TestCargoValidate:
    """Cargo.validate() — проверка корректности параметров."""

    def test_valid_cargo(self, sample_cargo: Cargo) -> None:
        """Корректный груз — validate возвращает True."""
        assert sample_cargo.validate() is True

    def test_zero_weight_raises(self) -> None:
        """Вес = 0 → InvalidCargoError."""
        cargo = Cargo(weight_kg=0.0, volume_m3=0.1)
        with pytest.raises(InvalidCargoError):
            cargo.validate()

    def test_negative_weight_raises(self) -> None:
        """Отрицательный вес → InvalidCargoError."""
        cargo = Cargo(weight_kg=-5.0, volume_m3=0.1)
        with pytest.raises(InvalidCargoError):
            cargo.validate()

    def test_zero_volume_raises(self) -> None:
        """Объём = 0 → InvalidCargoError."""
        cargo = Cargo(weight_kg=1.0, volume_m3=0.0)
        with pytest.raises(InvalidCargoError):
            cargo.validate()

    def test_negative_volume_raises(self) -> None:
        """Отрицательный объём → InvalidCargoError."""
        cargo = Cargo(weight_kg=1.0, volume_m3=-0.5)
        with pytest.raises(InvalidCargoError):
            cargo.validate()

    def test_fragile_cargo_valid(self, fragile_cargo: Cargo) -> None:
        """Хрупкий груз с корректными параметрами — True."""
        assert fragile_cargo.validate() is True

    def test_dangerous_cargo_valid(self, dangerous_cargo: Cargo) -> None:
        """Опасный груз с корректными параметрами — True."""
        assert dangerous_cargo.validate() is True

    def test_very_small_weight_valid(self) -> None:
        """Граничный случай: очень маленький, но положительный вес."""
        cargo = Cargo(weight_kg=0.001, volume_m3=0.001)
        assert cargo.validate() is True

    def test_very_large_weight_valid(self) -> None:
        """Граничный случай: очень большой вес."""
        cargo = Cargo(weight_kg=99999.0, volume_m3=500.0)
        assert cargo.validate() is True