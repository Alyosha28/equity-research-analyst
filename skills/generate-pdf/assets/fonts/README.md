# CJK Fonts for PDF Generation

## Recommended Fonts

For production-quality CJK rendering in PDF reports, install one of:

### Tier 1 (Best — recommended for all platforms)

**Noto Sans CJK SC + Noto Serif CJK SC** (Google)
- Full GB18030 coverage (44,000+ glyphs)
- Actively maintained, battle-tested
- Multiple weights (Thin through Black)
- https://github.com/googlefonts/noto-cjk

Installation:
```bash
# Debian/Ubuntu (recommended)
apt install fonts-noto-cjk

# macOS
brew install font-noto-sans-cjk-sc font-noto-serif-cjk-sc

# Windows
# Download from: https://github.com/googlefonts/noto-cjk/releases
# Install the .otf files via Windows Font Settings
```

**Source Han Sans SC + Source Han Serif SC** (Adobe)
- Nearly identical to Noto CJK (same source)
- https://github.com/adobe-fonts/source-han-sans
- https://github.com/adobe-fonts/source-han-serif

### Tier 2 (System fonts — fallback)

| Platform | Font | Coverage | Quality |
|----------|------|----------|---------|
| Windows | Microsoft YaHei | GB2312 (6,763) | Good for body text |
| Windows | SimSun / SimHei | GB2312 (6,763) | Basic, functional |
| macOS | PingFang SC | GB18030 | Excellent |
| Linux | WenQuanYi Micro Hei | GB18030 | Adequate |

### Why Noto/Source Han are better than system fonts

1. **Full character coverage**: GB18030 (44,000+) vs GB2312 (6,763)
2. **Multiple weights**: Proper bold/light for headings
3. **Multilingual**: Supports SC/TC/JP/KR in one family
4. **Open source**: No licensing concerns
5. **Active maintenance**: Regular updates, Harfbuzz compatible

## Testing Font Availability

```bash
# Check if Noto CJK is installed (Linux)
fc-list | grep -i "noto.*cjk"

# Check if any CJK font is available (cross-platform)
python -c "
import subprocess, sys
try:
    result = subprocess.run(['fc-list', ':lang=zh'], capture_output=True, text=True)
    if result.stdout.strip():
        print('CJK fonts found:')
        print(result.stdout[:500])
    else:
        print('No CJK fonts found via fc-list')
except FileNotFoundError:
    print('fc-list not available (not Linux?)')
"
```

## Bundling Fonts with the Skill

For environments without system CJK fonts (CI, Docker without fonts-noto-cjk):

1. Download Noto Sans CJK SC Regular and Bold:
   https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf
   https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Bold.otf

2. Place them in this directory:
   ```
   assets/fonts/
   ├── NotoSansCJKsc-Regular.otf
   └── NotoSansCJKsc-Bold.otf
   ```

3. Update cjk-overrides.css to use url() references:
   ```css
   @font-face {
     font-family: "CJK Body";
     src: url("../assets/fonts/NotoSansCJKsc-Regular.otf") format("opentype");
   }
   ```

4. Update render_pdf.py to pass the `--cjk-fonts-dir` argument pointing to
   the bundled fonts directory.

**Note:** Bundling fonts increases the skill directory size by ~15-30MB.
The recommended approach is to install system-level CJK fonts instead.

## License

Noto CJK and Source Han CJK are licensed under the SIL Open Font License 1.1.
They can be freely used, distributed, and embedded in PDF documents.
