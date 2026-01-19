import requests
import logging

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send_alert(self, message):
        if not self.token or not self.chat_id:
            logging.warning("Telegram: Token ou Chat ID não configurados.")
            return

        try:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            
            response = requests.post(self.base_url, data=payload, timeout=10)
            
            if response.status_code != 200:
                logging.error(f"Telegram API Erro: {response.text}")
            else:
                logging.info("Telegram: Alerta enviado com sucesso.")
                
        except Exception as e:
            logging.error(f"Telegram Conexão Falhou: {e}")