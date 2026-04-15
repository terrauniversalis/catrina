from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np
import cv2

# Requiere: PlatformProfile/CatrinaEngine en el mismo paquete


@dataclass
class DriftSample:
    line_idx: int
    pipe1_x: float
    pipe_width: float


def _auto_crop_table(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY_INV, 31, 10)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5))
    blob = cv2.morphologyEx(thr, cv2.MORPH_CLOSE, k)
    cnts, _ = cv2.findContours(blob, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return img
    x, y, w, h = cv2.boundingRect(max(cnts, key=cv2.contourArea))
    pad = 20
    return img[max(0, y-pad):y+h+pad, max(0, x-pad):x+w+pad]


def _binarize(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY_INV, 31, 10)


def _extract_vertical_mask(bin_img: np.ndarray) -> np.ndarray:
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 14))
    return cv2.morphologyEx(bin_img, cv2.MORPH_OPEN, kernel)


def _find_line_spans(bin_img: np.ndarray, min_h: int = 14) -> List[Tuple[int, int]]:
    proj = np.sum(bin_img, axis=1)
    spans: List[Tuple[int, int]] = []
    in_line = False
    y0 = 0
    for i, v in enumerate(proj):
        if v > 0 and not in_line:
            in_line = True
            y0 = i
        elif v == 0 and in_line:
            in_line = False
            if i - y0 >= min_h:
                spans.append((y0, i))
    if in_line and (len(proj) - y0) >= min_h:
        spans.append((y0, len(proj)))
    return spans


def _find_pipes_in_line(vertical_line: np.ndarray) -> List[Tuple[float, float, float]]:
    cnts, _ = cv2.findContours(vertical_line, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    H, W = vertical_line.shape[:2]
    out: List[Tuple[float, float, float]] = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        if h < 10 or w <= 0:
            continue
        ratio = w / float(h)
        if ratio < 0.35 and w < 12:
            xc = x + w / 2.0
            if 0.10 * W <= xc <= 0.90 * W:
                out.append((float(xc), float(w), float(h)))
    return out


def measure_pipe_positions(image_bgr: np.ndarray) -> List[DriftSample]:
    img = _auto_crop_table(image_bgr)
    bin_img = _binarize(img)
    vertical = _extract_vertical_mask(bin_img)
    spans = _find_line_spans(vertical)

    samples: List[DriftSample] = []
    for idx, (y0, y1) in enumerate(spans):
        vline = vertical[y0:y1, :]
        pipes = _find_pipes_in_line(vline)
        if not pipes:
            continue
        xc, w, _h = min(pipes, key=lambda t: t[0])
        samples.append(DriftSample(line_idx=idx, pipe1_x=xc, pipe_width=w))
    return samples


def update_profile_from_pixels(profile, errors_px: np.ndarray, pipe_width_px: float,
                               lr: float = 0.35, converge_thresh: float = 0.25):
    median_err_px = float(np.median(errors_px))
    if abs(median_err_px) < float(pipe_width_px) * float(converge_thresh):
        return profile

    pipe_vu = max(0.2, float(profile.char_widths.get("|", 2.5)))
    px_per_vu = float(pipe_width_px) / pipe_vu
    if px_per_vu < 0.1:
        return profile

    median_err_vu = median_err_px / px_per_vu
    step = lr * float(np.clip(median_err_vu, -2.0, 2.0))
    profile.left_target_offset = float(profile.left_target_offset + step)
    profile.left_target_offset = float(np.clip(profile.left_target_offset, -20.0, 20.0))
    return profile


def auto_calibrate_from_image(engine, image_bgr: np.ndarray, steps: int = 4, lr: float = 0.35, verbose: bool = True):
    prof = engine.p
    for it in range(steps):
        samples = measure_pipe_positions(image_bgr)
        if len(samples) < 2:
            if verbose:
                print(f"⚠️ Pipes insuficientes detectados: {len(samples)}")
            break

        xs = np.array([s.pipe1_x for s in samples], dtype=float)
        target_x = float(np.median(xs))
        errors = target_x - xs
        pipe_w = float(np.median([s.pipe_width for s in samples]))

        if verbose:
            print(f"Iter {it+1}: median_err={float(np.median(errors)):+.2f}px | pipe_w≈{pipe_w:.1f}px | offset={prof.left_target_offset:+.3f}")

        prof = update_profile_from_pixels(prof, errors, pipe_w, lr=lr, converge_thresh=0.25)

        if abs(float(np.median(errors))) < pipe_w * 0.25:
            if verbose:
                print("✅ Convergió (drift bajo).")
            break

    engine.p = prof
    return engine
