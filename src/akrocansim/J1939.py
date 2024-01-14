# SPN that still need handling: 7585, 6973, 6317(check), 3192, 5433(check), 900, 899, 927, 7716, 2928, 5677(check), 5678(check), 7750
# SPN 584, 585 are not handled correctly - 2**32 max value not supported
# spn for lat, long max,scale problem
# all bit mapped SPNs need GUI support
# resolution: 8 bit bit-mapped
import pickle
import json
from pathlib import Path
from openpyxl import load_workbook


bit_mapped_spns = [3344, 3345, 3346, 3347, 3348]
ignore_discrete_value_spns = [4180, 4181]


def _map_transmission_rate(rate):
    if rate is None:
        tx_rate_ms = None
    else:
        match rate:
            case 'To engine: Control Purpose dependent or 10 ms_x000D_\nTo retarder: 50 ms':
                tx_rate_ms = 50
            case 'When active; 50 ms to transmission and axles':
                tx_rate_ms = 50
            case 'When active: 20 ms; else 200 ms':
                tx_rate_ms = 20
            case '100 ms':
                tx_rate_ms = 10
            case 'Manufacturer defined, not faster than 20 ms':
                tx_rate_ms = 50
            case 'Every 100 ms and on change but no faster than 20 ms':
                tx_rate_ms = 100
            case 'Every 50ms and if SPN 5681 \"Driver activation demand for Advanced Emergency Braking System\" has changed but no faster than every 10 ms':
                tx_rate_ms = 500
            case '50 ms':
                tx_rate_ms = 50
            case '20 ms':
                tx_rate_ms = 20
            case 'Every 100 ms and on change of state but no faster than every 10 ms.':
                tx_rate_ms = 100
            case 'Engine speed dependent':
                tx_rate_ms = 50
            case '200 ms':
                tx_rate_ms = 200
            case 'As required':
                tx_rate_ms = 5000
            case '1 s':
                tx_rate_ms = 1000
            case 'Every 10 s and on change but no faster than 100 ms.':
                tx_rate_ms = 10000
            case 'On request':
                tx_rate_ms = 5000
            case 'Every 1 s and on change but no faster than 100 ms':
                tx_rate_ms = 1000
            case 'Every 1 s and on change of state but no faster than every 100 ms.':
                tx_rate_ms = 1000
            case 'As needed':
                tx_rate_ms = 5000
            case 'As required but no faster than once every 100 ms.':
                tx_rate_ms = 5000
            case 'Every 10 s and on change but no faster than 1 s.':
                tx_rate_ms = 10000
            case 'On powerup and on request':
                tx_rate_ms = 5000
            case 'As required but no more often than 500 ms':
                tx_rate_ms = 5000
            case 'Every 10 s and on change of state, but not faster than 1 s.  Every second when in tuning mode.':
                tx_rate_ms = 10000
            case 'Every 10 s and on change of state, but not faster than every 1 s.':
                tx_rate_ms = 10000
            case 'manufacturer defined, not faster than 100 ms':
                tx_rate_ms = 5000
            case 'Manufacturer defined, not faster than 100 ms':
                tx_rate_ms = 5000
            case 'On event':
                tx_rate_ms = 5000
            case '5 s':
                tx_rate_ms = 5000
            case 'Every 5 s and on change of state but no faster than every 100 ms':
                tx_rate_ms = 5000
            case '100 ms when active':
                tx_rate_ms = 100
            case 'This message is transmitted in response to an Anti-Theft Request message. This message is also sent when the component has an abnormal power interruption.  In this situation the Anti-Theft Status Report is sent without the Anti-Theft Request.':
                tx_rate_ms = 5000
            case 'Transmission of this message is interrupt driven.  This message is also transmitted upon power-up of the interfacing device sending this message.':
                tx_rate_ms = 5000
            case 'When needed':
                tx_rate_ms = 5000
            case '10 ms':
                tx_rate_ms = 10
            case '50 ms (preferred) or Engine Speed Dependent (if required by application)':
                tx_rate_ms = 50
            case '500 ms':
                tx_rate_ms = 500
            case '50 ms (only when active)':
                tx_rate_ms = 50
            case '20 ms when torque converter unlocked, 100 ms when torque converter locked':
                tx_rate_ms = 20
            case 'Engine speed dependent when there is no combustion, once every 5 s otherwise.':
                tx_rate_ms = 50
            case 'Engine speed dependent when knock present, once every 5 s otherwise.':
                tx_rate_ms = 50
            case 'Transmitted only after requested.  After request, broadcast rate is engine speed dependent.  Update stopped after key switch cycle.':
                tx_rate_ms = 50
            case 'Transmitted every 20 ms for the first 100 ms and then broadcast every 1 s for 10 s in case of a crash event':
                tx_rate_ms = 20
            case '10 ms (default) or 20 ms':
                tx_rate_ms = 10
            case 'Every 50ms and on change of \"AEBS state\" or change of \"Collision warning level\" but no faster than every 10 ms':
                tx_rate_ms = 50
            case '100 ms or on change, but no faster than 20 ms.':
                tx_rate_ms = 100
            case 'Engine Speed Dependent when active, otherwise every 1 s.':
                tx_rate_ms = 50
            case 'Engine Speed Dependent':
                tx_rate_ms = 50
            case 'Default broadcast rate of 20 ms unless the sending device has received Engine Start Control Message Rate (SPN 7752) from the engine start arbitrator indicating a switch to 250 ms or on change, but no faster than 20 ms.':
                tx_rate_ms = 20
            case 'Default broadcast rate of 20 ms unless the arbitrator is transmitting Engine Start Control Message Rate (SPN 7752) indicating a switch to 250 ms or on change, but no faster than 20 ms.':
                tx_rate_ms = 20
            case '10 sec':
                tx_rate_ms = 10000
            case '30 sec':
                tx_rate_ms = 30000
            case '250 ms (preferred) or Engine Speed Dependent (if required by application)':
                tx_rate_ms = 250
            case 'Every 1 s and on change of any parameter but no faster than 100 ms.':
                tx_rate_ms = 1000
            case 'Every 1s and on change in any door command but no faster than 100 ms':
                tx_rate_ms = 1000
            case 'Every 1s and on change in any door latch status but no faster than 100 ms':
                tx_rate_ms = 1000
            case '10 s':
                tx_rate_ms = 10000
            case '250 ms':
                tx_rate_ms = 250
            case 'Transmitted only after requested.  After request, broadcast rate is 1 s.  Update stopped after key switch cycle.':
                tx_rate_ms = 1000
            case 'Every 10 s and on change, but no faster than 1 s.':
                tx_rate_ms = 10000
            case 'Every 500 ms and on change but no faster than 50 ms.':
                tx_rate_ms = 500
            case 'Every 500 ms and on change but no faster than 20 ms':
                tx_rate_ms = 500
            case '1 s and on change of any switched power output status but no faster than once every 25 ms.':
                tx_rate_ms = 1000
            case '1 s and on change of any fused power output status but no faster than once every 25 ms.':
                tx_rate_ms = 1000
            case '1 s_x000D_\n_x000D_\nNote: Systems developed to the standard published before June, 2014 might not be transmitted at a 1 s rate, but be transmitted on request.':
                tx_rate_ms = 1000
            case '1 s._x000D_\n_x000D_\nNote: Systems developed to the standard published before June, 2015 might not be transmitted at a 1 s rate, but be transmitted on request.':
                tx_rate_ms = 1000
            case '30 s':
                tx_rate_ms = 30000
            case 'Every 5 s and on change of torque/speed points of more than 10% since last transmission but no faster than every 500 ms':
                tx_rate_ms = 5000
            case 'Every 1 s and on change of state but no faster than every 100 ms':
                tx_rate_ms = 1000
            case 'On start-up, and every 1 s until the dewpoint signal state = 1 (SPN 3240) has been received by the transmitter':
                tx_rate_ms = 1000
            case 'On start-up, and every 1 s until the dewpoint signal state = 1 (SPN 3239) has been received by the transmitter':
                tx_rate_ms = 1000
            case 'On start-up, and every 1 s until the dewpoint signal state = 1 (SPN 3238) has been received by the transmitter':
                tx_rate_ms = 1000
            case 'On start-up, and every 1 s until the dewpoint signal state = 1 (SPN 3237) has been received by the transmitter':
                tx_rate_ms = 1000
            case 'Transmitted every 5 s and on change of PGN 64791 but no faster than every 250 ms':
                tx_rate_ms = 5000
            case 'Every 100 ms and on change of state, but no faster than every 20 ms.  Grandfathered definition for systems that implemented this message prior to July, 2010: Every 100 ms or on change of state, but no faster than every 20 ms':
                tx_rate_ms = 100
            case 'Every 100 ms and on change of state, but no faster than every 20 ms. Grandfathered definition for systems that implemented this message prior to July, 2010: Every 100 ms or on change of state, but no faster than every 20 ms':
                tx_rate_ms = 100
            case 'On request.  Upon request, will be broadcast as many times as required to transmit all available axle groups.':
                tx_rate_ms = 5000
            case 'As needed.  Broadcast whenever an axle group equipped with an on-board scale joined or left the on-board scale subset.':
                tx_rate_ms = 5000
            case 'Every 1 s while active and on change of state but no faster than every 100 ms.  Grandfathered definition for systems that implemented this message prior to July, 2010:  1 s when active and on change of state':
                tx_rate_ms = 1000
            case 'Every 1 s and on change of state but no faster than every 100 ms.  Grandfathered definition for systems that implemented this message prior to July, 2010:  1 s and on change':
                tx_rate_ms = 1000
            case 'Every 1 s and on change of state but no faster than every 100 ms.  Grandfathered definition for systems that implemented this message prior to July, 2010:  1 s or on change':
                tx_rate_ms = 1000
            case '250 ms or on change of any state-based parameter but no faster than 20 ms':
                tx_rate_ms = 250
            case '100 ms (preferred) or Engine Speed Dependent (if required by application)':
                tx_rate_ms = 100
            case 'On Request':
                tx_rate_ms = 5000
            case '0.5 s':
                tx_rate_ms = 500
            case 'Every 1 s and on change of switch state but no faster than every 100 ms':
                tx_rate_ms = 1000
            case 'Every 10 s and on change of state but no faster than every 100 ms.  Grandfathered definition for systems that implemented this message prior to July, 2010: On change or every 10 s':
                tx_rate_ms = 10000
            case 'Every 100 ms and on change of state but no faster than every 20 ms.  Grandfathered definition for systems that implemented this message prior to July, 2010: 100 ms or on change, not to exceed 20 ms':
                tx_rate_ms = 100
            case '1 s or on change of state-based parameters but no faster than 100 ms.':
                tx_rate_ms = 1000
            case '1 s, when active':
                tx_rate_ms = 1000
            case 'As requested.':
                tx_rate_ms = 5000
            case 'On request or sender may transmit every 5 s until acknowledged by reception of the engine configuration message PGN 65251 SPN 7828.':
                tx_rate_ms = 5000
            case '500 ms or upon state change, but not faster than 100 ms.':
                tx_rate_ms = 500
            case '100ms':
                tx_rate_ms = 100
            case '100 ms_x000D_\n_x000D_\nNote: Systems developed to the standard published before January, 2015 transmit at a 1s rate.':
                tx_rate_ms = 100
            case '100ms or upon state change, but not faster than 20 ms.':
                tx_rate_ms = 100
            case '1s':
                tx_rate_ms = 1000
            case 'Every 1 s and on change of state but no faster than every 100 ms._x000D_\n_x000D_\nGrandfathered definition for systems that implemented this message prior to July, 2010: 1 s when active; or on change of state':
                tx_rate_ms = 1000
            case '1 s_x000D_\n_x000D_\nNote: Systems developed to the standard published before June, 2015 might not be transmitted at a 1 s rate, but be transmitted on request.':
                tx_rate_ms = 1000
            case '1 s_x000D_\n_x000D_\nNote: Systems developed to the standard published before SEP2015 transmit at a 5s rate.':
                tx_rate_ms = 5000
            case '10 s or on change but no more often than 1s':
                tx_rate_ms = 1000
            case _:
                tx_rate_ms = None
    return tx_rate_ms

