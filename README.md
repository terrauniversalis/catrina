# Catrina Engine vFinal+ (Discrete Visual Alignment Engine)

Catrina Engine vFinal+ genera **tablas visualmente alineadas** en **fuentes proporcionales** (Twitter/X, WhatsApp, etc.) usando:

- Modelo aproximado de **ancho visual**
- Optimización discreta de padding (`best_fill`)
- **Grapheme clusters** (manejo correcto de emojis compuestos)
- **PlatformProfile** por plataforma
- **Calibración humana** (pack A–I) y **auto‑calibración por visión** (screenshot)

## Instalación

```bash
pip install -r requirements.txt
```

> Para máxima precisión de graphemes se recomienda `regex`:
> 
> ```bash
> pip install regex
> ```

## Uso rápido (tablas)

```python
from src.catrina_engine import PlatformProfile, CatrinaEngine

rows = [
  ("BITCOIN", "$1.85T", "+4.2% 📈"),
  ("ETHEREUM", "$412B", "+2.9% 📈"),
  ("SOLANA", "$142B", "+13.5% 📈"),
  ("XRP", "$82B", "-1.1% 📉"),
]

p = PlatformProfile(name="X_WEB")
eng = CatrinaEngine(p)
print("\n".join(eng.format_table(rows, anchor_text="XRP::::::::::::")))
```

## Calibración visual (A–I)

```python
from src.catrina_engine import PlatformProfile
from src.catrina_engine import calibration_pack, pick_candidate, refine_pack

base = PlatformProfile(name="X_WEB")
print(calibration_pack(rows, base_profile=base, anchor_text="XRP::::::::::::"))
# pega en X/WhatsApp, elige letra
chosen = pick_candidate(base, "E")
print(refine_pack(rows, chosen))
print(chosen.to_json())
```

## Auto‑calibración por visión (screenshot)

1) Genera la tabla y pégala en la plataforma.
2) Toma screenshot (sin zoom raro, sin selección azul)
3) Corre:

```python
import cv2
from src.catrina_engine import PlatformProfile, CatrinaEngine
from src.catrina_autocalibrate import auto_calibrate_from_image

img = cv2.imread('screenshot.png')
base = PlatformProfile(name='X_WEB')
eng = CatrinaEngine(base)
eng = auto_calibrate_from_image(eng, img, steps=4, lr=0.35)
print(eng.p.to_json())
```

## Documentación
- `docs/WHITEPAPER.md` — Especificación y fundamentos.

## Licencia
MIT (ver `LICENSE`).
