# CLAUDE.md -- akrocansim

## 1. Project Overview

akrocansim is a desktop GUI application that simulates SAE J1939 CAN bus controllers. It allows automotive/embedded engineers to parse the SAE J1939 Digital Annex (a proprietary Excel spreadsheet defining PGN and SPN standards), configure which Parameter Group Numbers (PGNs) and Suspect Parameter Numbers (SPNs) to transmit, and then send those CAN messages over any hardware CAN interface supported by the python-can library. The GUI provides real-time signal editing with sliders, dropdown selectors, and raw value inputs so that engineers can dynamically adjust signal values and observe the effects on the CAN bus.

**License:** MIT (Copyright 2023 cfsok / Socrates Vlassis)
**Current version:** 0.6.5
**PyPI:** https://pypi.org/project/akrocansim/
**Repository:** https://github.com/cfsok/akrocansim (also referenced as pullthebox/akrocansim)

---

## 2. Tech Stack and Dependencies

| Component | Technology | Version |
|---|---|---|
| Language | Python | >= 3.13 (uses `match`/`case` syntax) |
| GUI framework | DearPyGui | 2.0.0 (pinned) |
| CAN bus library | python-can | 4.5.0 (pinned) |
| Excel parsing | openpyxl | 3.1.5 (pinned) |
| Version comparison | semver | 3.0.4 (pinned) |
| Build backend | hatchling | (build-time only) |
| Package manager | uv | (recommended tooling) |
| Config format | TOML | via stdlib `tomllib` |
| Serialization | pickle, json | stdlib |

All runtime dependencies are pinned to exact versions in `pyproject.toml`. The lockfile `uv.lock` captures the full resolved dependency tree including transitive dependencies (et-xmlfile, msgpack, packaging, typing-extensions, wrapt).

---

## 3. Project Structure

```
akrocansim/
├── .github/
│   └── workflows/
│       └── python-publish.yml      # CI/CD: publish to PyPI on v* tags
├── .claude/
│   └── settings.local.json         # Claude Code local permissions
├── docs/
│   └── images/                     # Demo screenshots for README
│       ├── demo_1_Akrocansim.png
│       ├── demo_1_PCAN-View.png
│       └── demo_2_Akrocansim.png
├── src/
│   └── akrocansim/
│       ├── __init__.py             # Package entry point, version string, main()
│       ├── gui.py                  # DearPyGui GUI: menus, dashboard, signal widgets (372 lines)
│       ├── config.py               # Config loading, CAN connection, J1939DA orchestration (203 lines)
│       ├── transmitter.py          # Threaded per-PGN CAN message transmission (119 lines)
│       ├── J1939DA.py              # J1939 Digital Annex Excel parser (646 lines)
│       ├── dbc.py                  # Vector CANdb++ DBC file generator (184 lines)
│       ├── signaltools.py          # Signal encode/decode/label utilities (27 lines)
│       ├── version_check.py        # Queries PyPI for latest version (19 lines)
│       └── resources/
│           ├── akrocansim.ico      # Application icon
│           └── akrocansim_logo_dark.png  # Logo for About dialog
├── tests/
│   └── test_protocols.py           # Unit tests for encode/decode functions
├── pyproject.toml                  # Project metadata, dependencies, build config
├── uv.lock                         # Dependency lockfile
├── build_exe.bat                   # PyInstaller script for Windows standalone exe
├── .python-version                 # Specifies Python 3.13
├── .gitignore
├── LICENSE                         # MIT License
├── README.md
└── CLAUDE.md                       # This file
```

Total source: approximately 1,579 lines of Python across 8 modules.

---

## 4. How to Install, Run, Test, and Build

### Install as a tool (end users)
```bash
# Requires uv: https://docs.astral.sh/uv/getting-started/installation/
uv tool install akrocansim
```

### Run
```bash
# After tool install
akrocansim

# From source (development)
uv run python -m akrocansim
# Or equivalently, since the entry point calls gui.AkrocansimGui():
uv run akrocansim
```