def _map_spn_position(pos):
    if pos is None:
        start_byte = None
        start_bit = None
    else:
        match pos, len(pos), len(pos.split('.')), len(pos.split('-')):
            case [char, 1, 1, 1] if char.isalpha():
                start_byte = None
                start_bit = None
            case ['1-2.1', _, _, _]:
                start_byte = 0
                start_bit = 0
            case ['1.7-2' | '1.7-2.1', _, _, _]:
                start_byte = 0
                start_bit = 7
            case ['2.4-4', _, _, _]:
                start_byte = 1
                start_bit = 3
            case ['2.8-3.1', _, _, _]:
                start_byte = 1
                start_bit = 7
            case ['3.7-4', _, _, _]:
                start_byte = 2
                start_bit = 6
            case ['4.7-5.1', _, _, _]:
                start_byte = 3
                start_bit = 6
            case ['5.7-6', _, _, _]:
                start_byte = 4
                start_bit = 6
            case ['5.8-6.1', _, _, _]:
                start_byte = 4
                start_bit = 7
            case ['6,7.1', _, _, _]:
                start_byte = 5
                start_bit = 0
            case ['7.6-8.1', _, _, _]:
                start_byte = 6
                start_bit = 5
            case ['7.7-8.1', _, _, _]:
                start_byte = 6
                start_bit = 6
            case ['1-N', _, _, _]:
                start_byte = 0
                start_bit = 0
            case ['2-n' | '2-N' | '2 to n', _, _, _]:
                start_byte = 1
                start_bit = 0
            case ['4 to n', _, _, _]:
                start_byte = 3
                start_bit = 0
            case ['5 to A', _, _, _]:
                start_byte = 4
                start_bit = 0
            case [_, 1 | 2, 1, 1]:
                start_byte = int(pos) - 1
                start_bit = 0
            case [_, 3 | 4, 2, 1]:
                start_byte, start_bit = pos.split('.')
                start_byte = int(start_byte) - 1
                start_bit = int(start_bit) - 1
            case [_, 3 | 4 | 5 | 7, 1, 2]:
                start_byte, start_bit = pos.split('-')
                start_byte = int(start_byte) - 1
                start_bit = 0
            case _:
                start_byte = None
                start_bit = None
    return start_byte, start_bit

