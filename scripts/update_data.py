#!/usr/bin/env python3
"""Market State Data Pipeline CLI.

This script acts as the entry point for GitHub Actions or local execution
to fetch market data, calculate indicators, and save the result to JSON.
"""

import os
import json
import logging
from dotenv import load_dotenv

from pipeline import PipelineConfig, refresh_all

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_existing_data(data_path):
    if os.path.exists(data_path):
        try:
            with open(data_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading existing market data: {e}")
    return {}


def save_data(data, data_path):
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    try:
        with open(data_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved market data to {data_path}")
    except Exception as e:
        logger.error(f"Error saving market data: {e}")


def main():
    logger.info("Starting market data pipeline...")
    
    # Load .env file so API keys are available via os.environ
    load_dotenv()
    
    config = PipelineConfig.from_env()
    
    # Load previous data for fallback purposes
    existing_data = load_existing_data(config.data_path)
    
    # Run the orchestrator
    updated_data = refresh_all(config, existing_data)
    
    # Save the updated data
    save_data(updated_data, config.data_path)
    
    logger.info("Market data pipeline completed successfully!")


if __name__ == "__main__":
    main()
