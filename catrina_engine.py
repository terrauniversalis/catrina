from __future__ import annotations

from dataclasses import dataclass, field, asdict
from math import floor
from typing import Dict, List, Optional, Tuple
import json
import re
import unicodedata

# --------------------
# Grapheme clusters
# --------------------
# Prefer: third-party 'regex' module for \X. Fallback is best-effort.

def iter_graphemes(text: str) -> List[str]:
    try:
        import regex  # type: ignore
        return regex.findall(r"\X", text)
    except Exception:
        clusters: List[str] = []
        i, n = 0, len(text)

        def is_combining(ch: str) -> bool:
            return unicodedata.combining(ch) != 0

        def is_ri(ch: str) -> bool:
            o = ord(ch)
            return 0x1F1E6 <= o <= 0x1F1FF

        while i < n:
            g = text[i]
            i += 1
            while i < n and is_combining(text[i]):
                g += text[i]
                i += 1
            while i < n and ord(text[i]) in (0xFE0F, 0xFE0E):
                g += text[i]
                i += 1
            while i < n and ord(text[i]) == 0x200D:
                g += text[i]
                i += 1
                if i < n:
                    g += text[i]
                    i += 1
                    while i < n and is_combining(text[i]):
                        g += text[i]
                        i += 1
                    while i < n and ord(text[i]) in (0xFE0F, 0xFE0E):
                        g += text[i]
                        i += 1
            if len(g) == 1 and is_ri(g) and i < n and is_ri(text[i]):
                g += text[i]
                i += 1
            clusters.append(g)
        return clusters


def is_emoji_grapheme(g: str) -> bool:
    for ch in g:
        o = ord(ch)
        if o in (0x200D, 0xFE0F):
            return True
        if 0x1F300 <= o <= 0x1FAFF:
            return True
        if 0x2600 <= o <= 0x27BF:
            return True
    return False


@dataclass
class PlatformProfile:
    name: str = "CUSTOM"
    separator: str = " | "

    colon_width: float = 3.6
    dot_width: float = 0.6
    space_width: float = 3.4
    emoji_width: float = 16.0

    left_target_width: Optional[float] = None
    left_target_offset: float = 0.0

    char_widths: Dict[str, float] = field(default_factory=lambda: {
        ":": 3.6,
        ".": 0.6,
        " ": 3.4,
        "|": 2.5,
        "I": 4.5,
        "L": 5.0,
        "T": 7.0,
        "R": 8.0,
        "A": 8.0,
        "N": 8.0,
        "S": 8.0,
        "E": 8.0,
        "O": 8.0,
        "U": 8.0,
        "D": 8.0,
        "P": 8.0,
        "G": 9.0,
        "$": 7.0,
        "+": 7.0,
        "-": 7.0,
        "%": 7.0,
        "0": 8.0,
        "1": 6.5,
        "2": 8.0,
        "3": 8.0,
        "4": 8.0,
        "5": 8.0,
        "6": 8.0,
        "7": 8.0,
        "8": 8.0,
        "9": 8.0,
        "B": 8.0,
        "M": 9.0,
        "K": 8.0,
        "H": 8.0,
        "X": 8.0,
        "C": 8.0,
        "Y": 8.0,
        ",": 3.0,
    })

    default_char_width: float = 8.0
    kerning_pairs: Dict[str, float] = field(default_factory=dict)

    enable_thin_space: bool = False
    thin_space_char: str = "\u2009"
    thin_space_width: float = 1.6

    over_penalty: float = 15.0
    quantize_step: Optional[float] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @staticmethod
    def from_json(s: str) -> "PlatformProfile":
        return PlatformProfile(**json.loads(s))


