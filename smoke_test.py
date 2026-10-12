"""Run a real formula through the GUI's background worker, without changing the clipboard."""
import time
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from app import App

app = App()
app.withdraw()
errors = []
try:
    app.error = lambda error: errors.append(str(error))
    with patch('app.ImageGrab.grabclipboard', return_value=Image.open('samples/formula.png')):
        app.paste()
    assert app.source is not None, 'Clipboard image not accepted'
    app.recognize()
    deadline = time.monotonic() + 120
    while app.busy and time.monotonic() < deadline:
        app.update()
        time.sleep(0.02)
    assert not app.busy, 'Inference timeout'
    assert not errors, errors
    result = app.output.get('1.0', 'end-1c')
    assert result.startswith('$$\n') and result.endswith('\n$$'), result
    assert r'\frac' in result and 'x' in result and 'y' in result, result
    app.mode.set('行内公式')
    app.reformat()
    assert app.output.get('1.0', 'end-1c').startswith('$')
    app.mode.set('块公式')
    app.reformat()
    assert app.output.get('1.0', 'end-1c') == result
    copied = []
    app.clipboard_clear = lambda: None
    app.clipboard_append = copied.append
    app.copy()
    assert copied == [result]
    with patch('app.filedialog.asksaveasfilename', return_value='samples/result.md'):
        app.save()
    assert Path('samples/result.md').read_text(encoding='utf-8').strip() == result
    # Transparent screenshots must become white, not black.
    app.set_image(Image.new('RGBA', (10, 10), (0, 0, 0, 0)))
    assert app.source.getpixel((0, 0)) == (255, 255, 255)
    assert not app.output.get('1.0', 'end-1c')
    print('PASS: paste, real OCR, format switching, copy, save, transparency, stale-output clearing')
    print(result)
finally:
    app.destroy()