def _map_spn_length(length):
    if length is None:
        length_bits = None
    else:
        match length.split(' '):
            case [n_bits, 'bit' | 'bits']:
                length_bits = int(n_bits)
            case [n_bytes, 'byte' | 'bytes']:
                length_bits = int(n_bytes) * 8
            case _:
                length_bits = None
    return length_bits

def _map_resolution(res):
    if res is None:
        scale = 1
    else:
        match res.split():
            case ['ASCII']:
                scale = 'ASCII'
            case ['Binary']:
                scale = 'BINARY'
            case ['bit-mapped'] | [_, 'bit', 'bit-mapped']:
                scale = 'ENUM'
            case [_, states, 'bit'] if states.split('/')[0] == 'states':
                scale = 'ENUM'
            case [res] if res.split('/')[1] == 'bit':
                num = res.split('/')[0]
                try:
                    scale = int(num)
                except ValueError:
                    scale = float(num)
            case [fraction_res, *_] if len(fraction_res.split('/')) == 2:
                numerator, denominator = fraction_res.split('/')
                scale = int(numerator) / int(denominator)
            case [num, *_]:
                try:
                    scale = int(num)
                except ValueError:
                    scale = float(num)
            case _:
                scale = None
    return scale

def _map_offset(offset):
    if offset is None:
        _offset = None
    else:
        num = offset.split(' ')[0].replace(',','')
        try:
            _offset = int(num)
        except ValueError:
            _offset = float(num)
    return _offset

