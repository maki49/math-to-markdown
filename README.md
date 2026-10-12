# Math → Markdown

极简 Windows 桌面公式识别工具。截图 → 本地识别 → Markdown。

## 启动

双击 **`MathToMarkdown.exe`** 启动（无终端窗口）。也可以使用 `启动.vbs` 或 `start.cmd`（显示诊断信息）。
首次在新机器使用时先运行 `setup.cmd`，需要联网和可用的 Python / pip。
项目使用独立的 Python 3.12 运行环境，不依赖系统 Python 的版本。
请保留整个目录；当前版本是源码 + 本地运行环境，EXE 是轻量启动器，不是独立可分发的单文件包。
移动目录后需要重新创建虚拟环境。

## 使用

1. 按 **Win + Shift + S**，尽量只截取一个清晰的公式。
2. 回到窗口按 **Ctrl + V**，或点击“打开图片”。
3. 点击“识别公式”（**Ctrl + Enter**）。
4. 选择块公式、行内公式或纯 LaTeX，检查并修改结果。
5. 点击“复制 Markdown”，粘贴到 Typora 等支持数学公式的编辑器；也可以保存 `.md`。

结果编辑框支持普通文本粘贴。加载新图片会清空旧结果，避免误复制。
识别在后台线程中运行，不阻塞窗口；请等待正在进行的任务结束再关闭。
普通 Markdown 本身不规定数学公式语法，需要编辑器支持 `$...$` / `$$...$$`。

## 开源模型

| 模型 | 程序内状态 | 用途与下载 |
| --- | --- | --- |
| [RapidLaTeXOCR](https://github.com/RapidAI/RapidLaTeXOCR) | 默认接入，CPU 推理 | ONNX 格式，适合印刷体单个公式；模型管理中加载检查 |
| [pix2tex / LaTeX-OCR](https://github.com/lukas-blecher/LaTeX-OCR) | 可选接入，按需安装 | PyTorch 依赖较大，模型管理中下载；首次加载下载权重 |
| [Pix2Text](https://github.com/breezedeus/Pix2Text) | 候选链接，暂未接入 | 面向图文混排等更大范围需求，可从官方项目下载开源模型 |

无需 API key。模型和依赖下载需要联网，截图只传给本机模型。
模型项目的许可与权重许可应以各自来源为准。
程序不是整页文档 OCR；手写、模糊、复杂多行公式可能有误，请核对上下标、括号及符号。

## 开发和检查

- `app.py`：Tkinter 界面、剪贴板、后台识别、模型管理。
- `core.py`：模型适配和 Markdown 格式转换。
- `requirements.txt`：默认后端依赖。
- `.venv312\Scripts\python.exe -m unittest -v`：格式转换测试。
- `.venv312\Scripts\python.exe smoke_test.py`：GUI 与真实模型冒烟检查。
- `app.log`：错误与模型安装日志。

下载失败时请检查网络后重试。不要将账号或 token 填入本程序。

测试图片 `samples/formula.png` 来自 RapidLaTeXOCR 官方仓库的 `tests/test_files/6.png`，仅用于验证。
