import platform
import os
import subprocess
from pathlib import Path
import tomllib
import pickle

import can

from . import J1939DA
from . import dbc
from .engine_spec import get_engine_j1939_spec, get_default_tx_pgns_spns


default_config_toml = '''[CAN_INTERFACE]
# akrocansim uses the python-can library for utilising CAN interfaces.
# Any configuration parameters defined by python-can, can be listed here
# in the same format at they would appear in can.interface.Bus().
# See https://python-can.readthedocs.io/en/v4.3.1/interfaces.html

# UDP multicast (no hardware needed — works cross-platform)
interface='udp_multicast'
channel='239.0.0.1'
port=10000

# Uncomment below for a USB CAN adapter (e.g. CANable with slcan firmware):
# interface='slcan'
# channel='/dev/tty.usbmodemXXXX'
# bitrate=250000

# Uncomment below for socketcan on Linux/RPi:
# interface='socketcan'
# channel='can0'
# bitrate=250000


[J1939_SOURCE]
# Set to 'embedded' to use built-in engine PGN/SPN definitions (no J1939DA file needed).
# Set to 'j1939da' to use a SAE J1939 Digital Annex spreadsheet.
mode = 'embedded'


[J1939DA]
# Only needed if [J1939_SOURCE] mode = 'j1939da'
# Obtain a copy of the J1939 Digital Annex from SAE International at: https://www.sae.org/standards/?search=j1939DA
# The J1939 Digital Annex is a Microsoft Excel file.
# If your copy is in .xls format, you need to convert it to .xlsx using Microsoft Excel.
# Save the 'J1939DA_??????.xlsx' file in the 'J1939' folder, located in the same folder with this configuration.

filename = 'J1939DA_??????.xlsx'
SPNs_and_PGNs_sheet = 'SPNs & PGNs'


[J1939DA.SPNs_and_PGNs_sheet_columns]
# Adjust as required

'PGN' = 'E'
'Parameter Group Label' = 'F'
'Acronym' = 'G'
'PGN Description' = 'H'
'PGN Data Length' = 'O'
'Default Priority' = 'P'
'Transmission Rate' = 'N'
'SPN' = 'S'
'SPN Name' = 'T'
'SPN Description' = 'U'
'SPN Position in PGN' = 'R'
'SPN Length' = 'V'
'Resolution' = 'W'
'Offset' = 'X'
'Data Range' = 'Y'
'Operational Range' = 'Z'
'Units' = 'AA'


[J1939DA.SPNs_to_parse]
# Specify the range of rows in the J1939 Digital Annex SPNs_and_PGNs_sheet that will be scanned for SPN definitions.

first_row = 5
last_row = 5000


[Tx_PGNs_SPNs]
# List the PGNs and SPNs to be loaded by akrocansim using the following format:
# PGN = [SPN#1, SPN#2, ..., SPN#N], e.g. 61444 = [513, 190]
# When using embedded mode, these are auto-populated if left empty.

#61444 = [513, 190]
'''


