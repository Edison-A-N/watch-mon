# Watch Mon

A MCP tool for monitoring and analyzing dApps on Monad testnet.

## Features

- Monad Chain Protocol monitoring
- Real-time dApp analysis
- Web3 integration

## Installation

1. Clone the repository:

2. Create and activate a virtual environment:

3. Install dependencies (choose one method):

Using pip:
```bash
pip install .
# For development with test dependencies:
pip install ".[test]"
```

Using uv (faster):
```bash
uv sync
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Usage


The MCP server configuration should be specified in your MCP config file with the following format:

```json
{
    "mcpServers": {
        "monad_chain_tracing": {
            "command": "/path/to/your/python",
            "args": [
                "/path/to/watch-mon/watch_mon/cli.py",
                "serve"
            ]
        }
    }
}
```

Replace the paths with your actual Python interpreter and project paths.

### Running Tests

```bash
pytest
```