class CatrinaEngine:
    def __init__(self, profile: Optional[PlatformProfile] = None) -> None:
        self.p = profile or PlatformProfile()

    def _q(self, x: float) -> float:
        if self.p.quantize_step is None:
            return x
        step = self.p.quantize_step
        return round(x / step) * step

    def grapheme_width(self, g: str) -> float:
        if is_emoji_grapheme(g):
            return self.p.emoji_width
        if self.p.enable_thin_space and g == self.p.thin_space_char:
            return self.p.thin_space_width
        if len(g) == 1:
            return self.p.char_widths.get(g, self.p.default_char_width)
        w = 0.0
        prev = ""
        for ch in g:
            w += self.p.char_widths.get(ch, self.p.default_char_width)
            if prev:
                w += self.p.kerning_pairs.get(prev + ch, 0.0)
            prev = ch
        return w

    def visual_width(self, text: str) -> float:
        total = 0.0
        prev_last = ""
        for g in iter_graphemes(text):
            total += self.grapheme_width(g)
            if prev_last and g:
                total += self.p.kerning_pairs.get(prev_last + g[0], 0.0)
            prev_last = g[-1] if g else prev_last
        return self._q(total)

    def best_fill(self, delta: float, units: List[Tuple[str, float]], max_counts: List[int],
                  prefer_not_over: bool = True) -> str:
        delta = self._q(delta)
        if delta <= 0:
            return ""

        if len(units) == 1:
            ch, w = units[0]
            if w <= 0:
                return ""
            n0 = max(0, min(max_counts[0], int(floor(delta / w))))
            n1 = max(0, min(max_counts[0], n0 + 1))

            def score(n: int) -> float:
                width = n * w
                err = abs(delta - width)
                over = width - delta
                return err + (self.p.over_penalty if (prefer_not_over and over > 0) else 0.0)

            return ch * (n0 if score(n0) <= score(n1) else n1)

        (ch0, w0), (ch1, w1) = units[0], units[1]
        max0, max1 = max_counts[0], max_counts[1]
        if w0 <= 0 or w1 <= 0:
            return ""

        n0_base = int(round(delta / w0))
        start = max(0, min(max0, n0_base - 5))
        end = max(0, min(max0, n0_base + 5))

        best_s = ""
        best_score = float("inf")
        for n0 in range(start, end + 1):
            width0 = n0 * w0
            residual = max(0.0, delta - width0)
            n1_base = int(round(residual / w1))
            for n1 in range(max(0, n1_base - 8), min(max1, n1_base + 8) + 1):
                width = width0 + n1 * w1
                err = abs(delta - width)
                over = width - delta
                score = err + (self.p.over_penalty if (prefer_not_over and over > 0) else 0.0)
                if score < best_score:
                    best_score = score
                    best_s = (ch0 * n0) + (ch1 * n1)
        return best_s

    def infer_targets(self, rows: List[Tuple[str, str, Optional[str]]], anchor_text: Optional[str] = None) -> Tuple[float, float, float]:
        max_name = max(self.visual_width(n) for n, _, _ in rows)
        max_val = max(self.visual_width(v) for _, v, _ in rows)
        max_chg = max(self.visual_width(c) for _, _, c in rows if c) if any(c for *_, c in rows) else 0.0

        if self.p.left_target_width is not None:
            left_target = self.p.left_target_width
        else:
            if anchor_text:
                left_target = max(max_name, self.visual_width(anchor_text))
            else:
                left_target = max_name

        left_target = self._q(left_target + self.p.left_target_offset)
        return left_target, max_val, max_chg

    def left_block(self, name: str, left_target: float) -> str:
        delta = left_target - self.visual_width(name)
        fill = self.best_fill(delta, units=[(":", self.p.colon_width), (".", self.p.dot_width)], max_counts=[220, 80])
        return f"{name}{fill}"

    def right_align_value(self, value: str, value_target: float) -> str:
        delta = value_target - self.visual_width(value)
        if delta <= 0:
            return value

        if self.p.enable_thin_space:
            units = [(" ", self.p.space_width), (self.p.thin_space_char, self.p.thin_space_width)]
            maxc = [400, 80]
        else:
            units = [(" ", self.p.space_width)]
            maxc = [500]

        fill = self.best_fill(delta, units=units, max_counts=maxc)
        return f"{fill}{value}"

    def make_line(self, name: str, value: str, change: Optional[str], left_target: float, value_target: float, change_target: Optional[float] = None) -> str:
        left = self.left_block(name, left_target)
        val = self.right_align_value(value, value_target)

        if not change:
            return f"{left}{self.p.separator}{val}"

        if change_target:
            chg = self.right_align_value(change, change_target)
        else:
            chg = change
        return f"{left}{self.p.separator}{val}{self.p.separator}{chg}"

    def format_table(self, rows: List[Tuple[str, str, Optional[str]]], anchor_text: Optional[str] = None, align_change: bool = False) -> List[str]:
        left_t, val_t, chg_t = self.infer_targets(rows, anchor_text=anchor_text)
        if not align_change:
            chg_t = 0.0
        out = []
        for n, v, c in rows:
            out.append(self.make_line(n, v, c, left_t, val_t, chg_t if align_change else None))
        return out


