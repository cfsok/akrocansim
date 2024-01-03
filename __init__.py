"""Akrocansim is a CAN bus J1939 controller simulator."""

__version__ = '0.2.0'

from pathlib import Path
import tomllib
import pickle
import canbustransmitter
import J1939
import gui
import can


akrocansim_dir = 'akrocansim'

default_config_toml = '''[CAN_INTERFACE]
# Akrocansim uses the python-can library for utilising CAN interfaces.
# Any configuration parameters defined by python-can, can be listed here
# in the same format at they would appear in can.interface.Bus().
# See https://python-can.readthedocs.io/en/stable/configuration.html.
# See example key/value pairs below for PCAN-USB.
interface='pcan'
channel='PCAN_USBBUS1'
bitrate=250000

[J1939DA]
# Obtain a copy of the J1939 Digital Annex from SAE International at: https://www.sae.org/standards/?search=j1939DA
# The J1939 Digital Annex is a Microsoft Excel file.
# If your copy is in .xls format, you need to convert it to .xlsx using Microsoft Excel.
# Save the 'J1939DA_??????.xlsx' file in the 'J1939' folder located in the same folder with this configuration.
# Edit the values of all keys in the [J1939DA] table as required and run J1939DA_parser.py.
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


config_file = Path.home().joinpath(akrocansim_dir, 'config.toml')
config_file.parent.mkdir(exist_ok=True)
Path.home().joinpath(akrocansim_dir, 'J1939').mkdir(exist_ok=True)


if not config_file.exists():
    with config_file.open('w', encoding='utf-8') as f:
        f.write(default_config_toml)
        print(f'Configuration file created at: {config_file}\n'
              f'Follow the instructions in the configuration file and run Akrocansim again.')
else:
    with config_file.open('rb') as f:
        config = tomllib.load(f)

    Tx_PGNs_SPNs = {}
    for pgn, spn_list in config['Tx_PGNs_SPNs'].items():
        Tx_PGNs_SPNs[int(pgn)] = spn_list
    gui.Tx_PGNs_SPNs = Tx_PGNs_SPNs

    if config['CAN_INTERFACE']:
        canbustransmitter.bus = can.thread_safe_bus.Bus(**config['CAN_INTERFACE'])


J1939_pickle = Path.home().joinpath(akrocansim_dir, 'J1939', 'J1939.pkl')
if J1939_pickle.exists():
    with J1939_pickle.open('rb') as f:
        J1939_dict = pickle.load(f)
    canbustransmitter.J1939 = J1939_dict
    J1939.J1939 = J1939_dict
    gui.J1939 = J1939_dict
    gui.start_gui(canbustransmitter.bus, str(config_file))

    print(f'Using {J1939_pickle}')
