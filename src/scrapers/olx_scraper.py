import time
import re
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

class OlxScraper:
    def __init__(self, db_manager, notifier, fipe_service, client_manager):
        self.db = db_manager
        self.notifier = notifier
        self.fipe = fipe_service
        self.client_manager = client_manager
        self.driver = None

    def _setup_driver(self):
        logging.info("Configurando Driver...")
        chrome_options = Options()
        chrome_options.add_argument("--headless=new") 
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def scrape(self, url):
        logging.info(f"Acessando: {url}")
        if not self.driver:
            self._setup_driver()

        try:
            self.driver.get(url)
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "olx-adcard"))
                )
            except Exception:
                logging.warning("Timeout aguardando OLX.")

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
            time.sleep(2)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            ads = soup.find_all('section', class_='olx-adcard')

            logging.info(f"Anuncios na pagina: {len(ads)}")
            
            count_new = 0
            for ad in ads:
                try:
                    link_tag = ad.find('a', {'data-testid': 'adcard-link'})
                    if not link_tag: continue
                    
                    href = link_tag.get('href')
                    title = link_tag.get('title') or link_tag.text.strip()
                    
                    ad_id = href.split('-')[-1]
                    if not ad_id.isdigit(): continue

                    if self.db.ad_exists(ad_id):
                        continue

                    price_val = 0.0
                    price_tag = ad.find('h3', class_='olx-adcard__price')
                    if price_tag:
                        clean = price_tag.text.strip().replace('R$', '').replace('.', '').replace(' ', '').replace('\xa0', '')
                        if clean.isdigit():
                            price_val = float(clean)

                    year = None
                    year_match = re.search(r'(19|20)\d{2}', title)
                    if year_match:
                        year = int(year_match.group(0))

                    if price_val > 0:
                        fipe_price = self.fipe.get_fipe_price(title, year)
                        
                        discount_percent = 0
                        if fipe_price:
                            discount_val = fipe_price - price_val
                            discount_percent = (discount_val / fipe_price) * 100
                        
                        self.db.save_ad({
                            'id': ad_id, 'title': title, 'price': price_val, 'url': href
                        })
                        count_new += 1
                        
                        interested_ids = self.client_manager.get_interested_clients(
                            price_val, year, discount_percent
                        )

                        if interested_ids and self.notifier:
                            logging.info(f"Notificando {len(interested_ids)} clientes sobre: {title}")
                            
                            fipe_text = f"R$ {fipe_price:,.2f}" if fipe_price else "N/A"
                            discount_text = f"{int(discount_percent)}% OFF" if fipe_price else "S/ FIPE"

                            msg = (
                                f"<b>🚨 OPORTUNIDADE ({discount_text})</b>\n\n"
                                f"🚗 <b>{title}</b>\n"
                                f"📅 Ano: {year if year else 'N/A'}\n"
                                f"💰 Pede: R$ {price_val:,.2f}\n"
                                f"📉 FIPE: {fipe_text}\n"
                                f"🔗 <a href='{href}'>Ver Anúncio</a>"
                            )
                            
                            for chat_id in interested_ids:
                                self.notifier.send_alert(chat_id, msg)

                except Exception as e:
                    logging.error(f"Erro item: {e}")
                    continue
            
            logging.info(f"Novos processados: {count_new}")

        except Exception as e:
            logging.critical(f"Erro scraper: {e}")
            if self.driver:
                self.driver.quit()
                self.driver = None