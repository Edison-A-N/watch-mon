from typing import Optional
from dotenv import find_dotenv

from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    # Monad settings
    MONAD_TESTNET_RPC: str = Field(default="")

    # Proxy settings
    HTTP_PROXY: Optional[str] = Field(default=None)
    HTTPS_PROXY: Optional[str] = Field(default=None)

    # Request settings
    MAX_CONCURRENT_REQUESTS: int = Field(default=8)

    # Logging settings
    LOG_LEVEL: str = Field(default="INFO")

    # UI settings
    SHOW_PROGRESS_BAR: bool = Field(default=False)

    @field_validator("MONAD_TESTNET_RPC")
    def validate_monad_rpc(cls, v: str) -> str:
        if not v:
            raise ValueError("MONAD_TESTNET_RPC is not set")
        return v

    model_config = ConfigDict(
        env_file=find_dotenv(),
        case_sensitive=True,
    )


# Global config instance
config = Config()
