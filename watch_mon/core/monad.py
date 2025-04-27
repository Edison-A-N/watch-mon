import asyncio
import random
from collections import defaultdict

import aiohttp
from web3 import Web3
from tqdm import tqdm

from watch_mon.config import config

# Global session
session = None


async def with_concurrency(func, *args, **kwargs):
    """Utility function to control concurrency of async operations"""
    semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_REQUESTS)

    async def wrapped(*args, **kwargs):
        async with semaphore:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                print(f"Error in concurrent operation: {str(e)}")
                raise

    return wrapped


async def get_session():
    """Get or create global session with proxy settings"""
    global session
    if session is None:
        proxy = config.HTTP_PROXY or config.HTTPS_PROXY
        session = aiohttp.ClientSession(proxy=proxy)
    return session


async def close_session():
    """Close the global session"""
    global session
    if session:
        await session.close()
        session = None


async def connect_to_monad():
    """Connect to Monad testnet"""
    proxy = config.HTTP_PROXY or config.HTTPS_PROXY
    if proxy:
        w3 = Web3(
            Web3.HTTPProvider(
                config.MONAD_TESTNET_RPC,
                request_kwargs={"proxies": {"http": proxy, "https": proxy}},
            )
        )
    else:
        w3 = Web3(Web3.HTTPProvider(config.MONAD_TESTNET_RPC))
    if not w3.is_connected():
        raise Exception("Failed to connect to Monad testnet")
    return w3


async def get_block_async(session, block_number, max_retries=3, base_delay=1):
    """Fetch a single block asynchronously with retry logic"""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": [hex(block_number), True],
        "id": 1,
    }

    for attempt in range(max_retries):
        try:
            async with session.post(config.MONAD_TESTNET_RPC, json=payload) as response:
                if response.status == 429:  # Rate limit hit
                    if attempt < max_retries - 1:
                        delay = base_delay * (2**attempt) + random.uniform(0, 1)
                        print(f"Rate limited, waiting {delay:.2f}s before retry...")
                        await asyncio.sleep(delay)
                        continue

                if response.status != 200:
                    error_text = await response.text()
                    print(f"HTTP {response.status} Error for block {block_number}:")
                    print(f"Response headers: {response.headers}")
                    print(f"Response body: {error_text}")
                    raise Exception(f"HTTP {response.status}: {error_text}")
                return await response.json()
        except aiohttp.ClientError as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt) + random.uniform(0, 1)
                print(f"Network error for block {block_number}, retrying in {delay:.2f}s: {str(e)}")
                await asyncio.sleep(delay)
                continue
            print(f"Network error for block {block_number}: {str(e)}")
            raise


async def get_dapp_transactions(w3, dapp_address, days=7):
    """Get transaction count for a dApp in the last N days"""
    current_block = w3.eth.block_number
    blocks_per_day = 86400
    start_block = current_block - (blocks_per_day * days)

    # Get transaction count
    tx_count = 0
    session = await get_session()

    get_block_with_concurrency = await with_concurrency(get_block_async)
    tasks = []
    for block_number in range(start_block, current_block + 1):
        tasks.append(get_block_with_concurrency(session, block_number))

    responses = await asyncio.gather(*tasks)
    if config.SHOW_PROGRESS_BAR:
        responses = tqdm(responses, desc="Processing blocks")
    for response in responses:
        if "result" in response and response["result"]:
            block = response["result"]
            for tx in block["transactions"]:
                if tx["to"] and tx["to"].lower() == dapp_address.lower():
                    tx_count += 1

    return tx_count


async def discover_dapps(w3, days=7):
    """Discover dApps by scanning recent blocks"""
    current_block = w3.eth.block_number
    blocks_per_day = 86400
    start_block = current_block - (blocks_per_day * days)

    # Track contract addresses and their transaction counts
    dapp_activity = defaultdict(int)

    print(f"Scanning blocks from {start_block} to {current_block}...")
    session = await get_session()

    get_block_with_concurrency = await with_concurrency(get_block_async)
    tasks = []
    for block_number in range(start_block, start_block + 100):
        tasks.append(get_block_with_concurrency(session, block_number))

    responses = await asyncio.gather(*tasks)
    if config.SHOW_PROGRESS_BAR:
        responses = tqdm(responses, desc="Processing blocks")
    for response in responses:
        if "result" in response and response["result"]:
            block = response["result"]
            for tx in block["transactions"]:
                if tx["to"]:  # Only count contract interactions
                    dapp_activity[tx["to"].lower()] += 1

    # Convert to list and sort by transaction count
    dapp_list = [{"address": addr, "transaction_count": count} for addr, count in dapp_activity.items()]
    return sorted(dapp_list, key=lambda x: x["transaction_count"], reverse=True)


