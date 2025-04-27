
import pytest

from watch_mon.core.monad import (
    close_session,
    connect_to_monad,
    get_dapp_details,
    get_dapp_transactions,
    get_top_dapps,
)


@pytest.mark.asyncio
async def test_connect_to_monad():
    """Test connection to Monad testnet"""
    w3 = await connect_to_monad()
    assert w3.is_connected()
    await close_session()


@pytest.mark.asyncio
async def test_get_top_dapps():
    """Test getting top dApps"""
    dapps = await get_top_dapps(days=1)
    assert isinstance(dapps, list)
    if dapps:  # If any dApps are found
        assert "address" in dapps[0]
        assert "transaction_count" in dapps[0]
    await close_session()


@pytest.mark.asyncio
async def test_get_dapp_details():
    """Test getting dApp details"""
    # Use a known test address
    test_address = "0x8462c247356d7deb7e26160dbfab16b351eef242"
    w3 = await connect_to_monad()
    details = await get_dapp_details(w3, test_address)
    assert details is not None
    assert "address" in details
    assert "is_verified" in details
    await close_session()


@pytest.mark.asyncio
async def test_get_dapp_transactions():
    """Test getting dApp transactions"""
    # Use a known test address
    test_address = "0x8462c247356d7deb7e26160dbfab16b351eef242"
    w3 = await connect_to_monad()
    count = await get_dapp_transactions(w3, test_address, days=1)
    assert isinstance(count, int)
    assert count >= 0
    await close_session()
