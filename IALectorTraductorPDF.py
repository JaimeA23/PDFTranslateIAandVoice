import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import fitz  # PyMuPDF
import pyttsx3
import pygame
import threading
import os
import time
import re
import hashlib
import json
import requests

class LMStudioTranslator:
    def __init__(self, base_url="http://localhost:1234"):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def translate(self, text, target_lang="es", language_name="Español", formal=True):
        endpoint = f"{self.base_url}/v1/chat/completions"

        system_prompt = self.get_system_prompt(target_lang)
        
        style = "formal profesional" if formal else "coloquial natural"
        user_prompt = f"""Traduce este texto al {target_lang} ({style}):
        {text}"""

        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": len(text) * 2,
            "top_p": 0.95,
            "frequency_penalty": 0.5,
            "presence_penalty": 0.3
        }

        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                data=json.dumps(payload))
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        
        except requests.exceptions.RequestException as e:
            return f"Error: {str(e)}"
        except KeyError:
            return "Error en el formato de respuesta"

    def get_system_prompt(self, target_lang):
        prompts = {
            'es': """Eres un traductor profesional especializado en traducciones técnicas. 
                Tu tarea es:
                1. Traducir con máxima fidelidad el texto proporcionado
                2. Mantener términos técnicos en su idioma original
                3. Conservar formatos y estructuras
                4. Respeta nombres propios y siglas
                5. Usar Español estándar internacional
                6. Devolver únicamente la traducción, sin comentarios adicionales""",
            'en': """You are a professional translator specialized in technical translations. 
                Your task is to:
                1. Translate with maximum fidelity the text provided 2.
                2. Maintain technical terms in their original language.
                3. Preserve formats and structures
                4. Respect proper names and acronyms
                5. Use international standard english.
                6. Return only the translation, without additional comments.""",
            'fr': """Vous êtes un traducteur professionnel spécialisé dans les traductions techniques. 
                Votre tâche consiste à
                1. traduire le texte fourni avec un maximum de fidélité
                2. maintenir les termes techniques dans leur langue d'origine
                3. Conserver les formats et les structures
                4. Respecter les noms propres et les acronymes
                5. Utiliser la norme internationale du français
                6. Ne renvoyer que la traduction, sans commentaires supplémentaires""",
            'de': """Sie sind ein professioneller Übersetzer, der sich auf technische Übersetzungen spezialisiert hat. 
                Ihre Aufgabe ist es:
                1. den gelieferten Text möglichst originalgetreu zu übersetzen.
                2. die Fachbegriffe in der Originalsprache beibehalten.
                3. Formate und Strukturen beibehalten
                4. Respektieren Sie Eigennamen und Akronyme
                5. Verwenden Sie internationales Standarddeutsch
                6. Senden Sie nur die Übersetzung zurück, ohne zusätzliche Kommentare""",
            'it': """Siete un traduttore professionista specializzato in traduzioni tecniche. 
                Il vostro compito è di:
                1. Tradurre il testo fornito con la massima fedeltà.
                2. Mantenere i termini tecnici nella lingua originale.
                3. Conservare i formati e le strutture.
                4. Rispettare i nomi propri e gli acronimi.
                5. Utilizzare l'italiano standard internazionale
                6. Restituire solo la traduzione, senza ulteriori commenti""",
            'pt': """É um tradutor profissional especializado em traduções técnicas. 
                A sua tarefa consiste em
                1. traduzir o texto fornecido com a máxima fidelidade.
                2. manter os termos técnicos na sua língua original.
                3. Conservar os formatos e as estruturas
                4. Respeitar os nomes próprios e os acrónimos
                5. Utilizar o português padrão internacional
                6. Devolver apenas a tradução, sem comentários adicionais""",
            'zh-cn': """您是一名专业技术翻译员。
                您的任务是
                1. 最大限度地忠实翻译所提供的文本。
                2. 保留原文中的技术术语。
                3. 保留格式和结构
                4. 尊重专有名称和缩略语
                5. 使用国际标准简体中文
                6. 只交回译文，不附加评论。""",
            'ja': """あなたは技術翻訳を専門とするプロの翻訳者です。
                あなたの仕事は
                1.提供されたテキストを最大限に忠実に翻訳する。
                2.専門用語を原語のまま維持する。
                3. 形式と構造を維持する。
                4. 固有名詞と略語を尊重する。
                5. 国際標準語の使用
                6. 追加コメントなしで、翻訳のみを返却すること。""",
            'ru': """Вы - профессиональный переводчик, специализирующийся на технических переводах. 
                Ваша задача состоит в том, чтобы:
                1. перевести предоставленный текст с максимальной точностью.
                2. сохранить технические термины на языке оригинала.
                3. Сохранить форматы и структуры.
                4. Соблюдать имена собственные и аббревиатуры.
                5. Используйте международный стандарт русского языка
                6. Возвращать только перевод, без дополнительных комментариев.""",
            'ar': """أنت مترجم محترف متخصص في الترجمة التقنية. 
                مهمتك هي
                1 - ترجمة النص المقدم بأقصى قدر من الدقة.
                2- الحفاظ على المصطلحات التقنية بلغتها الأصلية.
                3. الحفاظ على التنسيقات والتراكيب
                4. احترام أسماء العلم والمختصرات
                5. استخدام اللغة العربية الفصحى الدولية
                6. أعد الترجمة فقط، دون تعليقات إضافية."""
        }
        return prompts.get(target_lang, prompts['en'])

