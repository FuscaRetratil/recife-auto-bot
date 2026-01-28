import json
import logging
import os

class ClientManager:
    def __init__(self, filepath="config/clients.json"):
        self.filepath = filepath
        self.clients = []
        self.load_clients()

    def load_clients(self):
        if not os.path.exists(self.filepath):
            logging.warning(f"Arquivo não encontrado: {self.filepath}")
            self.clients = []
            return
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.clients = json.load(f)
            logging.info(f"Clientes carregados: {len(self.clients)}")
        except Exception as e:
            logging.error(f"Erro ao carregar clientes: {e}")
            self.clients = []
    
    def get_interested_clients(self, car_price, car_year, discount_percent):
        interested_chat_ids = []

        for client in self.clients:
            if not client.get('active', True):
                continue

            filters = client.get('filters', {})

            min_year = filters.get('min_year', 0)
            if car_year and car_year < min_year:
                continue
            
            max_price = filters.get('max_price', float('inf'))
            if car_price > max_price:
                continue

            min_discount = filters.get('min_discount', 0)
            if discount_percent < min_discount:
                continue

            interested_chat_ids.append(client['chat_id'])
        return interested_chat_ids
