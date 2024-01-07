import platform
import os
import subprocess
from pathlib import Path
import tomllib

from .protocols.J1939DA_parser import parse_J1939DA

default_config_toml = '''[CAN_INTERFACE]
# Akrocansim uses the python-can library for utilising CAN interfaces.
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
# Save the 'J1939DA_??????.xlsx' file in the 'J1939' folder located in the same folder with this configuration.
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
# List the PGNs and SPNs to be loaded by Akrocansim using the following format:
# PGN = [SPN#1, SPN#2, ..., SPN#N], e.g. 61444 = [513, 190]

#61444 = [513, 190]
'''


class Config:
    def __init__(self, akrocansim_user_dir: Path):
        self.akrocansim_user_dir: Path = akrocansim_user_dir
        self.config_toml: Path = akrocansim_user_dir/'config.toml'
        self.J1939_dir: Path = akrocansim_user_dir/'J1939'
        self.J1939_pickle: Path = self.J1939_dir/'J1939.pkl'
        self._config: dict = {}

    def __getitem__(self, item):
        return self._config[item]

    def bootstrap(self) -> None:
        self.akrocansim_user_dir.mkdir(exist_ok=True)
        self.J1939_dir.mkdir(exist_ok=True)
        with self.config_toml.open(mode='w', encoding='utf-8') as f:
            f.write(default_config_toml)

    def load(self) -> None:
        with self.config_toml.open('rb') as f:
            self._config = tomllib.load(f)

    def ext_edit(self) -> None:
        filename = str(self.config_toml)
        if platform.system() == 'Windows':
            os.system(filename)
        else:
            os.system('%s %s' % (os.getenv('EDITOR'), filename))

    def ext_browse(self) -> None:
        path = str(self.akrocansim_user_dir)
        if platform.system() == 'Windows':
            os.startfile(path)
        else:
            subprocess.Popen(["xdg-open", path])

    def parse_J1939DA(self):
        return parse_J1939DA(J1939_dir=self.J1939_dir, J1939DA_config=self._config['J1939DA'])
