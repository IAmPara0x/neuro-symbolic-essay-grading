"""Transparent calibration of the fuzzy grade to the human mark scale (Lever 4).

Centroid defuzzification compresses the output range, so raw fuzzy grades sit
below a corpus whose human mean is high. A single monotone calibration map fixes
this without any network training. We fit both an affine map and an isotonic
(monotone, non-parametric) map and keep whichever gives lower error.

The map is fit once (see eval/fit_calibration.py) and stored as JSON; the grader
applies it if config.APPLY_CALIBRATION and the file exists. Pearson is unchanged
by any monotone map, so calibration only affects absolute scores (RMSE), not
ranking.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from . import config

try:
    from sklearn.isotonic import IsotonicRegression
    _HAS_ISO = True
except Exception:
    _HAS_ISO = False


def fit(raw: np.ndarray, human: np.ndarray) -> dict:
    """Fit affine and isotonic maps; return a serialisable params dict."""
    raw = np.asarray(raw, float)
    human = np.asarray(human, float)
    slope, intercept = np.polyfit(raw, human, 1)
    params: dict = {
        "affine": {"slope": float(slope), "intercept": float(intercept)},
    }
    if _HAS_ISO:
        iso = IsotonicRegression(y_min=config.SCORE_MIN, y_max=config.SCORE_MAX,
                                 out_of_bounds="clip").fit(raw, human)
        # store as a lookup table over the grade universe for portability
        xs = np.linspace(config.SCORE_MIN, config.SCORE_MAX, 101)
        ys = iso.predict(xs)
        params["isotonic"] = {"x": xs.tolist(), "y": ys.tolist()}
    return params


def _rmse(pred, true):
    return float(np.sqrt(np.mean((np.asarray(pred) - np.asarray(true)) ** 2)))


def choose_method(params: dict, raw: np.ndarray, human: np.ndarray) -> str:
    """Pick the map with lower RMSE on the given (validation) data."""
    cand = ["affine"] + (["isotonic"] if "isotonic" in params else [])
    best, best_err = "affine", float("inf")
    for m in cand:
        err = _rmse(apply(raw, params, method=m), human)
        if err < best_err:
            best, best_err = m, err
    return best


def apply(grade, params: dict, method: str | None = None):
    """Apply the calibration map to a scalar or array of raw grades."""
    method = method or params.get("method", "affine")
    arr = np.asarray(grade, float)
    if method == "isotonic" and "isotonic" in params:
        out = np.interp(arr, params["isotonic"]["x"], params["isotonic"]["y"])
    else:
        a = params["affine"]
        out = a["slope"] * arr + a["intercept"]
    out = np.clip(out, config.SCORE_MIN, config.SCORE_MAX)
    return float(out) if np.isscalar(grade) or arr.ndim == 0 else out


def save(params: dict, path: Path | None = None) -> None:
    path = Path(path) if path else config.CALIBRATION_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(params, indent=2))


def load(path: Path | None = None) -> dict | None:
    path = Path(path) if path else config.CALIBRATION_PATH
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None
