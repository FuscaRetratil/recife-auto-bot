import time
import random
import re
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


class OlxScraper:
    def __init__(self, db_manager, notifier, fipe_service):
        self.db = db_manager
        self.notifier = notifier
        self.fipe = fipe_service
        self.driver = None

    def _setup_driver(self):
        logging.info("Configurando Google Chrome Driver...")
        chrome_options = Options()
#        chrome_options.add_argument("--headless=new")
#        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def scrape(self, url):
        logging.info(f"Iniciando raspagem: {url}")
        if not self.driver:
            self._setup_driver()

        try:
            self.driver.get(url)

            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "olx-adcard"))
                )
            except:
                logging.warning(
                    "Timeout: Elementos da OLX demoraram a aparecer.")

            # Scroll para carregar imagens/dados lazy
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight/3);")
            time.sleep(2)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            ads = soup.find_all('section', class_='olx-adcard')

            logging.info(f"Anúncios encontrados no HTML: {len(ads)}")

            count_new = 0
            for ad in ads:
                try:
                    link_tag = ad.find('a', {'data-testid': 'adcard-link'})
                    if not link_tag:
                        continue

                    href = link_tag.get('href')
                    title = link_tag.get('title') or link_tag.text.strip()

                    ad_id = href.split('-')[-1]
                    if not ad_id.isdigit():
                        continue

                    if self.db.ad_exists(ad_id):
                        continue

                    price_val = 0.0
                    price_tag = ad.find('h3', class_='olx-adcard__price')
                    if price_tag:
                        price_text = price_tag.text.strip()
                        clean_price = price_text.replace('R$', '').replace(
                            '.', '').replace(' ', '').replace('\xa0', '')
                        if clean_price.isdigit():
                            price_val = float(clean_price)

                    year = None
                    year_match = re.search(r'(19|20)\d{2}', title)
                    if year_match:
                        year = int(year_match.group(0))

                    if price_val > 0:
                        fipe_price = self.fipe.get_fipe_price(title, year)

                        discount_percent = 0
                        is_opportunity = False

                        if fipe_price:
                            discount_val = fipe_price - price_val
                            discount_percent = (
                                discount_val / fipe_price) * 100

                            if discount_percent >= 20:
                                is_opportunity = True

                        self.db.save_ad({
                            'id': ad_id,
                            'title': title,
                            'price': price_val,
                            'url': href
                        })
                        count_new += 1

                        # Dispara alerta
                        if is_opportunity and self.notifier:
                            logging.info(
                                f"🚨 OPORTUNIDADE: {title} (-{discount_percent:.1f}%)")
                            msg = (
                                f"<b>🚨 SUPER OFERTA ({int(discount_percent)}% OFF)</b>\n\n"
                                f"🚗 <b>{title}</b>\n"
                                f"📅 Ano: {year}\n"
                                f"💰 Pede: R$ {price_val:,.2f}\n"
                                f"📉 FIPE: R$ {fipe_price:,.2f}\n"
                                f"🔗 <a href='{href}'>Ver Anúncio</a>"
                            )
                            self.notifier.send_alert(msg)

                except Exception as e:
                    logging.error(f"Erro ao processar item individual: {e}")
                    continue

            logging.info(f"Novos anúncios processados: {count_new}")

        except Exception as e:
            logging.critical(f"Erro fatal no scraper: {e}")
            if self.driver:
                self.driver.quit()
                self.driver = None
