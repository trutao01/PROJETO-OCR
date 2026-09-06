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

        from PIL import ImageEnhance
        # Pre-processamento: aumenta o contraste para ajudar a IA a enxergar melhor as letras
        enhancer = ImageEnhance.Contrast(image_pil)
        image_pil = enhancer.enhance(2.0)

        # Converte a imagem para o formato que o EasyOCR entende
        image_np = np.array(image_pil)
        
        # Extrai os textos usando ampliação (mag_ratio) para fontes difíceis
        results = self.reader.readtext(image_np, detail=0, mag_ratio=2.0)
        
        # Junta todas as frases encontradas
        extracted_text = " ".join(results).strip()
        
        if not extracted_text:
            return "A IA não conseguiu ler as letras nessa imagem."

        print(f"Texto lido pelo OCR: {extracted_text}")
        
        # Mapeia o idioma selecionado para o código do tradutor
        lang_to_code = {
            "Inglês": "en", "Japonês": "ja", "Coreano": "ko",
            "Chinês (Simplificado)": "zh-CN", "Chinês (Tradicional)": "zh-TW", "Russo": "ru"
        }
        src_lang = lang_to_code.get(self.current_lang, "en")
        
        # Remove hifens e pontuações estranhas no final que causam bug no Google Translator
        clean_text = extracted_text.strip(" -_.,;?!")
        
        try:
            # Usar o idioma específico em vez de 'auto' resolve 99% dos erros 500 do Google
            translator = GoogleTranslator(source=src_lang, target='pt')
            translated = translator.translate(clean_text)
            
            # Se mesmo assim o Google falhar, usamos um tradutor de segurança (MyMemory)
            if "Error 500" in translated or "That's an error" in translated:
                from deep_translator import MyMemoryTranslator
                print("Google falhou, acionando tradutor reserva (MyMemory)...")
                # MyMemory exige en-US ou en-GB em vez de apenas 'en'
                src_my = "en-US" if src_lang == "en" else src_lang
                backup_translator = MyMemoryTranslator(source=src_my, target='pt-BR')
                translated = backup_translator.translate(clean_text)

            # Devolve a tradução e o texto original embaixo para o usuário conferir
            return f"{translated}\n\n(Original lido: {extracted_text})"
        except Exception as e:
            try:
                # Fallback caso o Google jogue um erro de internet/conexão
                from deep_translator import MyMemoryTranslator
                src_my = "en-US" if src_lang == "en" else src_lang
                backup_translator = MyMemoryTranslator(source=src_my, target='pt-BR')
                translated = backup_translator.translate(clean_text)
                return f"{translated}\n\n(Original lido: {extracted_text})"
            except:
                return f"⚠️ Erro nos servidores de tradução.\n\nTexto original lido: {extracted_text}"
