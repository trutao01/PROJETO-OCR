import customtkinter as ctk
import tkinter as tk
import sys
import mss
import mss.tools
from PIL import Image
from ocr_engine import OCREngine
import threading
import keyboard

# Configuração de Aparência
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END) # Scroll para o final
        
    def flush(self):
        pass

class OCRTranslatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("KRONOS - Screen Translator")
        self.geometry("600x450")
        self.attributes("-topmost", True)

        self.engine = OCREngine()
        self.hotkey = "f8" # Atalho padrão
        self.is_active = False

        self.setup_ui()
        
        # Redireciona o print para o painel de logs
        sys.stdout = RedirectText(self.log_box)
        sys.stderr = RedirectText(self.log_box)
        
        print("Iniciando KRONOS Tradutor...")
        
        # Carrega modelo inicial no fundo
        threading.Thread(target=self.engine.set_language, args=("Inglês",), daemon=True).start()

    def setup_ui(self):
        self.tabview = ctk.CTkTabview(self, width=580)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)

        self.tab_main = self.tabview.add("Tradutor")
        self.tab_config = self.tabview.add("Configurações e Logs")

        # --- ABA PRINCIPAL ---
        self.lbl_title = ctk.CTkLabel(self.tab_main, text="Tradução em Tempo Real", font=("Segoe UI", 20, "bold"))
        self.lbl_title.pack(pady=15)

        self.lang_var = ctk.StringVar(value="Inglês")
        langs = ["Inglês", "Japonês", "Coreano", "Chinês (Simplificado)", "Chinês (Tradicional)", "Russo"]
        self.combo = ctk.CTkOptionMenu(self.tab_main, variable=self.lang_var, values=langs, command=self.on_lang_change)
        self.combo.pack(pady=10)

        # Botão/Switch Liga e Desliga
        self.switch_var = ctk.StringVar(value="off")
        self.switch = ctk.CTkSwitch(self.tab_main, text="Serviço Ativo", command=self.toggle_service,
                                    variable=self.switch_var, onvalue="on", offvalue="off", font=("Segoe UI", 14, "bold"))
        self.switch.pack(pady=20)

        self.lbl_status = ctk.CTkLabel(self.tab_main, text="Pressione a Tecla de Atalho para traduzir.", text_color="gray")
        self.lbl_status.pack(pady=10)

        # --- ABA CONFIGURAÇÕES E LOGS ---
        # Configuração de Atalho
        frame_hotkey = ctk.CTkFrame(self.tab_config)
        frame_hotkey.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(frame_hotkey, text="Tecla de Atalho:").pack(side="left", padx=10)
        self.entry_hotkey = ctk.CTkEntry(frame_hotkey, width=100)
        self.entry_hotkey.insert(0, self.hotkey)
        self.entry_hotkey.pack(side="left", padx=10)
        
        btn_save_hotkey = ctk.CTkButton(frame_hotkey, text="Salvar Atalho", width=100, command=self.save_hotkey)
        btn_save_hotkey.pack(side="left", padx=10)

        # Painel de Logs
        ctk.CTkLabel(self.tab_config, text="Console / Logs:", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.log_box = ctk.CTkTextbox(self.tab_config, height=200, fg_color="black", text_color="#00FF00", font=("Consolas", 11))
        self.log_box.pack(padx=10, pady=5, fill="both", expand=True)

    def save_hotkey(self):
        new_hk = self.entry_hotkey.get().lower()
        if new_hk:
            if self.is_active:
                keyboard.remove_hotkey(self.hotkey)
                keyboard.add_hotkey(new_hk, self.start_snip_thread)
            self.hotkey = new_hk
            print(f"Atalho atualizado para: {new_hk}")

    def toggle_service(self):
        if self.switch_var.get() == "on":
            self.is_active = True
            keyboard.add_hotkey(self.hotkey, self.start_snip_thread)
            self.lbl_status.configure(text=f"Ativo! Pressione '{self.hotkey.upper()}' para selecionar.", text_color="#00FF00")
            print("Serviço Ligado.")
        else:
            self.is_active = False
            keyboard.remove_hotkey(self.hotkey)
            self.lbl_status.configure(text="Inativo.", text_color="gray")
            print("Serviço Desligado.")

    def on_lang_change(self, choice):
        print(f"Alterando idioma para {choice}...")
        threading.Thread(target=self.engine.set_language, args=(choice,), daemon=True).start()

    def start_snip_thread(self):
        self.after(0, self.start_snip)

    def start_snip(self):
        self.withdraw()
        self.after(200, self.create_snip_window)

    def create_snip_window(self):
        self.snip_window = ctk.CTkToplevel(self)
        self.snip_window.attributes('-fullscreen', True)
        self.snip_window.attributes('-alpha', 0.3)
        self.snip_window.config(cursor="cross")
        
        self.canvas = tk.Canvas(self.snip_window, cursor="cross", bg="gray")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_snip_press)
        self.canvas.bind("<B1-Motion>", self.on_snip_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_snip_release)

    def on_snip_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='#00FFFF', width=3, fill="black")

    def on_snip_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_snip_release(self, event):
        end_x, end_y = event.x, event.y
        self.snip_window.destroy()
        
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        if x2 - x1 < 10 or y2 - y1 < 10:
            self.deiconify()
            return 

        self.process_snip(x1, y1, x2, y2)

    def process_snip(self, x1, y1, x2, y2):
        print(f"Capturando área: {x1},{y1} -> {x2},{y2}")
        with mss.mss() as sct:
            monitor = {"top": y1, "left": x1, "width": x2 - x1, "height": y2 - y1}
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        
        self.deiconify()
        
        loading_window = self.create_floating_result(x2, y1, "⏳ Traduzindo...")

        def run_ocr():
            resultado = self.engine.process_image(img)
            self.after(0, lambda: self.update_floating_result(loading_window, resultado))

        threading.Thread(target=run_ocr, daemon=True).start()

    def create_floating_result(self, x, y, text):
        float_win = ctk.CTkToplevel(self)
        float_win.overrideredirect(True)
        float_win.attributes("-topmost", True)
        float_win.attributes("-alpha", 0.9)
        
        screen_w = self.winfo_screenwidth()
        if x + 300 > screen_w: x = screen_w - 320
        float_win.geometry(f"+{x+10}+{y}")
        
        frame = ctk.CTkFrame(float_win, border_width=2, border_color="#00FFFF")
        frame.pack(fill="both", expand=True)
        
        lbl = ctk.CTkLabel(frame, text=text, font=("Segoe UI", 12), wraplength=280, justify="left")
        lbl.pack(padx=15, pady=15)
        
        btn_close = ctk.CTkButton(frame, text="✖", width=20, height=20, fg_color="transparent", hover_color="#FF5555", command=float_win.destroy)
        btn_close.place(relx=0.95, rely=0.05, anchor="ne")
        
        self.after(15000, float_win.destroy)
        return lbl

    def update_floating_result(self, lbl_widget, text):
        try:
            lbl_widget.configure(text=text)
            print("Tradução concluída.")
        except:
            pass

if __name__ == "__main__":
    app = OCRTranslatorApp()
    app.mainloop()
