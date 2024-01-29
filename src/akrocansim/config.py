import platform
import os
import subprocess
from pathlib import Path
import tomllib
import pickle

import can

from .import J1939

default_config_toml = '''[CAN_INTERFACE]
# akrocansim uses the python-can library for utilising CAN interfaces.
# Any configuration parameters defined by python-can, can be listed here
# in the same format at they would appear in can.interface.Bus().
# See https://python-can.readthedocs.io/en/v4.3.1/interfaces.html

# See example key/value pairs below for PCAN-USB.

interface='pcan'
channel='PCAN_USBBUS1'
bitrate=250000


[J1939DA]
# Obtain a copy of the J1939 Digital Annex from SAE International at: https://www.sae.org/standards/?search=j1939DA
# The J1939 Digital Annex is a Microsoft Excel file.
# If your copy is in .xls format, you need to convert it to .xlsx using Microsoft Excel.
# Save the 'J1939DA_??????.xlsx' file in the 'J1939' folder, located in the same folder with this configuration.
# Edit the values of all keys in the [J1939DA] table as required and parse the J1939 Digital Annex.

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

#61444 = [513, 190]
'''


class Config:
    def __init__(self, config_dir: Path = None):
        if config_dir is None:
            self.config_dir = Path.home()/'akrocansim'
        else:
            self.config_dir = config_dir
        self.config_toml = self.config_dir/'config.toml'
        self.J1939_dir = self.config_dir/'J1939'
        self.J1939DA_xlsx = None
        self.J1939_pickle = self.J1939_dir/'J1939.pkl'

        self._config = {}

        self.J1939_spec = None
        self.bus = None
        self.tx_PGNs_SPNs = {}

    def load(self) -> (str, list[str]):
        status_message = ''
        error_messages = []

        state = 'INIT'
        while True:
            match state:
                case 'INIT':
                    if self.config_toml.exists():
                        state = 'CONFIG_PRESENT'
                    else:
                        state = 'CONFIG_NOT_PRESENT'

                case 'CONFIG_NOT_PRESENT':
                    self.config_dir.mkdir(exist_ok=True)
                    self.J1939_dir.mkdir(exist_ok=True)
                    with self.config_toml.open(mode='w', encoding='utf-8') as f:
                        f.write(default_config_toml)
                    status_message = f'new configuration file created at {self.config_toml}'
                    state = 'RETURN'

                case 'CONFIG_PRESENT':
                    try:
                        with self.config_toml.open('rb') as f:
                            self._config = tomllib.load(f)
                        state = 'CHECK_CAN_CONFIG'
                    except tomllib.TOMLDecodeError as e:
                        status_message = 'configuration file cannot be loaded'
                        error_messages.append(f'FORMAT ERROR: {e}')
                        state = 'RETURN'

                case 'CHECK_CAN_CONFIG':
                    if self.bus is not None:
                        self.bus.shutdown()
                    try:
                        if not self._config['CAN_INTERFACE']:
                            status_message = 'incorrect or incomplete configuration'
                            error_messages.append('MISSING ELEMENT ERROR: CAN interface configuration parameters'
                                                  ' not found in [CAN_INTERFACE] section')
                        else:
                            try:
                                self.bus = can.Bus(**self._config['CAN_INTERFACE'])
                            except can.exceptions.CanError as e:
                                status_message = 'incorrect or incomplete configuration'
                                error_messages.append(f'CAN INTERFACE ERROR: {e}')
                    except KeyError:
                        status_message = 'incorrect or incomplete configuration'
                        error_messages.append(f'MISSING ELEMENT ERROR: [CAN_INTERFACE] section not found')
                    state = 'CHECK_J1939DA'

                case 'CHECK_J1939DA':
                    if '?' in self._config['J1939DA']['filename']:
                        status_message = 'incorrect or incomplete configuration'
                        error_messages.append(f'INCORRECT ELEMENT ERROR: [J1939DA] filename has not been set')
                        state = 'RETURN'
                    elif Path(self._config['J1939DA']['filename']).suffix != '.xlsx':
                        status_message = 'incorrect or incomplete configuration'
                        error_messages.append('INCORRECT ELEMENT ERROR: J1939DA filename must be in .xlsx format')
                        state = 'RETURN'
                    else:
                        self.J1939DA_xlsx = self.J1939_dir/self._config['J1939DA']['filename']
                        if not self.J1939DA_xlsx.exists():
                            status_message = 'incorrect or incomplete configuration'
                            error_messages.append(f'INCORRECT ELEMENT ERROR: {self.J1939DA_xlsx} file not found')
                            state = 'RETURN'
                        else:
                            state = 'CHECK_J1939_PKL'

                    # I think it's all good until here.

                case 'CHECK_J1939_PKL':
                    if not self.J1939_pickle.exists():
                        status_message = 'J1939DA has not been parsed'
                        state = 'RETURN'
                    else:
                        with self.J1939_pickle.open('rb') as f:
                            self.J1939_spec = pickle.load(f)
                            state = 'CHECK_TX_SPNS'

                case 'CHECK_TX_SPNS':
                    if not self._config['Tx_PGNs_SPNs']:
                        status_message = 'incorrect or incomplete configuration'
                        error_messages.append('INCORRECT ELEMENT ERROR: PGNs not found in [Tx_PGNs_SPNs] section')
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
                                        status_message = 'incorrect or incomplete configuration'
                                        error_messages.append(
                                            f'MISSING SPN ERROR: SPN {spn} not found in parsed elements of J1939DA')
                            except KeyError:
                                pgn_spn_errors_found = True
                                status_message = 'incorrect or incomplete configuration'
                                error_messages.append(
                                    f'MISSING PGN ERROR: PGN {pgn} not found in parsed elements of J1939DA')
                            if not pgn_spn_errors_found:
                                self.tx_PGNs_SPNs[int(pgn)] = spn_list
                            pgn_spn_errors_found = False

                    state = 'RETURN'

                case 'RETURN':
                    return status_message, error_messages

                case _:
                    raise Exception()

    def parse_J1939DA(self) -> str:
        parsing_result = J1939.parse_J1939DA(J1939_dir=self.J1939_dir, J1939DA_config=self._config['J1939DA'])
        return parsing_result

    def ext_browse(self) -> None:
        path = str(self.config_dir)
        if platform.system() == 'Windows':
            os.startfile(path)
        else:
            subprocess.Popen(["xdg-open", path])

    def ext_edit(self) -> None:
        filename = str(self.config_toml)
        if platform.system() == 'Windows':
            os.system(filename)
        else:
            os.system('%s %s' % (os.getenv('EDITOR'), filename))
