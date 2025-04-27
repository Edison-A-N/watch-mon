from mcp.server.fastmcp import FastMCP

from watch_mon.core.monad import connect_to_monad, get_dapp_details, get_dapp_transactions

mcp = FastMCP("Monad Chain Protocol")


@mcp.tool()
async def get_contract_details(address: str) -> dict:
    """Get contract details by address"""
    try:
        w3 = await connect_to_monad()
        details = await get_dapp_details(w3, address)
        return details
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_dapp_transactions_count(address: str, days: int = 7) -> dict:
    """Get transaction count for a dApp in the last N days"""
    try:
        w3 = await connect_to_monad()
        count = await get_dapp_transactions(w3, address, days)
        return {"address": address, "transaction_count": count, "days": days}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_network_info() -> dict:
    """Get current network information"""
    try:
        w3 = await connect_to_monad()
        gas_price = w3.eth.gas_price
        return {
            "chain_id": w3.eth.chain_id,
            "block_number": w3.eth.block_number,
            "gas_price": {"wei": gas_price, "gwei": gas_price / 1e9, "tmon": gas_price / 1e18},
        }
    except Exception as e:
        return {"error": str(e)}