async def get_top_dapps(days=7):
    """Get top 10 active dApps on Monad testnet"""
    w3 = await connect_to_monad()
    dapp_activity = await discover_dapps(w3, days)
    return dapp_activity[:10]


async def get_dapp_details(w3, dapp_address):
    """Get detailed information about a dApp by its address"""
    try:
        # Convert to checksum address
        dapp_address = w3.to_checksum_address(dapp_address)

        # Basic info
        info = {
            "address": dapp_address,
            "name": None,
            "description": None,
            "contract_code": None,
            "is_verified": False,
            "creator": None,
            "creation_block": None,
            "creation_tx": None,
            "total_transactions": 0,
            "last_active": None,
            "interfaces": [],
        }

        # Get contract code
        try:
            code = w3.eth.get_code(dapp_address)
            info["contract_code"] = code.hex() if code else None
            info["is_verified"] = bool(code)
        except Exception as e:
            print(f"Error getting contract code: {str(e)}")

        # Get contract creation info
        try:
            # Get the first transaction to this address
            current_block = w3.eth.block_number
            block_range = range(max(0, current_block - 1000000), current_block + 1)
            if config.SHOW_PROGRESS_BAR:
                block_range = tqdm(block_range, desc="Finding creation block")
            for block_number in block_range:
                block = w3.eth.get_block(block_number, full_transactions=True)
                for tx in block.transactions:
                    if tx.to and tx.to.lower() == dapp_address.lower():
                        info["creation_block"] = block_number
                        info["creation_tx"] = tx.hash.hex()
                        info["creator"] = tx["from"]
                        break
                if info["creation_block"]:
                    break
        except Exception as e:
            print(f"Error getting creation info: {str(e)}")

        # Get transaction count
        try:
            info["total_transactions"] = w3.eth.get_transaction_count(dapp_address)
        except Exception as e:
            print(f"Error getting transaction count: {str(e)}")

        # Get last active block
        try:
            current_block = w3.eth.block_number
            block_range = range(current_block, max(0, current_block - 1000), -1)
            if config.SHOW_PROGRESS_BAR:
                block_range = tqdm(block_range, desc="Finding last active block")
            for block_number in block_range:
                block = w3.eth.get_block(block_number, full_transactions=True)
                for tx in block.transactions:
                    if tx.to and tx.to.lower() == dapp_address.lower():
                        info["last_active"] = block_number
                        break
                if info["last_active"]:
                    break
        except Exception as e:
            print(f"Error getting last active block: {str(e)}")

        # Try to detect interfaces
        try:
            # ERC165 interface detection
            if info["contract_code"]:
                # Common interface IDs
                interfaces = {
                    "ERC721": "0x80ac58cd",
                    "ERC1155": "0xd9b67a26",
                    "ERC20": "0x36372b07",
                    "ERC777": "0xe58e113c",
                    "ERC165": "0x01ffc9a7",
                }

                # Create contract instance for interface detection
                contract = w3.eth.contract(address=dapp_address, abi=[])

                interface_items = interfaces.items()
                if config.SHOW_PROGRESS_BAR:
                    interface_items = tqdm(interface_items, desc="Detecting interfaces")
                for interface_name, interface_id in interface_items:
                    try:
                        # Try to call supportsInterface
                        result = contract.functions.supportsInterface(interface_id).call()
                        if result:
                            info["interfaces"].append(interface_name)
                    except Exception:
                        continue
        except Exception as e:
            print(f"Error detecting interfaces: {str(e)}")

        return info

    except Exception as e:
        print(f"Error getting dApp details: {str(e)}")
        return None
