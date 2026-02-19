import pytest

from app.models.arrival_session import (
    ACTIVE_STATUSES,
    TERMINAL_STATUSES,
    VALID_TRANSITIONS,
    _generate_reply_code,
)
from app.services.pos_adapter import ManualPOSAdapter, get_pos_adapter, POSOrder


def test_generate_reply_code_is_4_digits():
    code = _generate_reply_code()
    assert isinstance(code, str)
    assert len(code) == 4
    assert code.isdigit()


def test_generate_reply_code_uniqueness():
    codes = {_generate_reply_code() for _ in range(100)}
    assert len(codes) > 90


def test_active_and_terminal_statuses_are_disjoint():
    assert ACTIVE_STATUSES.isdisjoint(TERMINAL_STATUSES)


def test_all_active_statuses_have_transitions():
    for status in ACTIVE_STATUSES:
        assert status in VALID_TRANSITIONS


@pytest.mark.asyncio
async def test_manual_pos_lookup_returns_unknown():
    adapter = ManualPOSAdapter()
    order = await adapter.lookup_order("1234")
    assert isinstance(order, POSOrder)
    assert order.status == "unknown"


@pytest.mark.asyncio
async def test_manual_pos_get_order_total_returns_none():
    adapter = ManualPOSAdapter()
    total = await adapter.get_order_total("1234")
    assert total is None


def test_get_pos_adapter_none_returns_manual():
    adapter = get_pos_adapter("none", None)
    assert isinstance(adapter, ManualPOSAdapter)


def test_get_pos_adapter_toast_without_credentials_returns_manual():
    adapter = get_pos_adapter("toast", None)
    assert isinstance(adapter, ManualPOSAdapter)


def test_valid_transitions_include_canceled_for_active_statuses():
    for status in ACTIVE_STATUSES:
        assert "canceled" in VALID_TRANSITIONS[status]


def test_valid_transitions_include_expired_for_active_statuses():
    for status in ACTIVE_STATUSES:
        assert "expired" in VALID_TRANSITIONS[status]
