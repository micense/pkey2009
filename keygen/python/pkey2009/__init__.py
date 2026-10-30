"""Oracle-free PKEY2009 keygen for Microsoft's 2025-generation products."""

from .keygen import (
    decode,
    encode,
    forge,
    load_catalog,
    load_masks,
    predict_checksum,
    resolve_alias,
)

__all__ = [
    "decode",
    "encode",
    "forge",
    "load_catalog",
    "load_masks",
    "predict_checksum",
    "resolve_alias",
]

__version__ = "1.0.0"