def _map_data_range(data_range):
    if data_range is None:
        min_value = None
        max_value = None
    else:
        match data_range.replace(',','').split(' '):
            case ['bit-mapped']:
                min_value = None
                max_value = None
            case [min, 'to', max, *_]:
                try:
                    min_value = int(min)
                except ValueError:
                    min_value = float(min)
                try:
                    max_value = int(max)
                except ValueError:
                    max_value = float(max)
            case _:
                min_value = None
                max_value = None
    return min_value, max_value

def _map_operational_range(op_range):
    operational_min_value = None
    operational_max_value = None
    if op_range is not None:
        match op_range:
            case '0 to 125% engine torque requests, -125% to 0% for retarder torque requests':
                operational_min_value = -125
                operational_max_value = 125
            case '0 to 7 and 15 exclusively':
                operational_min_value = 0
                operational_max_value = 15
            case '0 is used to indicate that a maximum vehicle speed is not selected.  1 through 7 are valid selectable speed limits. 8 through 250 are not allowed.':
                operational_min_value = 0
                operational_max_value = 7
            case '-125 to +125, negative values are reverse gears, positive values are forward gears, zero is neutral. 251 (0xFB) is park.':
                operational_min_value = -125
                operational_max_value = 251
            case '0 to 250 km/h.  251 (0xFB) is used to indicate that a maximum vehicle speed limit is not selected.':
                operational_min_value = 0
                operational_max_value = 251
            case '0xFF = no vehicle detected':
                operational_min_value = 0
                operational_max_value = 255
            case '–3200 to +3200 mm, negative values are below setpoint, positive values are above setpoint, zero is on grade.':
                operational_min_value = -3200
                operational_max_value = 3200
            case '0 to 200%, 0 to 99% indicates target is left of center, 101 to 200% indicates  target is right of center, 100% indicates target is centered, 0xFF indicates previous pass mode and thus no horizontal deviation':
                operational_min_value = 0
                operational_max_value = 255
            case '1-4':
                operational_min_value = 1
                operational_max_value = 4
            case '(upper byte resolution = 32 rpm/bit)':
                operational_min_value = 0
                operational_max_value = None
            case '0: continuous control,1 On/Off control, 2 to 250: Number of steps':
                operational_min_value = 0
                operational_max_value = 250
            case '0 to 25 sec, 0 = no override of high idle allowed, 255 = not applicable (no time restriction)':
                operational_min_value = 0
                operational_max_value = 255
            case '-200 deg (DECENT) to +301.992 deg (ASCENT)':
                operational_min_value = -200
                operational_max_value = 301.992
            case '-210 deg (SOUTH) to +211.1081215 deg (NORTH)':
                operational_min_value = -210
                operational_max_value = 211.1081215
            case '-210 deg (WEST) to +211.1081215 deg (EAST)':
                operational_min_value = 210
                operational_max_value = 211.1081215
            case 'Up to 63 Characters':
                operational_min_value = None
                operational_max_value = None
            case '0.1 s to 25 s':
                operational_min_value = 1
                operational_max_value = 25
            case '-209.7152m to 209.7152m':
                operational_min_value = -209.7152
                operational_max_value = 209.7152
            case _:
                opr = op_range.replace(' %', '')
                opr = opr.replace('%', '')
                opr = opr.replace(',', '')
                min, _, max, *_ = opr.split(' ')
                try:
                    operational_min_value = int(min)
                except ValueError:
                    operational_min_value = float(min)
                try:
                    operational_max_value = int(max)
                except ValueError:
                    operational_max_value = float(max)
    return operational_min_value, operational_max_value

