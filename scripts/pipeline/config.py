"""Pipeline configuration."""

import os
from dataclasses import dataclass


@dataclass
class PipelineConfig:
    """Configuration for the data pipeline.

    Holds API keys and file paths. Created from environment variables
    via the from_env() factory method.
    """

    fred_api_key: str | None
    fmp_api_key: str | None
    nasdaq_api_key: str | None
    data_path: str

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Create a PipelineConfig from environment variables."""
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "market_data.json",
        )
        return cls(
            fred_api_key=os.environ.get("FRED_API_KEY"),
            fmp_api_key=os.environ.get("FMP_API_KEY"),
            nasdaq_api_key=os.environ.get("NASDAQ_DATA_LINK_API_KEY"),
            data_path=data_path,
        )