### Test
```bash
uv run pytest tests/
```

Note: The test file `tests/test_protocols.py` uses an import path `from .. src.akrocansim.protocols.protocols import decode, encode` which does not match the current source layout (it should be `from akrocansim.signaltools import decode, encode`). Tests may not pass without fixing this import.

### Build distribution
```bash
uv build
```
This uses hatchling as the build backend and produces sdist and wheel artifacts in `dist/`.

### Build standalone Windows executable
```bat
build_exe.bat
```
Uses PyInstaller to bundle the application as a single-file Windows executable with embedded icon and logo resources. This is Windows-only.

---

## 5. Architecture and Module Relationships

### Data Flow

```
J1939 Digital Annex (.xlsx)
        |
        v
  J1939DA.py (parse_J1939DA)
        |
        +---> .pkl pickle cache (fast reload)
        +---> .json files (human-inspectable debug output)
        |
        v
  config.py (Config.load)
        |
        +---> Reads config.toml for CAN interface params and PGN/SPN selection
        +---> Loads pickle into Config.J1939_spec
        +---> Validates requested PGNs/SPNs against parsed data
        |
        v
  gui.py (AkrocansimGui)
        |
        +---> Creates DearPyGui viewport, menus, log window
        +---> Instantiates Transmitter
        +---> Builds per-PGN signal editing dashboard
        |       (sliders for continuous signals, combos for discrete/ENUM signals)
        +---> User interactions update signal values via signaltools and transmitter
        |
        v
  transmitter.py (Transmitter)
        |
        +---> One daemon thread per registered PGN
        +---> Threads sleep for the configured tx rate, then send if mode allows
        +---> Three global modes: Stop All / Tx All (continuous) / Use PGN Settings
        +---> Per-PGN modes: continuous or one-shot
        +---> Sends CAN messages via python-can Bus.send()
```

### Module Details

**`__init__.py`** -- Defines `__version__` (used by hatchling for dynamic versioning via `[tool.hatch.version] path`), `__app_name__`, and the `main()` entry point which simply instantiates `AkrocansimGui`.

**`config.py` (Config class)** -- Central configuration manager. On first run, creates `~/akrocansim/` with a default `config.toml` template. Uses `tomllib` to parse TOML. Manages:
- CAN interface connection/disconnection via `can.Bus(**config['CAN_INTERFACE'])`
- J1939DA parsing orchestration (delegates to `J1939DA.parse_J1939DA`)
- Pickle-based caching of parsed J1939 data for fast subsequent loads
- PGN/SPN validation against parsed data
- DBC file export (delegates to `dbc.dump_J1939_dbc`)
- External file/folder opening via OS commands (`os.startfile` on Windows, `xdg-open` on Linux)

**`J1939DA.py`** -- The largest module. Parses the SAE J1939 Digital Annex Excel spreadsheet using openpyxl. Contains extensive `match`/`case` blocks for mapping:
- Transmission rates (human-readable strings to milliseconds)
- SPN positions (complex byte.bit notation to start_byte/start_bit integers)
- SPN lengths (string like "16 bits" to integer bit count)
- Resolution/scale (fraction strings like "0.5/bit" to numeric scale factors; special values "ENUM", "ASCII", "BINARY")
- Offsets, data ranges, operational ranges, units
- Discrete value labels (parsed from SPN description text)

Outputs: one pickle file for runtime use, plus 10 JSON files for debugging/inspection.

**`gui.py` (AkrocansimGui class)** -- DearPyGui-based GUI with:
- Viewport menu bar: Configuration (Open folder, Edit, Load), Signals (Parse J1939DA, Save as DBC), CAN interface (Connect, Disconnect), Help (issues, discussions, About)
- Application log window (right panel) showing INFO/ERROR messages
- Global Tx controls: Stop All / Tx All / Use PGN Settings radio buttons, Tx All Once button
- Per-PGN collapsible sections containing:
  - Continuous signal table: real value input (int or float), unit label, raw hex display, raw decimal slider
  - Discrete (ENUM) signal table: decimal input, binary display, hex display, combo dropdown for labels
  - Per-PGN Tx mode checkbox, rate input (ms), Tx Once button