def _map_units(unit):
    _unit = None
    if unit is not None:
        match unit:
            case 'bit' | 'bit-mapped':
                _unit = ''
            case _:
                _unit = unit
    return _unit

def _parse_discrete_value_label(spn, spn_description):
    last_checked = 'xxx'#7750
    last_checked_reached = False
    if spn == last_checked:
        last_checked_reached = True
    if last_checked_reached:
        print(f' ##### SPN {spn} #####')
        print(spn_description)
        input()
    value_label_dict = {}

    is_decimal = False
    for line in spn_description.splitlines():
        line = (line
                .lstrip()
                .removeprefix('13 preprogrammed')
                .removesuffix('_x000D_'))

        value = None
        val = line.split(' ', 1)[0].split('-', 1)[0].split('…', 1)[0].split('..', 1)[0]
        val = val.removesuffix('b').removesuffix(':')

        if val[:2] in ['0x', '0X']:
            value = int(val, 16)
        elif val.isnumeric():
            if not is_decimal:
                try:
                    value = int(val.removesuffix('b'), 2)
                except ValueError:
                    value = int(val)
                    is_decimal = True
            else:
                value = int(val)

        if value is not None:
            try:  # try if entry exists, do nothing
                _ = value_label_dict[value]
            except KeyError:  # if it doesn't exist, add with value string
                value_label_dict[value] = line
                continue

            try:  # if entry exists, try adding additional value to list
                value_label_dict[value].append(line)
            except AttributeError:  # if not a list, make a list with the existing description and add new
                value_label_dict[value] = [value_label_dict[value]]
                value_label_dict[value].append(line)

    return value_label_dict

