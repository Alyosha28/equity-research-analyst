# CJK Font Installation Guide

For charts with Chinese, Japanese, or Korean text, you need a CJK-capable font.

## Windows

```powershell
# Option 1: Noto Sans CJK (recommended)
winget install Google.NotoSansCJK

# Option 2: Manual download
# Download from: https://www.google.com/get/noto/help/cjk/
# Install the .ttf files to C:\Windows\Fonts

# Option 3: Use built-in fonts (less coverage)
# Microsoft YaHei, SimHei, DengXian are available by default on most Windows systems.
```

## macOS

```bash
# Option 1: Homebrew (recommended)
brew install --cask font-noto-sans-cjk-sc

# Option 2: Built-in fonts
# PingFang SC and Hiragino Sans GB are available by default on macOS.
```

## Linux (Debian/Ubuntu)

```bash
# Option 1: APT (recommended)
sudo apt install fonts-noto-cjk

# Option 2: WenQuanYi (lightweight alternative)
sudo apt install fonts-wqy-microhei fonts-wqy-zenhei

# Clear font cache after install
fc-cache -fv
```

## Linux (RHEL/Fedora)

```bash
sudo dnf install google-noto-sans-cjk-sc-fonts
```

## Verification

Run this Python snippet to check what CJK fonts matplotlib can see:

```python
import matplotlib.font_manager as fm
fonts = {f.name for f in fm.fontManager.ttflist}
cjk_candidates = [
    "Noto Sans SC", "Noto Sans CJK SC", "Microsoft YaHei",
    "SimHei", "PingFang SC", "WenQuanYi Micro Hei"
]
for f in cjk_candidates:
    status = "FOUND" if f in fonts else "missing"
    print(f"  {f}: {status}")
```

If no CJK font is found, CJK characters will render as tofu boxes (□).
This is acceptable for internal drafts but not for client-facing reports.
