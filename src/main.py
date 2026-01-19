import time
import logging
import sys
from config.settings import Config
from database.db_manager import DatabaseManager
from scrapers.olx_scraper import OlxScraper
from services.fipe_service import FipeService
from services.telegram_service import TelegramNotifier

# Configuração de Logs Profissional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


def main():
    logging.info("🚀 Iniciando Micro-SaaS Auto Bot (Produção v1.0)...")

    # 1. Inicializa dependências
    db = DatabaseManager(Config.DB_PATH)
    fipe = FipeService()
    notifier = TelegramNotifier(Config.TELEGRAM_TOKEN, Config.TELEGRAM_CHAT_ID)

    # 2. Inicializa o Scraper com tudo conectado
    scraper = OlxScraper(db, notifier, fipe)

    logging.info(f"Monitorando URL: {Config.OLX_URL}")
    logging.info(f"Intervalo entre ciclos: {Config.CHECK_INTERVAL} segundos")

    # 3. Loop Principal (24/7)
    while True:
        try:
            logging.info("--- Iniciando ciclo de verificação ---")
            scraper.scrape(Config.OLX_URL)

            logging.info(f"Ciclo concluído. Dormindo...")
            time.sleep(Config.CHECK_INTERVAL)

        except KeyboardInterrupt:
            logging.info("🛑 Bot parado manualmente.")
            break
        except Exception as e:
            logging.critical(f"Erro não tratado no loop principal: {e}")
            time.sleep(60)  # Espera de segurança para não travar o servidor


if __name__ == "__main__":
    main()
