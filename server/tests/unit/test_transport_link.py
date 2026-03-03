"""Тесты TransportLink.can_transport() — проверка ограничений ребра."""

import pytest
from decimal import Decimal

from logistics.domain.enums import NodeType, TransportType
from logistics.domain.models import Cargo, Location, TransportLink


@pytest.fixture()
def restricted_link() -> TransportLink:
    """Ребро с жёсткими ограничениями: макс. 50 кг, 1 м³, без опасных."""
    src = Location(id=10, name="A", type=NodeType.WAREHOUSE, address="addr A")
    dst = Location(id=11, name="B", type=NodeType.WAREHOUSE, address="addr B")
    return TransportLink(
        id=100,
        source=src,
        target=dst,
        transport_type=TransportType.ROAD,
        distance_km=100,
        duration_min=60,
        cost_base=Decimal("500.00"),
        max_weight_kg=50.0,
        max_volume_m3=1.0,
        allows_dangerous=False,
        allows_fragile=True,
        allows_temp_control=False,
    )


@pytest.fixture()
def permissive_link() -> TransportLink:
    """Ребро без ограничений (все флаги разрешены, нет лимитов)."""
    src = Location(id=10, name="A", type=NodeType.HUB, address="addr A")
    dst = Location(id=11, name="B", type=NodeType.HUB, address="addr B")
    return TransportLink(
        id=101,
        source=src,
        target=dst,
        transport_type=TransportType.SEA,
        distance_km=5000,
        duration_min=7200,
        cost_base=Decimal("2000.00"),
        max_weight_kg=None,
        max_volume_m3=None,
        allows_dangerous=True,
        allows_fragile=True,
        allows_temp_control=True,
    )


class TestCanTransport:
    """TransportLink.can_transport(cargo)."""

    def test_normal_cargo_allowed(
        self, restricted_link: TransportLink,
    ) -> None:
        """Обычный груз в пределах лимитов → True."""
        cargo = Cargo(weight_kg=10.0, volume_m3=0.5)
        assert restricted_link.can_transport(cargo) is True

    def test_overweight_cargo_rejected(
        self, restricted_link: TransportLink,
    ) -> None:
        """Вес превышает max_weight_kg → False."""
        cargo = Cargo(weight_kg=100.0, volume_m3=0.5)
        assert restricted_link.can_transport(cargo) is False

    def test_overvolume_cargo_rejected(
        self, restricted_link: TransportLink,
    ) -> None:
        """Объём превышает max_volume_m3 → False."""
        cargo = Cargo(weight_kg=10.0, volume_m3=5.0)
        assert restricted_link.can_transport(cargo) is False

    def test_dangerous_cargo_on_restricted_link(
        self, restricted_link: TransportLink,
    ) -> None:
        """Опасный груз, ребро не разрешает → False."""
        cargo = Cargo(weight_kg=5.0, volume_m3=0.1, is_dangerous=True)
        assert restricted_link.can_transport(cargo) is False

    def test_dangerous_cargo_on_permissive_link(
        self, permissive_link: TransportLink,
    ) -> None:
        """Опасный груз, ребро разрешает → True."""
        cargo = Cargo(weight_kg=5.0, volume_m3=0.1, is_dangerous=True)
        assert permissive_link.can_transport(cargo) is True

    def test_fragile_cargo_allowed(
        self, restricted_link: TransportLink,
    ) -> None:
        """Хрупкий груз, ребро позволяет хрупкие → True."""
        cargo = Cargo(weight_kg=2.0, volume_m3=0.05, is_fragile=True)
        assert restricted_link.can_transport(cargo) is True

    def test_temp_control_on_restricted_link(
        self, restricted_link: TransportLink,
    ) -> None:
        """Требуется тем. контроль, ребро не поддерживает → False."""
        cargo = Cargo(weight_kg=5.0, volume_m3=0.1, req_temp_control=True)
        assert restricted_link.can_transport(cargo) is False

    def test_temp_control_on_permissive_link(
        self, permissive_link: TransportLink,
    ) -> None:
        """Требуется тем. контроль, ребро поддерживает → True."""
        cargo = Cargo(weight_kg=5.0, volume_m3=0.1, req_temp_control=True)
        assert permissive_link.can_transport(cargo) is True

    def test_exact_weight_limit(
        self, restricted_link: TransportLink,
    ) -> None:
        """Граничный случай: вес ровно = max_weight_kg → True."""
        cargo = Cargo(weight_kg=50.0, volume_m3=0.5)
        assert restricted_link.can_transport(cargo) is True

    def test_exact_volume_limit(
        self, restricted_link: TransportLink,
    ) -> None:
        """Граничный случай: объём ровно = max_volume_m3 → True."""
        cargo = Cargo(weight_kg=10.0, volume_m3=1.0)
        assert restricted_link.can_transport(cargo) is True

    def test_no_limits_any_cargo(
        self, permissive_link: TransportLink,
    ) -> None:
        """Ребро без лимитов — любой груз проходит."""
        cargo = Cargo(
            weight_kg=99999.0,
            volume_m3=9999.0,
            is_fragile=True,
            is_dangerous=True,
            req_temp_control=True,
        )
        assert permissive_link.can_transport(cargo) is True