import time
import logging
import sys
from config.settings import Config
from database.db_manager import DatabaseManager
from scrapers.olx_scraper import OlxScraper
from services.fipe_service import FipeService
from services.telegram_service import TelegramNotifier
from services.client_manager import ClientManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def main():
    logging.info("Iniciando Sistema Multi-Cliente v2.0...")
    
    db = DatabaseManager(Config.DB_PATH)
    fipe = FipeService()
    
    notifier = TelegramNotifier(Config.TELEGRAM_TOKEN)
    client_manager = ClientManager("src/config/clients.json")
    
    scraper = OlxScraper(db, notifier, fipe, client_manager)

    logging.info(f"Monitorando: {Config.OLX_URL}")
    
    while True:
        try:
            logging.info("--- Iniciando ciclo ---")
            scraper.scrape(Config.OLX_URL)
            logging.info(f"Dormindo por {Config.CHECK_INTERVAL}s")
            time.sleep(Config.CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            logging.info("Parando bot...")
            break
        except Exception as e:
            logging.critical(f"Erro fatal: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()