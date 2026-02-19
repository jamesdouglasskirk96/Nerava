import pytest

from app.models.merchant_pos_credentials import MerchantPOSCredentials
from app.services.pos_adapter import (
    ManualPOSAdapter,
    ToastPOSAdapter,
    SquarePOSAdapter,
    POSOrder,
    get_pos_adapter,
)


@pytest.mark.asyncio
async def test_manual_lookup_order_returns_pos_order():
    adapter = ManualPOSAdapter()
    order = await adapter.lookup_order("A-100")
    assert isinstance(order, POSOrder)
    assert order.order_number == "A-100"


@pytest.mark.asyncio
async def test_manual_get_order_status_returns_unknown():
    adapter = ManualPOSAdapter()
    status = await adapter.get_order_status("A-100")
    assert status == "unknown"


@pytest.mark.asyncio
async def test_manual_get_order_total_returns_none():
    adapter = ManualPOSAdapter()
    total = await adapter.get_order_total("A-100")
    assert total is None


@pytest.mark.asyncio
async def test_toast_lookup_order_returns_none():
    adapter = ToastPOSAdapter(restaurant_guid="r1", access_token="token")
    order = await adapter.lookup_order("A-100")
    assert order is None


@pytest.mark.asyncio
async def test_square_lookup_order_returns_none():
    adapter = SquarePOSAdapter(location_id="loc", access_token="token")
    order = await adapter.lookup_order("A-100")
    assert order is None


def test_get_pos_adapter_factory_types():
    toast_creds = MerchantPOSCredentials(merchant_id="m1", pos_type="toast", restaurant_guid="r1")
    square_creds = MerchantPOSCredentials(merchant_id="m2", pos_type="square")

    assert isinstance(get_pos_adapter("toast", toast_creds), ToastPOSAdapter)
    assert isinstance(get_pos_adapter("square", square_creds), SquarePOSAdapter)
    assert isinstance(get_pos_adapter("none", None), ManualPOSAdapter)
