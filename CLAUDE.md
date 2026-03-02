# CLAUDE.md — akrocansim

## Project Overview

**akrocansim** is a Python desktop GUI application for simulating J1939 CAN bus controllers. It lets users configure PGNs/SPNs from the SAE J1939 Digital Annex and transmit CAN messages over a hardware or virtual CAN interface.

- **Language:** Python 3.13+
- **GUI framework:** DearPyGUI 2.0.0
- **CAN library:** python-can 4.5.0
- **Package manager:** `uv` (preferred over pip)
- **Build backend:** hatchling
- **Current version:** 0.6.5

---

## Project Structure

```
src/akrocansim/
├── __init__.py       # Entry point, main() calls gui.AkrocansimGui()
├── gui.py            # DearPyGUI application window
├── config.py         # TOML config management & CAN bus setup
├── transmitter.py    # J1939 PGN transmission via CAN bus
├── J1939DA.py        # Parses SAE J1939 Digital Annex Excel files
├── dbc.py            # Generates Vector CANdb++ DBC files
├── signaltools.py    # Signal encode/decode utilities
├── version_check.py  # PyPI version checker
└── resources/        # Bundled icon and logo assets
tests/
└── test_protocols.py # Unit tests for encode/decode
```

---

## Common Commands

```bash
# Run the application (after installing)
uv tool install akrocansim
akrocansim

# Run from source
uv run python -m akrocansim

# Run tests
uv run pytest tests/

# Build the package
uv build

# Build a standalone Windows executable
build_exe.bat
```

---

## Architecture

- **Config** (`config.py`): Loads `~/akrocansim/config.toml`, parses J1939DA Excel to pickle cache, manages CAN interface connection.
- **Transmitter** (`transmitter.py`): Manages per-PGN daemon threads for periodic CAN message transmission; three global modes: stop / continuous / per-PGN.
- **GUI** (`gui.py`): DearPyGUI window with menus, dashboard, and signal editors (sliders, dropdowns, raw inputs). Callback-driven.
- **J1939DA** (`J1939DA.py`): Parses the SAE J1939 Digital Annex Excel file; outputs pickle (fast load) and JSON (inspection). Contains known SPN edge cases.
- **signaltools** (`signaltools.py`): `encode()`, `decode()`, `start_bit()`, `raw_min/max_value()`, `get_label()`.

---

## Configuration

User config lives at `~/akrocansim/config.toml`. A default template is written on first run. Key sections:

- `[CAN_INTERFACE]` — interface type, channel, bitrate
- `[J1939DA]` — path to J1939 Digital Annex Excel file, column name mappings
- `[Tx_PGNs_SPNs]` — PGNs and SPNs to transmit

---

## Publishing / CI

- GitHub Actions (`.github/workflows/python-publish.yml`) publishes to PyPI on `v*` tags using `uv build` + `uv publish` with OIDC trusted publishing.
- Bump `version` in `pyproject.toml` and `src/akrocansim/__init__.py` before tagging.

---

## Known Issues / Notes

- J1939DA parser has known edge cases for SPNs: 7585, 6973, 3192, 900, 899, 927, 7716, 2928.
- DearPyGUI is pinned to `2.0.0` — API changes between versions are breaking.
- Python 3.13+ required; uses `match`/`case` statements.
- Windows is the primary platform; Linux is supported but executable build is Windows-only.