**`transmitter.py` (Transmitter class)** -- Manages CAN message transmission using daemon threads. Each registered PGN gets its own `threading.Thread` running `send_periodic()` which loops with `time.sleep()`. The CAN frame data is stored as a bytearray per CAN ID. The `modify_pgn_data()` method handles bit-level packing for 1-7 bit, 8-bit, 16-bit, and 32-bit signal widths using bitmask operations. CAN IDs are constructed as J1939 extended frames: `priority << 26 | pgn << 8 | source_address`.

**`signaltools.py`** -- Pure utility functions:
- `encode(decoded_value, scale, offset)` -> raw_value: `round((decoded_value - offset) / scale)`
- `decode(raw_value, scale, offset)` -> decoded_value: `raw_value * scale + offset`
- `start_bit(signal_spec)` -> absolute bit position: `start_byte * 8 + start_bit`
- `raw_min_value(signal_spec)` / `raw_max_value(signal_spec)` -- encode the spec's min/max
- `get_label(signal_spec, value)` / `get_label_value(signal_spec, label)` -- discrete value label lookups

**`dbc.py`** -- Generates Vector CANdb++ (DBC) format files from configured PGNs/SPNs. Contains hardcoded DBC header boilerplate with J1939-specific attribute definitions. Builds BO_ (message) and SG_ (signal) entries, plus BA_ (attribute values) and VAL_ (value tables) sections. Signal names are sanitized to 32 characters with non-word characters replaced by underscores.

**`version_check.py`** -- Queries `https://pypi.org/pypi/akrocansim/json` to check if the running version is the latest on PyPI. Uses `semver.Version.parse` for comparison. Called from the About dialog.

---

## 6. Configuration Details

### User configuration directory
`~/akrocansim/` (i.e., `Path.home() / 'akrocansim'`). Created automatically on first run.

### config.toml structure

```toml
[CAN_INTERFACE]
# Parameters passed directly to can.Bus() constructor
# See https://python-can.readthedocs.io/en/v4.3.1/interfaces.html
interface = 'pcan'
channel = 'PCAN_USBBUS1'
bitrate = 250000

[J1939DA]
filename = 'J1939DA_??????.xlsx'       # Must be .xlsx, placed in ~/akrocansim/J1939DA/
SPNs_and_PGNs_sheet = 'SPNs & PGNs'   # Worksheet name in the Excel file

[J1939DA.SPNs_and_PGNs_sheet_columns]
# Maps logical column names to Excel column letters
'PGN' = 'E'
'SPN' = 'S'
'SPN Name' = 'T'
# ... (14 total column mappings)

[J1939DA.SPNs_to_parse]
first_row = 5
last_row = 5000

[Tx_PGNs_SPNs]
# Format: PGN_number = [SPN1, SPN2, ...]
# Example: 61444 = [513, 190]
```

### Parsed data storage
`~/akrocansim/J1939DA/` contains:
- The user's J1939DA Excel file
- `J1939DA.pkl` -- pickle cache of the parsed J1939 dictionary
- Multiple `J1939DA_*.json` files for inspecting parsing results (transmission rates, SPN positions, lengths, resolutions, offsets, data ranges, operational ranges, units, discrete values)

### DBC export
`~/akrocansim/Tx_PGNs_SPNs.dbc` -- Vector CANdb++ file generated from configured Tx PGNs/SPNs.

---

## 7. Code Conventions and Patterns