class Config:
    def __init__(self, config_dir: Path = None):
        if config_dir is None:
            self.config_dir = Path.home()/'akrocansim'
        else:
            self.config_dir = config_dir
        self.config_toml = self.config_dir/'config.toml'
        self.J1939DA_dir = self.config_dir / 'J1939DA'
        self.J1939DA_xlsx = None
        self.J1939DA_pickle = self.J1939DA_dir / 'J1939DA.pkl'

        self._config = {}

        self.J1939_spec = None
        self.bus = None
        self.tx_PGNs_SPNs = {}
        self.tx_PGNs_SPNs_dbc = self.config_dir / 'Tx_PGNs_SPNs.dbc'

    def load(self):
        messages = []

        if not self.config_toml.exists():
            self.config_dir.mkdir(exist_ok=True)
            self.J1939DA_dir.mkdir(exist_ok=True)
            with self.config_toml.open(mode='w', encoding='utf-8') as f:
                f.write(default_config_toml)
            messages.append(f'INFO: configuration file created: {self.config_toml}')
            messages.append('INFO: follow the instructions in the configuration file: MENU > Configuration > Edit')
        else:
            try:
                with self.config_toml.open('rb') as f:
                    self._config = tomllib.load(f)
            except tomllib.TOMLDecodeError as e:
                messages.append(f'ERROR: incompatible configuration file - {e}')

            # Check source mode: 'embedded' or 'j1939da'
            source_mode = self._config.get('J1939_SOURCE', {}).get('mode', 'j1939da')

            if source_mode == 'embedded':
                messages.extend(self._load_embedded_spec())
            else:
                messages.extend(self._load_j1939da_spec())

        return messages

    def _load_embedded_spec(self):
        """Load the built-in engine J1939 spec (no Digital Annex needed)."""
        messages = []
        self.J1939_spec = get_engine_j1939_spec()
        messages.append('INFO: loaded embedded engine J1939 spec '
                        f'({len(self.J1939_spec)} PGNs)')

        # Use Tx_PGNs_SPNs from config if defined, otherwise use defaults
        tx_config = self._config.get('Tx_PGNs_SPNs', {})
        if tx_config:
            for pgn, spn_list in tx_config.items():
                pgn_int = int(pgn)
                if pgn_int in self.J1939_spec:
                    self.tx_PGNs_SPNs[pgn_int] = spn_list
                else:
                    messages.append(f'ERROR: PGN {pgn} not found in embedded spec')
        else:
            self.tx_PGNs_SPNs = get_default_tx_pgns_spns()
            messages.append(f'INFO: using default engine Tx PGNs ({len(self.tx_PGNs_SPNs)} PGNs)')

        return messages

    def _load_j1939da_spec(self):
        """Load from the SAE J1939 Digital Annex spreadsheet (original behavior)."""
        messages = []

        if '?' in self._config['J1939DA']['filename']:
            messages.append(f'INFO: [J1939DA] filename has not been specified in the configuration file')
        elif Path(self._config['J1939DA']['filename']).suffix != '.xlsx':
            messages.append('ERROR: J1939DA filename must be in .xlsx format')
        else:
            self.J1939DA_xlsx = self.J1939DA_dir / self._config['J1939DA']['filename']
            if not self.J1939DA_xlsx.exists():
                messages.append(f'ERROR: {self.J1939DA_xlsx} file not found')
            else:
                if not self.J1939DA_pickle.exists():
                    messages.append(self.parse_J1939DA())
                else:
                    with self.J1939DA_pickle.open('rb') as f:
                        self.J1939_spec = pickle.load(f)
                        messages.append(f'INFO: loaded: {self.J1939DA_pickle}')

                    if not self._config['Tx_PGNs_SPNs']:
                        messages.append('ERROR: PGNs not found in [Tx_PGNs_SPNs] section of configuration file')
                    else:
                        pgn_spn_errors_found = False
                        for pgn, spn_list in self._config['Tx_PGNs_SPNs'].items():
                            try:
                                _ = self.J1939_spec[int(pgn)]
                                for spn in spn_list:
                                    try:
                                        _ = self.J1939_spec[int(pgn)]['SPNs'][spn]
                                    except KeyError:
                                        pgn_spn_errors_found = True
                                        messages.append(f'ERROR: SPN {spn} not found in parsed elements of J1939DA')
                            except KeyError:
                                pgn_spn_errors_found = True
                                messages.append(f'ERROR: PGN {pgn} not found in parsed elements of J1939DA')
                            if not pgn_spn_errors_found:
                                self.tx_PGNs_SPNs[int(pgn)] = spn_list
                            pgn_spn_errors_found = False

        return messages

    def connect_can(self):
        messages = []

        if not self._config:
            messages.append('ERROR: configuration file has not been loaded')
        elif self.bus is not None:
            messages.append(self.disconnect_can())
        try:
            if not self._config['CAN_INTERFACE']:
                messages.append('ERROR: CAN interface configuration parameters not found '
                                'in [CAN_INTERFACE] section of configuration file')
            else:
                try:
                    self.bus = can.Bus(**self._config['CAN_INTERFACE'])
                    bitrate = self._config['CAN_INTERFACE'].get('bitrate')
                    bitrate_info = f", bit rate: {bitrate / 1000:.0f} kbit/s" if bitrate else ""
                    messages.append(f"INFO: connected to: {self.bus.channel_info}{bitrate_info}")
                except can.exceptions.CanError as e:
                    messages.append(f'ERROR: {e}')
        except KeyError:
            messages.append(f'ERROR: [CAN_INTERFACE] section not found in configuration file')

        return messages

    def disconnect_can(self):
        if self.bus is not None:
            channel_info = self.bus.channel_info
            self.bus.shutdown()
            self.bus = None
            return f'INFO: {channel_info} disconnected'
        else:
            return 'INFO: CAN bus is not connected'

    def parse_J1939DA(self):
        parsing_result = J1939DA.parse_J1939DA(J1939DA_config=self._config['J1939DA'],
                                               J1939DA_dir=self.J1939DA_dir,
                                               J1939DA_pickle=self.J1939DA_pickle)
        messages = [f'INFO: {parsing_result}', 'reload configuration to use parsed J1939DA definitions']
        return messages

    def dump_tx_PGNs_SPNs_dbc(self):
        dbc.dump_J1939_dbc(J1939DA=self.J1939_spec, PGNs_SPNs=self.tx_PGNs_SPNs, PGNs_SPNs_dbc=self.tx_PGNs_SPNs_dbc)
        return f'INFO: DBC file created: {self.tx_PGNs_SPNs_dbc}'

    def ext_browse(self) -> None:
        path = str(self.config_dir)
        if platform.system() == 'Windows':
            os.startfile(path)
        elif platform.system() == 'Darwin':
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def ext_edit(self) -> None:
        filename = str(self.config_toml)
        if platform.system() == 'Windows':
            os.system(filename)
        elif platform.system() == 'Darwin':
            subprocess.Popen(["open", "-t", filename])
        else:
            os.system('%s %s' % (os.getenv('EDITOR', 'nano'), filename))