def parse_J1939DA(*, J1939_dir: Path, J1939DA_config: dict) -> str:
    J1939_file = J1939_dir/J1939DA_config['filename']
    J1939_wb = load_workbook(filename=J1939_file)
    J1939_sheet = J1939_wb[J1939DA_config['SPNs_and_PGNs_sheet']]
    spn_rows = J1939DA_config['SPNs_to_parse']
    cols = J1939DA_config['SPNs_and_PGNs_sheet_columns']

    J1939 = {}
    J1939_transmission_rates_dict = {}  # Mapping of [Transmission Rate] values to J1939...['tx_rate_ms']
    J1939_spn_positions_dict = {}  # Mapping of [SPN Position in PGN] values to J1939...['start_byte'], ['start_bit']
    J1939_spn_length_dict = {}  # Mapping of [SPN Length] values to J1939...['length_bits']
    J1939_resolution_dict = {}  # Mapping of [Resolution] values to J1939...['scale']
    J1939_offset_dict = {}  # Mapping of [Offset] values to J1939...['offset']
    J1939_data_range_dict = {}  # Mapping of [Data Range] values to J1939...['min_value'], ['max_value']
    J1939_operational_range_dict = {}  # Mapping of [Operational Range] values to J1939...['min_value'], ['max_value']
    J1939_unit_dict = {}  # Mapping of [Units] values to J1939...['unit']
    J1939_discrete_values_dict = {}  # Parsing of [SPN Description] values to identify J1939...['discrete_values']


    for n in range(spn_rows['first_row'], spn_rows['last_row'] + 1):
        try:
            _ = J1939[J1939_sheet[f"{cols['PGN']}{n}"].value]
        except KeyError:
            transmission_rate_ms = _map_transmission_rate(J1939_sheet[f"{cols['Transmission Rate']}{n}"].value)
            J1939_transmission_rates_dict[J1939_sheet[f"{cols['Transmission Rate']}{n}"].value] = transmission_rate_ms

            J1939[J1939_sheet[f"{cols['PGN']}{n}"].value] = {
                'Parameter Group Label': J1939_sheet[f"{cols['Parameter Group Label']}{n}"].value,
                'Acronym': J1939_sheet[f"{cols['Acronym']}{n}"].value,
                'PGN Description': J1939_sheet[f"{cols['PGN Description']}{n}"].value,
                'PGN Data Length': J1939_sheet[f"{cols['PGN Data Length']}{n}"].value \
                    if J1939_sheet[f"{cols['PGN Data Length']}{n}"].value != 'Variable' else 8,
                'Default Priority': J1939_sheet[f"{cols['Default Priority']}{n}"].value,
                'Transmission Rate': J1939_sheet[f"{cols['Transmission Rate']}{n}"].value,
                'transmission_rate_ms': transmission_rate_ms,
                'SPNs': {}
            }

    for n in range(spn_rows['first_row'], spn_rows['last_row'] + 1):
        J1939[J1939_sheet[f"{cols['PGN']}{n}"].value]['SPNs'][J1939_sheet[f"{cols['SPN']}{n}"].value] = {
            'SPN Name': J1939_sheet[f"{cols['SPN Name']}{n}"].value,
            'SPN Description': J1939_sheet[f"{cols['SPN Description']}{n}"].value,
            'SPN Position in PGN': J1939_sheet[f"{cols['SPN Position in PGN']}{n}"].value,
            'SPN Length': J1939_sheet[f"{cols['SPN Length']}{n}"].value,
            'Resolution': J1939_sheet[f"{cols['Resolution']}{n}"].value,
            'Offset': J1939_sheet[f"{cols['Offset']}{n}"].value,
            'Data Range': J1939_sheet[f"{cols['Data Range']}{n}"].value,
            'Operational Range': J1939_sheet[f"{cols['Operational Range']}{n}"].value,
            'Units': J1939_sheet[f"{cols['Units']}{n}"].value
        }

    pgn_count = 0
    spn_count = 0
    for pgn, pgn_spec in J1939.items():
        pgn_count += 1
        for spn, spn_spec in pgn_spec['SPNs'].items():
            spn_count += 1

            start_byte, start_bit = _map_spn_position(spn_spec['SPN Position in PGN'])
            spn_spec['start_byte'], spn_spec['start_bit'] = start_byte, start_bit
            J1939_spn_positions_dict[spn_spec['SPN Position in PGN']] = {
                'start_byte': start_byte, 'start_bit': start_bit
            }

            length_bits = _map_spn_length(spn_spec['SPN Length'])
            spn_spec['length_bits'] = length_bits
            J1939_spn_length_dict[spn_spec['SPN Length']] = length_bits

            scale = _map_resolution(spn_spec['Resolution'])
            spn_spec['scale'] = scale
            J1939_resolution_dict[spn_spec['Resolution']] = scale

            spn_spec['n_decimals'] = len(str(scale).split('.')[-1]) if str(scale).count('.') else 0

            offset = _map_offset(spn_spec['Offset'])
            spn_spec['offset'] = offset
            J1939_offset_dict[spn_spec['Offset']] = offset

            min_value, max_value = _map_data_range(spn_spec['Data Range'])
            op_min_value, op_max_value = _map_operational_range(spn_spec['Operational Range'])
            spn_spec['min_value'] = min_value if op_min_value is None else op_min_value
            if length_bits == 32 and scale not in ['ASCII']:
                spn_spec['max_value'] = 100_000 / scale
            else:
                spn_spec['max_value'] = max_value if op_max_value is None else op_max_value

            J1939_data_range_dict[spn_spec['Data Range']] = {'min_value': min_value, 'max_value': max_value}
            J1939_operational_range_dict[spn_spec['Operational Range']] = {
                'min_value': op_min_value, 'max_value': op_max_value
            }

            unit = _map_units(spn_spec['Units'])
            spn_spec['unit'] = unit
            J1939_unit_dict[spn_spec['Units']] = unit

            if spn_spec['Units'] in ['bit', 'bit-mapped'] and spn not in ignore_discrete_value_spns:
                value_label_dict = _parse_discrete_value_label(spn, spn_spec['SPN Description'])

                J1939_discrete_values_dict[spn] = {'scale': scale} | dict.fromkeys(range(2 ** spn_spec['length_bits']))

                if spn in bit_mapped_spns:
                    spn_spec['scale'] = 'BIT_MAPPED'
                    J1939_discrete_values_dict[spn] = {'scale': 'BIT_MAPPED'}

                spn_spec['discrete_values'] = {}

                for value, labels in value_label_dict.items():
                    spn_spec['discrete_values'][value] = labels
                    J1939_discrete_values_dict[spn][value] = labels


    def save_json(file: Path, J1939_dict: dict):
        with file.open('w', encoding='utf-8') as f:
            json.dump(J1939_dict, f, indent=4, ensure_ascii=False)
    base_filename = J1939DA_config['filename'].removesuffix('.xlsx')
    save_json(J1939_dir/f'{base_filename}.json', J1939)
    save_json(J1939_dir/f'{base_filename}_transmission_rates.json', J1939_transmission_rates_dict)
    save_json(J1939_dir/f'{base_filename}_spn_positions.json', J1939_spn_positions_dict)
    save_json(J1939_dir/f'{base_filename}_spn_lengths.json', J1939_spn_length_dict)
    save_json(J1939_dir/f'{base_filename}_resolutions.json', J1939_resolution_dict)
    save_json(J1939_dir/f'{base_filename}_offsets.json', J1939_offset_dict)
    save_json(J1939_dir/f'{base_filename}_data_ranges.json', J1939_data_range_dict)
    save_json(J1939_dir/f'{base_filename}_operational_ranges.json', J1939_operational_range_dict)
    save_json(J1939_dir/f'{base_filename}_units.json', J1939_unit_dict)
    save_json(J1939_dir/f'{base_filename}_discrete_values.json', J1939_discrete_values_dict)

    J1939_pkl = J1939_dir/'J1939.pkl'
    with J1939_pkl.open('wb') as f:
        pickle.dump(J1939, f)

    return f'processed {pgn_count} PGNs and {spn_count} SPNs'

def raw_min_value(*, signal_spec: dict):
    min_value = encode(decoded_value=signal_spec['min_value'], offset=signal_spec['offset'], scale=signal_spec['scale'])
    return min_value

def raw_max_value(*, signal_spec: dict):
    max_value = encode(decoded_value=signal_spec['max_value'], offset=signal_spec['offset'], scale=signal_spec['scale'])
    return max_value

def decode(*, raw_value, scale, offset):
    return raw_value * scale + offset

def encode(*, decoded_value, scale, offset):
    return round((decoded_value - offset) / scale)

def get_label(*, signal_spec: dict, value: int):
    try:
        return signal_spec['discrete_values'][value]
    except KeyError:
        return ''

def get_label_value(*, signal_spec: dict, label: str):
    for value, _label in signal_spec['discrete_values'].items():
        if label == _label:
            return value
