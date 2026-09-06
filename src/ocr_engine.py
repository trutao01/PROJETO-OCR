import easyocr
from deep_translator import GoogleTranslator
import numpy as np
from PIL import Image

class OCREngine:
    def __init__(self):
        # O modelo é carregado apenas quando o usuário escolhe o idioma
        self.reader = None
        self.current_lang = None
        
        # Mapeando os nomes dos idiomas para os códigos do EasyOCR
        self.lang_map = {
            "Inglês": ['en'],
            "Japonês": ['ja', 'en'],
            "Coreano": ['ko', 'en'],
            "Chinês (Simplificado)": ['ch_sim', 'en'],
            "Chinês (Tradicional)": ['ch_tra', 'en'],
            "Russo": ['ru', 'en']
        }

    def set_language(self, lang_name):
        """Inicializa ou troca o modelo do OCR se o idioma mudar."""
        if lang_name != self.current_lang:
            print(f"Carregando inteligência artificial para: {lang_name} (Isso pode demorar um pouco na primeira vez...)")
            langs = self.lang_map.get(lang_name, ['en'])
            # Usando GPU se disponível, senão vai no processador (CPU)
            self.reader = easyocr.Reader(langs)
            self.current_lang = lang_name
            print("Modelo carregado com sucesso!")

    def process_image(self, image_pil):
        """Recebe uma imagem da tela, lê o texto e traduz para PT-BR."""
        if self.reader is None:
            return "Selecione um idioma primeiro."

        # Converte a imagem para o formato que o EasyOCR entende
        image_np = np.array(image_pil)
        
        # Extrai os textos da imagem
        results = self.reader.readtext(image_np)
        
        if not results:
            return "Nenhum texto encontrado na área."

        # Junta todas as frases encontradas
        extracted_text = " ".join([res[1] for res in results])
        
        try:
            # Traduz automaticamente para português
            translator = GoogleTranslator(source='auto', target='pt')
            translated = translator.translate(extracted_text)
            return translated
        except Exception as e:
            return "Erro na tradução. Verifique sua internet."