### General style
- No type annotations on most functions (except `Config.__init__` and a few return types)
- Heavy use of Python 3.10+ `match`/`case` statements, especially in J1939DA.py for pattern matching on string-formatted data from the Excel sheet
- Module-level constants use UPPER_CASE with double-underscore separators (e.g., `_INDIVIDUAL_TX_MODE__TX_CONT`)
- Private functions prefixed with underscore (e.g., `_map_transmission_rate`, `_hyperlink`)
- Classes use CamelCase; methods and functions use snake_case
- DearPyGui widget tags use string formatting with PGN/SPN numbers: `f'{pgn}_{spn}_input'`, `f'{spn}_hex'`, `str(spn)`

### Naming conventions
- J1939 terms are used directly: PGN (Parameter Group Number), SPN (Suspect Parameter Number), CAN ID, source address, priority
- The main J1939 data structure is a nested dict: `J1939[pgn]['SPNs'][spn][property]`
- Variables often shadow builtins (`min`, `max`) in the J1939DA parser -- be cautious when modifying

### GUI callback pattern
DearPyGui callbacks receive `(sender, app_data, user_data)`. The codebase uses `user_data` tuples like `(pgn, spn, spn_spec)` to pass context to callbacks. Lambda wrappers are used for simple callbacks that need to call methods with specific arguments.

### Threading model
Each PGN gets its own daemon thread that runs an infinite loop with `time.sleep()`. Global mode flags (`global_tx_mode__stop`, `global_tx_mode__cont`, `global_tx_mode__per_pgn`) and per-PGN flags are checked each cycle to determine whether to transmit. There is no explicit thread synchronization (no locks/mutexes) -- the flags are simple boolean/int values.

### Error handling pattern
Methods return lists of message strings (prefixed with `INFO:` or `ERROR:`) rather than raising exceptions. The GUI's `add_messages()` method displays these in the log window.

### Import style
- Relative imports within the package: `from . import J1939DA`, `from .transmitter import Transmitter`
- `from .__init__ import __version__, __app_name__` for version/name access

### Version management
The version string `__version__` in `src/akrocansim/__init__.py` is the single source of truth. Hatchling reads it via `[tool.hatch.version] path = "src/akrocansim/__init__.py"`. The `pyproject.toml` uses `dynamic = ["version", "description"]`.

---

## 8. CI/CD and Release Process

### GitHub Actions workflow
File: `.github/workflows/python-publish.yml`

Triggers on pushing tags matching `v*` (e.g., `v0.6.5`). The workflow:
1. Checks out the repository
2. Sets up `uv` via `astral-sh/setup-uv@v3`
3. Runs `uv build` to create sdist and wheel
4. Runs `uv publish --trusted-publishing always` to publish to PyPI

Uses OIDC trusted publishing (no API tokens needed) via the `release` GitHub environment with `id-token: write` permissions.

### Release process
1. Update `__version__` in `src/akrocansim/__init__.py`
2. Commit the version bump
3. Tag the commit with `v{version}` (e.g., `git tag v0.6.5`)
4. Push the tag to trigger the GitHub Actions publish workflow

### Windows executable build
`build_exe.bat` uses PyInstaller to create a standalone `.exe`:
- `--onefile`: single executable
- `--noconsole`: no console window
- Bundles `akrocansim.ico` and `akrocansim_logo_dark.png` as data files
- References `src/akrocansim_main.py` as the entry script (this file does not exist in the current repo -- may be created locally for exe builds)

---

## 9. Known Issues and Gotchas

### J1939DA parser limitations
- SPNs that still need handling: 7585, 6973, 3192, 900, 899, 927, 7716, 2928 (documented at top of J1939DA.py)
- SPN 584, 585 are not handled correctly due to 2^32 max value not being supported
- Latitude/longitude SPNs have max/scale problems
- All bit-mapped SPNs (3344, 3345, 3346, 3347, 3348) need GUI support -- currently parsed as "BIT_MAPPED" but no GUI rendering
- Some discrete value SPNs are explicitly ignored: 4180, 4181, 7750, 7757

### J1939DA parser has debug code
The `_parse_discrete_value_label` function contains a global `last_checked_reached` flag and `print()`/`input()` calls used for interactive debugging. This code can halt execution if `last_checked` is set to a matching SPN value. Currently `last_checked = 'xxx'` (string), so it will not match any integer SPN, but this is fragile.

