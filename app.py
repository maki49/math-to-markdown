from __future__ import annotations

import logging
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser

from PIL import Image, ImageGrab, ImageOps, ImageTk
from core import MODELS, Engine, available, ready, to_markdown

ROOT = Path(__file__).resolve().parent
LOG = ROOT / 'app.log'
# pythonw has no console streams; model libraries may still write to them.
if sys.stdout is None:
    sys.stdout = LOG.open('a', encoding='utf-8', buffering=1)
if sys.stderr is None:
    sys.stderr = sys.stdout
logging.basicConfig(filename=LOG, level=logging.INFO, encoding='utf-8',
                    format='%(asctime)s %(levelname)s %(message)s')


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Math → Markdown')
        self.geometry('780x740')
        self.minsize(620, 620)
        self.configure(bg='#f5f6f8')
        self.engine = Engine()
        self.events = queue.Queue()
        self.busy = False
        self.source = None
        self.preview_photo = None
        self.model = tk.StringVar(value=MODELS['rapid']['name'])
        self.mode = tk.StringVar(value='块公式')
        self.status = tk.StringVar(value='Win + Shift + S 截图，然后在这里按 Ctrl + V')
        self._build()
        self.bind('<Control-v>', self._paste_shortcut)
        self.bind('<Control-Return>', lambda event: self.recognize())
        self.bind('<Control-Shift-C>', lambda event: self.copy())
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(100, self.poll)

    def _build(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('.', font=('Microsoft YaHei UI', 10), background='#f5f6f8')
        style.configure('TButton', padding=(13, 8), borderwidth=0)
        style.configure('Accent.TButton', background='#315efb', foreground='white')
        style.map('Accent.TButton', background=[('active', '#2447cc'), ('disabled', '#a8b4dd')])
        style.configure('TCombobox', padding=5)
        outer = ttk.Frame(self, padding=24)
        outer.pack(fill='both', expand=True)
        header = ttk.Frame(outer)
        header.pack(fill='x')
        ttk.Label(header, text='Math → Markdown', font=('Segoe UI', 23, 'bold')).pack(side='left')
        ttk.Button(header, text='模型管理', command=self.model_manager).pack(side='right')
        ttk.Label(outer, text='粘贴公式截图，带走可编辑的 Markdown。', foreground='#687080').pack(anchor='w', pady=(5, 18))
        self.preview = tk.Label(outer, text='在此粘贴公式截图\n\nCtrl + V  /  打开图片',
                                bg='white', fg='#858c9b', font=('Microsoft YaHei UI', 13),
                                relief='flat', height=1)
        self.preview.pack(fill='both', expand=True)
        self.preview.bind('<Configure>', lambda event: self.render_preview())
        bar = ttk.Frame(outer)
        bar.pack(fill='x', pady=12)
        self.paste_btn = ttk.Button(bar, text='粘贴截图', command=self.paste)
        self.paste_btn.pack(side='left')
        self.open_btn = ttk.Button(bar, text='打开图片', command=self.open_image)
        self.open_btn.pack(side='left', padx=8)
        self.recognize_btn = ttk.Button(bar, text='识别公式  ↵', style='Accent.TButton', command=self.recognize)
        self.recognize_btn.pack(side='right')
        options = ttk.Frame(outer)
        options.pack(fill='x', pady=(0, 14))
        self.model_box = ttk.Combobox(options, textvariable=self.model, state='readonly',
                                      values=[m['name'] for m in MODELS.values()], width=29)
        self.model_box.pack(side='left')
        self.mode_box = ttk.Combobox(options, textvariable=self.mode, state='readonly',
                                     values=['块公式', '行内公式', '纯 LaTeX'], width=11)
        self.mode_box.pack(side='right')
        self.mode_box.bind('<<ComboboxSelected>>', self.reformat)
        ttk.Label(outer, text='MARKDOWN', font=('Segoe UI', 9, 'bold'), foreground='#687080').pack(anchor='w')
        self.output = tk.Text(outer, height=7, wrap='word', font=('Consolas', 12),
                              bg='white', fg='#1f2937', relief='flat', padx=14, pady=12,
                              undo=True, insertbackground='#315efb')
        self.output.pack(fill='x', pady=(7, 12))
        footer = ttk.Frame(outer)
        footer.pack(fill='x')
        ttk.Label(footer, text='本地识别 · 无需 API key', foreground='#687080').pack(side='left')
        ttk.Button(footer, text='保存 .md', command=self.save).pack(side='right')
        ttk.Button(footer, text='复制 Markdown', style='Accent.TButton', command=self.copy).pack(side='right', padx=8)
        self.progress = ttk.Progressbar(outer, mode='indeterminate')
        self.progress.pack(fill='x', pady=(14, 7))
        ttk.Label(outer, textvariable=self.status, foreground='#687080', wraplength=690).pack(anchor='w')

    def key(self):
        return next(k for k, v in MODELS.items() if v['name'] == self.model.get())

    def _paste_shortcut(self, event):
        # Let text-only clipboard contents paste normally into the editor.
        try:
            value = ImageGrab.grabclipboard()
        except Exception:
            value = None
        if isinstance(value, Image.Image) or isinstance(value, list) or event.widget != self.output:
            self.paste(value)
            return 'break'

    def paste(self, value=None):
        if self.busy:
            return
        try:
            if value is None:
                value = ImageGrab.grabclipboard()
            if isinstance(value, Image.Image):
                self.set_image(value)
            elif isinstance(value, list) and value:
                self.load_image(value[0])
            else:
                self.status.set('剪贴板中没有图片。请先用 Win + Shift + S 截取公式。')
        except Exception as exc:
            self.error(exc)

    def open_image(self):
        if self.busy:
            return
        path = filedialog.askopenfilename(filetypes=[('图片', '*.png *.jpg *.jpeg *.bmp *.webp'), ('所有文件', '*.*')])
        if path:
            self.load_image(path)

    def load_image(self, path):
        try:
            with Image.open(path) as image:
                self.set_image(ImageOps.exif_transpose(image))
        except Exception as exc:
            self.error(exc)

    def set_image(self, image):
        if image.width * image.height > 25_000_000:
            raise ValueError('图片过大，请裁剪到公式区域后重试（最多 2500 万像素）。')
        rgba = image.convert('RGBA')
        background = Image.new('RGBA', rgba.size, 'white')
        background.alpha_composite(rgba)
        self.source = background.convert('RGB')
        self.output.delete('1.0', 'end')
        self.render_preview()
        self.status.set(f'已载入 {image.width} × {image.height} 图片 · 点击识别或按 Ctrl + Enter')

    def render_preview(self):
        if self.source is None:
            return
        image = self.source.copy()
        image.thumbnail((max(1, self.preview.winfo_width() - 24), max(1, self.preview.winfo_height() - 24)), Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(image)
        self.preview.configure(image=self.preview_photo, text='')

    def run_job(self, fn, kind, message):
        if self.busy:
            return
        self.busy = True
        for widget in (self.paste_btn, self.open_btn, self.recognize_btn, self.model_box):
            widget.configure(state='disabled')
        self.status.set(message)
        self.progress.start(12)
        def work():
            try:
                self.events.put((kind, fn()))
            except Exception as exc:
                logging.exception('Background job failed')
                self.events.put(('error', str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def recognize(self):
        if self.busy:
            return
        if self.source is None:
            self.status.set('请先粘贴截图或打开一张公式图片。')
            return
        key = self.key()
        if not ready(key):
            self.status.set('所选模型尚未准备好。请打开“模型管理”下载 / 加载。')
            self.model_manager()
            return
        image = self.source.copy()
        def work():
            start = time.monotonic()
            return self.engine.recognize(key, image), time.monotonic() - start
        self.run_job(work, 'result', '正在本机识别… 首次加载模型会稍慢。')

    def poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == 'progress':
                    self.status.set(value)
                    continue
                self.busy = False
                self.progress.stop()
                for widget in (self.paste_btn, self.open_btn, self.recognize_btn):
                    widget.configure(state='normal')
                self.model_box.configure(state='readonly')
                if kind == 'result':
                    latex, seconds = value
                    self.output.delete('1.0', 'end')
                    self.output.insert('1.0', to_markdown(latex, self.mode.get()))
                    self.status.set(f'识别完成 · {seconds:.1f} 秒 · 可编辑后复制，请核对上下标和符号。')
                elif kind == 'ready':
                    self.status.set('模型已准备好，可以开始识别。')
                else:
                    self.error(value)
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def reformat(self, event=None):
        value = self.output.get('1.0', 'end-1c')
        self.output.delete('1.0', 'end')
        self.output.insert('1.0', to_markdown(value, self.mode.get()))

    def copy(self):
        value = self.output.get('1.0', 'end-1c').strip()
        if not value:
            self.status.set('还没有可复制的结果。')
            return
        self.clipboard_clear()
        self.clipboard_append(value)
        self.status.set('已复制 Markdown。')

    def save(self):
        value = self.output.get('1.0', 'end-1c').strip()
        if not value:
            self.status.set('还没有可保存的结果。')
            return
        path = filedialog.asksaveasfilename(defaultextension='.md', filetypes=[('Markdown', '*.md')])
        if path:
            try:
                Path(path).write_text(value + '\n', encoding='utf-8')
                self.status.set('Markdown 已保存。')
            except Exception as exc:
                self.error(exc)

    def model_manager(self):
        dialog = tk.Toplevel(self)
        dialog.title('本地模型')
        dialog.geometry('590x430')
        dialog.transient(self)
        body = ttk.Frame(dialog, padding=22)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text='选择本地识别模型', font=('Microsoft YaHei UI', 16, 'bold')).pack(anchor='w')
        ttk.Label(body, text='下载需要联网；识别在本机完成，不需要账号或 API key。', wraplength=530).pack(anchor='w', pady=(8, 14))
        for key, model in MODELS.items():
            row = ttk.Frame(body)
            row.pack(fill='x', pady=7)
            ttk.Label(row, text=model['name'], font=('Microsoft YaHei UI', 11, 'bold')).pack(anchor='w')
            ttk.Label(row, text=model['description'], wraplength=520, foreground='#687080').pack(anchor='w', pady=4)
            ttk.Button(row, text='加载检查' if ready(key) else '下载并安装',
                       command=lambda k=key: self.install(k, dialog)).pack(side='left')
            ttk.Button(row, text='项目 / 模型来源', command=lambda url=model['url']: webbrowser.open(url)).pack(side='left', padx=8)
        ttk.Separator(body).pack(fill='x', pady=10)
        ttk.Label(body, text='其他候选：Pix2Text（适合后续扩展图文混排，本程序暂未接入）', wraplength=520).pack(anchor='w')
        ttk.Button(body, text='查看 Pix2Text 开源模型', command=lambda: webbrowser.open('https://github.com/breezedeus/Pix2Text')).pack(anchor='w', pady=5)

    def install(self, key, dialog):
        if self.busy:
            self.status.set('请等待当前任务完成。')
            return
        if not available(key) and not messagebox.askokcancel('下载模型',
            '即将从 PyPI / 模型官方来源下载开源依赖和权重，可能需要数百 MB 至数 GB 空间。继续下载？', parent=dialog):
            return
        dialog.destroy()
        self.model.set(MODELS[key]['name'])
        def work():
            if not available(key):
                python = Path(sys.executable).with_name('python.exe')
                if not python.exists():
                    python = Path(sys.executable)
                with LOG.open('a', encoding='utf-8') as log:
                    completed = subprocess.run([str(python), '-m', 'pip', 'install', MODELS[key]['package'], '-c', str(ROOT / 'constraints.txt')],
                        stdout=log, stderr=subprocess.STDOUT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                if completed.returncode:
                    raise RuntimeError('下载或安装失败，请检查网络后重试。详细信息见 app.log。')
            self.engine.load(key, lambda text: self.events.put(('progress', text)))
        self.run_job(work, 'ready', '正在下载 / 加载模型… 请保持网络连接，详细进度写入 app.log。')

    def error(self, exc):
        logging.error('%s', exc)
        self.status.set('操作失败，可重试。详细信息见 app.log。')
        messagebox.showerror('Math → Markdown', str(exc)[:900])

    def close(self):
        if self.busy:
            messagebox.showinfo('任务进行中', '请等待识别或模型安装完成后再关闭。')
            return
        self.destroy()


if __name__ == '__main__':
    App().mainloop()
