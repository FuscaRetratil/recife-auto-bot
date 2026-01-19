import requests
import logging
from thefuzz import process, fuzz

class FipeService:
    def __init__(self):
        self.base_url = "https://parallelum.com.br/fipe/api/v1/carros/marcas"
        self.models_cache = {}
        # Mapeamento manual para economizar requisições
        self.brands_map = {
            "chevrolet": 23, "vw": 59, "volkswagen": 59, "fiat": 21,
            "ford": 22, "honda": 25, "toyota": 56, "hyundai": 26,
            "renault": 48, "nissan": 43, "jeep": 29, "kia": 31,
            "peugeot": 44, "citroen": 11, "mitsubishi": 41
        }

    def _get_brand_id(self, text):
        text_lower = text.lower()
        for name, brand_id in self.brands_map.items():
            if name in text_lower:
                return brand_id
        return None

    def _fetch_models(self, brand_id):
        if brand_id in self.models_cache:
            return self.models_cache[brand_id]
        
        try:
            url = f"{self.base_url}/{brand_id}/modelos"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = data.get('modelos', [])
                self.models_cache[brand_id] = models
                return models
        except Exception as e:
            logging.error(f"Erro ao baixar modelos da marca {brand_id}: {e}")
        
        return []

    def get_fipe_price(self, ad_title, ad_year):
        if not ad_year:
            return None

        brand_id = self._get_brand_id(ad_title)
        if not brand_id:
            return None

        models = self._fetch_models(brand_id)
        if not models:
            return None

        # Fuzzy Matching: Encontra o modelo FIPE mais parecido com o título do anúncio
        model_names = [m['nome'] for m in models]
        best_match, score = process.extractOne(ad_title, model_names, scorer=fuzz.token_set_ratio)

        # Se a certeza for menor que 70%, assumimos que não achamos o carro certo
        if score < 70:
            return None

        best_model_data = next((m for m in models if m['nome'] == best_match), None)
        if not best_model_data:
            return None

        try:
            # Busca o preço específico do Ano
            model_code = best_model_data['codigo']
            url_years = f"{self.base_url}/{brand_id}/modelos/{model_code}/anos"
            resp_years = requests.get(url_years, timeout=5)
            years_data = resp_years.json()

            target_code = None
            for y_data in years_data:
                if str(ad_year) in y_data['nome']:
                    target_code = y_data['codigo']
                    break
            
            if not target_code:
                return None

            url_price = f"{self.base_url}/{brand_id}/modelos/{model_code}/anos/{target_code}"
            resp_price = requests.get(url_price, timeout=5)
            price_data = resp_price.json()
            
            price_str = price_data.get('Valor', '0').replace('R$', '').replace('.', '').replace(',', '.')
            return float(price_str)

        except Exception as e:
            logging.error(f"Erro ao buscar preço final FIPE: {e}")
            return None