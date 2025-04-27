from typing import Optional

from pydantic import Field, field_validator
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

    @field_validator("MONAD_TESTNET_RPC")
    @classmethod
    def validate_monad_rpc(cls, v: str) -> str:
        if not v:
            raise ValueError("MONAD_TESTNET_RPC is not set")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global config instance
config = Config()