class PDFPagedViewer:
    def __init__(self, root):
        self.root = root
        self.doc = None
        self.current_page = 0
        self.total_pages = 0
        self.page_texts = []
        self.pages_per_view = 1
        self.translator = LMStudioTranslator()
        self.languages = [
            ('Inglés', 'en'), ('Español', 'es'), ('Francés', 'fr'),
            ('Alemán', 'de'), ('Italiano', 'it'), ('Portugués', 'pt'),
            ('Chino', 'zh-cn'), ('Japonés', 'ja'), ('Ruso', 'ru'), ('Árabe', 'ar')
        ]
        
        self.playing = False
        self.paused = False
        self.current_audio_file = None
        self.current_audio_hash = None
        self.stop_event = threading.Event()
        pygame.mixer.init()
        
        self.setup_ui()

    def setup_ui(self):
        self.toolbar = ttk.Frame(self.root)
        self.toolbar.pack(fill=tk.X, padx=5, pady=5, side=tk.TOP)
        
        ttk.Button(self.toolbar, text="Abrir PDF", command=self.load_pdf_dialog).pack(side=tk.LEFT)
        
        # Control de páginas por vista
        ttk.Label(self.toolbar, text="Vistas:").pack(side=tk.LEFT, padx=5)
        self.view_scale = ttk.Scale(
            self.toolbar,
            from_=1,
            to=5,
            orient=tk.HORIZONTAL,
            length=100,
            command=self.update_pages_view
        )
        self.view_scale.set(1)
        self.view_scale.pack(side=tk.LEFT, padx=5)
        self.view_label = ttk.Label(self.toolbar, text="1")
        self.view_label.pack(side=tk.LEFT)
        
        self.language_var = tk.StringVar()
        self.lang_combobox = ttk.Combobox(
            self.toolbar,
            textvariable=self.language_var,
            values=[lang[0] for lang in self.languages],
            state="readonly",
            width=15
        )
        self.lang_combobox.set('Inglés')
        self.lang_combobox.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.toolbar, text="Traducir", command=self.start_translation_thread).pack(side=tk.LEFT, padx=5)
        self.page_label = ttk.Label(self.toolbar, text="Páginas: 0/0")
        self.page_label.pack(side=tk.RIGHT, padx=10)
        
        self.audio_toolbar = ttk.Frame(self.root)
        self.audio_toolbar.pack(fill=tk.X, padx=5, pady=5, side=tk.TOP)
        
        self.play_btn = ttk.Button(self.audio_toolbar, text="▶", command=self.toggle_play)
        self.play_btn.pack(side=tk.LEFT)
        self.stop_btn = ttk.Button(self.audio_toolbar, text="⏹", command=self.stop_audio)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.volume_scale = ttk.Scale(self.audio_toolbar, from_=0.0, to=1.0, value=0.5, command=self.set_volume)
        self.volume_scale.pack(side=tk.RIGHT, padx=10)
        ttk.Label(self.audio_toolbar, text="Volumen:").pack(side=tk.RIGHT)
        
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.text_widget = tk.Text(self.main_frame, wrap="word", font=("Helvetica", 10), padx=10, pady=10)
        self.scrollbar = ttk.Scrollbar(self.main_frame, command=self.on_scroll)
        self.text_widget.configure(yscrollcommand=self.scrollbar.set)
        
        self.page_progress = ttk.Scale(
            self.main_frame, 
            orient=tk.VERTICAL,
            from_=1,
            to=1,
            command=self.on_progress_move
        )
        self.page_progress.set(1)
        
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.page_progress.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        
        self.text_widget.bind("<MouseWheel>", self.on_mousewheel)
        self.text_widget.bind("<Button-4>", self.on_mousewheel)
        self.text_widget.bind("<Button-5>", self.on_mousewheel)
        
        self.update_text_display("Abre un archivo PDF para comenzar")

    def clean_text(self, text):
        text = re.sub(r'(?<![.!?,;:\n])\n', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'([.!?;:])\s*', r'\1\n', text)
        return text.strip()

    def load_pdf_dialog(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            self.load_pdf(file_path)

    def load_pdf(self, path: str):
        self.doc = fitz.open(path)
        self.total_pages = len(self.doc)
        self.page_texts = []
        
        for page in self.doc:
            raw_text = page.get_text("text")
            self.page_texts.append(self.clean_text(raw_text))
        
        self.current_page = 0
        self.page_progress.config(from_=1, to=self.total_pages)
        self.show_page()

    def show_page(self):
        if not self.page_texts:
            return
        
        self.stop_audio()
        
        start_page = self.current_page
        end_page = min(start_page + self.pages_per_view - 1, self.total_pages - 1)
        
        combined_text = ""
        for page in range(start_page, end_page + 1):
            page_number = page + 1
            combined_text += f"--- Página {page_number} ---\n"
            combined_text += self.page_texts[page] + "\n\n"
        
        self.current_display_text = combined_text.strip()
        self.update_display()
        
        page_range = f"{start_page + 1}-{end_page + 1}" if start_page != end_page else f"{start_page + 1}"
        self.page_label.config(text=f"Páginas: {page_range}/{self.total_pages}")
        self.page_progress.set(self.current_page + 1)

    def update_pages_view(self, value):
        new_value = int(float(value))
        if new_value != self.pages_per_view:
            self.pages_per_view = new_value
            self.view_label.config(text=str(new_value))
            self.show_page()

    def start_translation_thread(self):
        if not self.page_texts:
            return
        
        threading.Thread(target=self.translate_page).start()

    def translate_page(self):
        try:
            self.stop_audio()
            target_lang_code = self.get_language_code()
            language_name = self.language_var.get()
            original_text = self.current_display_text
            
            translated = self.translator.translate(
                text=original_text,
                target_lang=target_lang_code,
                language_name=language_name,
                formal=True
            )
            
            if translated.startswith("Error:"):
                raise Exception(translated)
            
            self.current_display_text = self.clean_text(translated)
            self.root.after(0, self.update_display)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"No se pudo traducir: {str(e)}"))

    def update_display(self):
        self.text_widget.configure(state="normal")
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert(tk.END, self.current_display_text)
        self.text_widget.configure(state="disabled")
        self.text_widget.yview_moveto(0)

    def toggle_play(self):
        if not self.current_display_text.strip():
            return
        
        if self.playing and not self.paused:
            self.pause_audio()
        else:
            self.play_audio()

    def play_audio(self):
        if self.paused:
            pygame.mixer.music.unpause()
            self.paused = False
            self.playing = True
            return
        
        current_hash = self.get_content_hash()
        if current_hash != self.current_audio_hash:
            self.stop_audio()
            self.current_audio_hash = current_hash
            self.current_audio_file = f"temp_audio_{current_hash}.wav"
            
            if not os.path.exists(self.current_audio_file):
                threading.Thread(target=self.generate_audio).start()
            else:
                threading.Thread(target=self.play_generated_audio).start()
        else:
            threading.Thread(target=self.play_generated_audio).start()

    def generate_audio(self):
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 180)
            engine.setProperty('volume', 1.0)
            
            formatted_text = self.current_display_text.replace("--- Página", "\n\n--- Página")
            engine.save_to_file(formatted_text, self.current_audio_file)
            engine.runAndWait()
            self.play_generated_audio()
        except Exception as e:
            messagebox.showerror("Error", f"Error generando audio: {str(e)}")

    def play_generated_audio(self):
        try:
            pygame.mixer.music.load(self.current_audio_file)
            pygame.mixer.music.play()
            self.playing = True
            self.paused = False
            while pygame.mixer.music.get_busy() and not self.stop_event.is_set():
                time.sleep(0.1)
            self.playing = False
        except Exception as e:
            messagebox.showerror("Error", f"Error reproduciendo audio: {str(e)}")

    def pause_audio(self):
        if self.playing and not self.paused:
            pygame.mixer.music.pause()
            self.paused = True

    def stop_audio(self):
        self.stop_event.set()
        pygame.mixer.music.stop()
        self.playing = False
        self.paused = False
        self.clean_audio_files()
        self.stop_event.clear()

    def set_volume(self, val):
        pygame.mixer.music.set_volume(float(val))

    def get_content_hash(self):
        return hashlib.md5(self.current_display_text.encode()).hexdigest()

    def clean_audio_files(self):
        if self.current_audio_file and os.path.exists(self.current_audio_file):
            try:
                os.remove(self.current_audio_file)
            except:
                pass

    def get_language_code(self):
        selected_lang = self.language_var.get()
        return next((lang[1] for lang in self.languages if lang[0] == selected_lang), 'en')

    def update_text_display(self, message: str):
        self.text_widget.configure(state="normal")
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert(tk.END, message)
        self.text_widget.configure(state="disabled")

    def on_scroll(self, action, *args):
        self.change_page(1 if args[0] == "1" else -1)

    def on_mousewheel(self, event):
        self.change_page(-1 if (event.num == 4 or event.delta > 0) else 1)

    def change_page(self, delta: int):
        new_page = self.current_page + delta
        if 0 <= new_page < self.total_pages:
            self.current_page = new_page
            self.show_page()

    def on_progress_move(self, value):
        new_page = int(float(value)) - 1
        if 0 <= new_page < self.total_pages and new_page != self.current_page:
            self.current_page = new_page
            self.show_page()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Lector de PDF Traducción y Voz")
    root.geometry("800x600")
    app = PDFPagedViewer(root)
    root.mainloop()
    app.stop_audio()