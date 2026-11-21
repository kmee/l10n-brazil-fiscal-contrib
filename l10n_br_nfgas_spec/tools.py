# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from pathlib import Path

SCHEMA_DIR = Path(__file__).parent / "schemas" / "v1_0"


def schema_path(file_name="nfgas_v1.00.xsd"):
    """Path of one of the official NFGas xsd files shipped with the module."""
    return str(SCHEMA_DIR / file_name)