# -------------------- Calibration Pack --------------------

def generate_candidate_profiles(base: PlatformProfile, mode: str = "grid") -> List[PlatformProfile]:
    candidates: List[PlatformProfile] = []
    tweaks = [
        (-0.20, -0.20, -2.0, -0.3, -0.3),
        (-0.20,  0.00,  0.0, -0.3,  0.0),
        (-0.20, +0.20, +2.0, -0.3, +0.3),
        ( 0.00, -0.20, -2.0,  0.0, -0.3),
        ( 0.00,  0.00,  0.0,  0.0,  0.0),
        ( 0.00, +0.20, +2.0,  0.0, +0.3),
        (+0.20, -0.20, -2.0, +0.3, -0.3),
        (+0.20,  0.00,  0.0, +0.3,  0.0),
        (+0.20, +0.20, +2.0, +0.3, +0.3),
    ]

    for i, (dc, ds, de, dp, dlo) in enumerate(tweaks):
        p = PlatformProfile(**asdict(base))
        p.name = f"{base.name}_{mode.upper()}_{i}"
        p.colon_width = max(0.1, base.colon_width + dc)
        p.space_width = max(0.1, base.space_width + ds)
        p.emoji_width = max(6.0, base.emoji_width + de)
        pipe = p.char_widths.get("|", 2.5)
        p.char_widths["|"] = max(0.5, pipe + dp)
        p.left_target_offset = base.left_target_offset + dlo
        candidates.append(p)

    return candidates


def calibration_pack(rows: List[Tuple[str, str, Optional[str]]], base_profile: Optional[PlatformProfile] = None,
                     anchor_text: Optional[str] = "XRP::::::::::::", align_change: bool = False,
                     title: str = "CATrina vFinal+ :: CALIBRACIÓN VISUAL") -> str:
    base = base_profile or PlatformProfile(name="CUSTOM")
    cands = generate_candidate_profiles(base, mode="grid")
    labels = "ABCDEFGHI"

    out: List[str] = []
    out.append(f"=== {title} ===")
    out.append("Pega este bloque en la plataforma destino y elige la etiqueta más recta.\n")

    for idx, prof in enumerate(cands[:9]):
        eng = CatrinaEngine(prof)
        lines = eng.format_table(rows, anchor_text=anchor_text, align_change=align_change)
        out.append(f"[{labels[idx]}] colon={prof.colon_width:.2f} space={prof.space_width:.2f} emoji={prof.emoji_width:.1f} pipe={prof.char_widths.get('|',2.5):.2f} Loff={prof.left_target_offset:+.2f}")
        out.extend(lines)
        out.append("")

    out.append("=== Fin calibración ===")
    return "\n".join(out)


def pick_candidate(base: PlatformProfile, choice_label: str) -> PlatformProfile:
    labels = "ABCDEFGHI"
    idx = labels.find(choice_label.strip().upper())
    if idx < 0:
        return base
    return generate_candidate_profiles(base, mode="grid")[idx]


def refine_pack(rows: List[Tuple[str, str, Optional[str]]], chosen: PlatformProfile,
                anchor_text: Optional[str] = "XRP::::::::::::", align_change: bool = False) -> str:
    return calibration_pack(rows, base_profile=chosen, anchor_text=anchor_text,
                            align_change=align_change,
                            title="CATrina vFinal+ :: REFINAMIENTO (adaptive)")