### Test file import path is broken
`tests/test_protocols.py` imports from `.. src.akrocansim.protocols.protocols` which does not exist. The correct import would be `from akrocansim.signaltools import decode, encode`. Tests will fail without fixing this.

### DearPyGui version sensitivity
DearPyGui is pinned to exactly `2.0.0`. The DearPyGui API changes significantly between major versions -- do not upgrade without thorough testing.

### All dependencies are pinned to exact versions
`dearpygui==2.0.0`, `python-can==4.5.0`, `openpyxl==3.1.5`, `semver==3.0.4`. This ensures reproducibility but requires manual updates for security patches.

### Threading without synchronization
The `Transmitter` class uses daemon threads without locks. The boolean flags and bytearray data are modified from the GUI thread and read from transmitter threads. This works in practice due to Python's GIL but is technically a race condition for compound operations like the bitmask manipulation in `modify_pgn_data`.

### Windows-primary design
- `Config.ext_edit()` uses `os.system(filename)` on Windows (opens file with default editor) and `os.system('%s %s' % (os.getenv('EDITOR'), filename))` on Linux
- `Config.ext_browse()` uses `os.startfile` on Windows and `xdg-open` on Linux
- The PyInstaller build script is Windows-only (`build_exe.bat`)
- DearPyGui has platform-specific wheels (macOS x86/arm, Linux x86, Windows amd64)

### Source address is hardcoded
The J1939 source address is hardcoded to `0` in `gui.py` line 174: `source_address = 0`. There is no GUI control or config option to change it.

### Variable-length PGN data
When the J1939DA specifies `PGN Data Length` as `'Variable'`, the parser defaults to 8 bytes (standard CAN frame length).

### 32-bit signal max value workaround
For 32-bit signals with non-ASCII scale, the parser caps `max_value` at `100_000 / scale` instead of the full 2^32 range, working around display/slider limitations.

### Config.load() menu callback issue
In `gui.py` line 63, the Configuration > Load menu item callback is `lambda: self.make_tx_dashboard` -- note this references the method without calling it (missing `()`). This means clicking Load does nothing.

---

## 10. Additional Details

### J1939 CAN ID construction
J1939 uses 29-bit extended CAN IDs constructed as:
```
CAN_ID = priority << 26 | PGN << 8 | source_address
```
For DBC export, the extended frame flag (bit 31) is additionally set:
```
frame_id = 1 << 31 | priority << 26 | PGN << 8 | source_address
```

### Signal types
The parser distinguishes several signal types via the `scale` field:
- Numeric (int or float scale): continuous signals with sliders in the GUI
- `'ENUM'`: discrete signals with combo dropdowns
- `'BIT_MAPPED'`: identified but not yet supported in the GUI
- `'ASCII'`: text signals (not supported in GUI)
- `'BINARY'`: binary signals (not supported in GUI)

### Data encoding (little-endian / Intel byte order)
CAN message data is packed in little-endian (LSB first) format, consistent with J1939:
- 16-bit: `data[start_byte] = value & 0x00FF`, `data[start_byte+1] = value >> 8`
- 32-bit: least significant byte first across 4 consecutive bytes
- Sub-byte signals: bitmask operations with `start_bit` offset within the byte

### DBC file format
The generated DBC file follows the Vector CANdb++ format with J1939-specific extensions:
- `VFrameFormat` attribute set to `3` (J1939PG)
- `BusType` set to "CAN"
- `ProtocolType` set to "J1939"
- Signal names are truncated to 32 characters
- Message names starting with a digit are prefixed with underscore

### Python version requirement
Python 3.13+ is required. This is enforced in `pyproject.toml` (`requires-python = ">=3.13"`) and `.python-version`. The codebase uses `match`/`case` (available since 3.10) and `tomllib` (available since 3.11). The 3.13 requirement appears driven by DearPyGui 2.0.0 wheel availability.
