import json
import logging
import requests
from typing import List
from app.entities.processed_agent_data import ProcessedAgentData
from app.interfaces.store_gateway import StoreGateway

class StoreApiAdapter(StoreGateway):
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url

    def save_data(self, processed_agent_data_batch: list[ProcessedAgentData]) -> bool:
        url = f"{self.api_base_url}/processed_agent_data/"
        try:
            # Використовуємо mode="json" щоб datetime перетворився в рядок
            payload = [item.model_dump(mode="json") for item in processed_agent_data_batch]
            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()
            #logging.info(f"Successfully sent {len(processed_agent_data_batch)} items to Store API.")
            return True
        except Exception as e:
            #logging.error(f"Failed to send data to Store API: {e}")
            return False
