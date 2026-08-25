"""
Helpers for parsing and validating user-uploaded CSV datasets used as the
basis for bootstrap-distribution Monte Carlo simulations.
"""
from __future__ import annotations

import io
import pandas as pd
import numpy as np

from config import Config


class DatasetError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def parse_uploaded_csv(file_bytes: bytes) -> tuple[pd.DataFrame, np.ndarray]:
    """
    Parse an uploaded CSV of historical prices (or returns) into a DataFrame
    and a 1D ndarray of daily log returns suitable for bootstrap sampling.

    Expected format: a single numeric column of prices, OR a column literally
    named "return"/"returns" containing already-computed simple returns.
    Extra columns (e.g. a date column) are ignored as long as at least one
    numeric column is present.
    """
    if len(file_bytes) > Config.MAX_UPLOAD_BYTES:
        raise DatasetError(f"File is too large (max {Config.MAX_UPLOAD_BYTES // 1024} KB).")

    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as exc:
        raise DatasetError(f"Could not parse file as CSV: {exc}") from exc

    if df.empty:
        raise DatasetError("The uploaded file has no rows.")

    if len(df) > Config.MAX_UPLOAD_ROWS:
        raise DatasetError(f"The uploaded file has too many rows (max {Config.MAX_UPLOAD_ROWS:,}).")

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        raise DatasetError("No numeric column found in the uploaded file.")

    return_col = next((c for c in df.columns if c.strip().lower() in ("return", "returns", "log_return", "log_returns")), None)

    if return_col is not None:
        returns = df[return_col].dropna().to_numpy(dtype=np.float64)
        if len(returns) < 30:
            raise DatasetError("Need at least 30 non-missing return observations.")
        return df, returns

    # Otherwise treat the first numeric column as a price series.
    price_col = numeric_cols[0]
    prices = df[price_col].dropna().to_numpy(dtype=np.float64)
    prices = prices[prices > 0]
    if len(prices) < 31:
        raise DatasetError("Need at least 31 positive price observations to derive 30+ returns.")

    log_returns = np.diff(np.log(prices))
    return df, log_returns
