from __future__ import annotations

import io
import importlib.util
from pathlib import Path
import tempfile
import os

MODELS = {
    'rapid': {
        'name': 'RapidLaTeXOCR · CPU 推荐',
        'package': 'rapid-latex-ocr==0.0.9',
        'module': 'rapid_latex_ocr',
        'url': 'https://github.com/RapidAI/RapidLaTeXOCR',
        'description': 'ONNX 本地推理，适合印刷体单个公式。首次加载下载模型，CPU 即可运行。',
    },
    'pix2tex': {
        'name': 'pix2tex · LaTeX-OCR',
        'package': 'pix2tex==0.1.4',
        'module': 'pix2tex',
        'url': 'https://github.com/lukas-blecher/LaTeX-OCR',
        'description': 'PyTorch 本地推理。依赖和模型较大，首次加载会下载权重。适合对照识别结果。',
    },
}


def clean_latex(value: str) -> str:
    value = value.strip()
    if value.startswith('```') and value.endswith('```'):
        lines = value.splitlines()
        value = '\n'.join(lines[1:-1]).strip()
    for left, right in [('$$', '$$'), ('\\[', '\\]'), ('\\(', '\\)'), ('$', '$')]:
        if value.startswith(left) and value.endswith(right) and len(value) >= len(left) + len(right):
            return value[len(left):-len(right)].strip()
    return value


def to_markdown(value: str, mode: str) -> str:
    latex = clean_latex(value)
    if not latex:
        return ''
    if mode == '行内公式':
        return '$' + latex + '$'
    if mode == '纯 LaTeX':
        return latex
    return '$$\n' + latex + '\n$$'


def available(key: str) -> bool:
    return importlib.util.find_spec(MODELS[key]['module']) is not None


RAPID_FILES = ('image_resizer.onnx', 'encoder.onnx', 'decoder.onnx', 'tokenizer.json')


def rapid_directory():
    spec = importlib.util.find_spec('rapid_latex_ocr')
    if spec is None:
        raise RuntimeError('请先安装 RapidLaTeXOCR。')
    return Path(spec.origin).parent / 'models'


def ready(key):
    if not available(key):
        return False
    if key == 'rapid':
        return all((rapid_directory() / name).is_file() for name in RAPID_FILES)
    return True


def prepare_rapid(progress=None):
    # Write atomically: an interrupted download must never look like a model.
    import requests
    directory = rapid_directory()
    directory.mkdir(parents=True, exist_ok=True)
    for name in RAPID_FILES:
        target = directory / name
        if target.is_file():
            continue
        url = 'https://github.com/RapidAI/RapidLaTeXOCR/releases/download/v0.0.0/' + name
        temporary = None
        try:
            with requests.get(url, stream=True, timeout=(15, 60)) as response:
                response.raise_for_status()
                total = int(response.headers.get('content-length', 0))
                count = 0
                with tempfile.NamedTemporaryFile(dir=directory, suffix='.part', delete=False) as handle:
                    temporary = Path(handle.name)
                    for chunk in response.iter_content(1024 * 1024):
                        handle.write(chunk)
                        count += len(chunk)
                        if progress:
                            progress(f'正在下载 {name} · {count / 1048576:.1f} / {total / 1048576:.1f} MB')
                if total and count != total:
                    raise RuntimeError('模型下载不完整，请重试。')
                os.replace(temporary, target)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()


class Engine:
    def __init__(self):
        self.models = {}

    def load(self, key: str, progress=None):
        if key not in self.models:
            if key == 'rapid':
                from rapid_latex_ocr import LaTeXOCR
                prepare_rapid(progress)
                directory = rapid_directory()
                self.models[key] = LaTeXOCR(
                    image_resizer_path=directory / 'image_resizer.onnx',
                    encoder_path=directory / 'encoder.onnx',
                    decoder_path=directory / 'decoder.onnx',
                    tokenizer_json=directory / 'tokenizer.json')
            elif key == 'pix2tex':
                from pix2tex.cli import LatexOCR
                self.models[key] = LatexOCR()
            else:
                raise ValueError('未知模型')
        return self.models[key]

    def recognize(self, key, image):
        model = self.load(key)
        if key == 'rapid':
            data = io.BytesIO()
            image.save(data, format='PNG')
            result, _ = model(data.getvalue())
        else:
            result = model(image)
        result = clean_latex(str(result))
        if not result:
            raise RuntimeError('没有识别到公式，请缩小截图范围、提高图片清晰度后重试。')
        return result
