"""Configuración reproducible; no se modifican umbrales usando prueba/validación."""
from dataclasses import dataclass
from pathlib import Path
ROOT = Path(__file__).resolve().parent
SEED = 42
PAIRS = {
    'NWS_NWSA': ('NWS', 'NWSA'),
    'GOOG_GOOGL': ('GOOG', 'GOOGL'),
    'TLT_VGLT': ('TLT', 'VGLT'),
}
JUSTIFICATION = {
    'NWS_NWSA': 'Dos clases de acciones de News Corp; selección inicial favorable.',
    'GOOG_GOOGL': 'Dos clases de Alphabet; rango de Johansen principal no fue 1.',
    'TLT_VGLT': 'ETF Treasury a largo plazo de diferentes duraciones; no superó FDR.',
}
@dataclass(frozen=True)
class Settings:
    start: str = '2014-01-01'
    end: str = '2026-11-05'  # fin exclusivo en yfinance
    initial_capital: float = 1_000_000.0
    max_gross_fraction: float = .80
    fee: float = .00125
    annual_borrow: float = .0025
    entry_z: float = 2.0
    exit_z: float = .5
    stop_z: float = 4.0
    max_hold: int = 45
    kalman_q_hedge: float = 1e-5
    kalman_r_hedge: float = 4.0
    kalman_q_mean: float = 1e-4
    kalman_r_mean: float = .01
    strict_cointegration: bool = False  # False = análisis exploratorio, NO certificación
CFG = Settings()
