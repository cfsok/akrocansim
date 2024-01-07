from pathlib import Path

import dearpygui.dearpygui as dpg
from can.exceptions import CanError

from . import caninterface
from . protocols import protocols
from . config import Config


J1939 = None

def set_signal_value(sender, new_value, old_value):
    pgn, spn, sender_type = sender.split('_')
    spn_spec = J1939[int(pgn)]['SPNs'][int(spn)]
    if sender_type == 'input':
        dpg.set_value(f'{spn}_raw_value', protocols.encode(decoded_value=new_value,
                                                                scale=spn_spec['scale'],
                                                                offset=spn_spec['offset']))
    elif sender_type == 'combo':
        dpg.set_value(f'{spn}_raw_value', protocols.get_label_value(signal_spec=spn_spec, label=new_value))
    #if new_value > old_value:
    #    ...
    #else:
    #    ...
    #    dpg.set_value(spn, dpg.get_value(spn) - 1)
    #    dpg.set_item_user_data(sender, new_value)

def set_label(spn, new_value, pgn):
    spn_spec = J1939[int(pgn)]['SPNs'][int(spn)]
    dpg.set_value(f'{pgn}_{spn}_combo', protocols.get_label(signal_spec=spn_spec, raw_value=new_value))

def slider_min_value(pgn, spn):
    min_value = protocols.encode(decoded_value=J1939[pgn]['SPNs'][spn]['min_value'],
                                 offset=J1939[pgn]['SPNs'][spn]['offset'],
                                 scale=J1939[pgn]['SPNs'][spn]['scale'])
    return min_value

def slider_max_value(pgn, spn):
    max_value = protocols.encode(decoded_value=J1939[pgn]['SPNs'][spn]['max_value'],
                                 offset=J1939[pgn]['SPNs'][spn]['offset'],
                                 scale=J1939[pgn]['SPNs'][spn]['scale'])
    if J1939[pgn]['SPNs'][spn]['length_bits'] < 32 or spn in [584, 585]: ###########################################################
        return max_value
    else:
        print('spn_max_value override [100_000]') ######################################################################################
        return 100_000 / J1939[pgn]['SPNs'][spn]['scale']

def add_pgn(J1939, pgn, spns: list, bus: caninterface.Bus):
    priority = J1939[pgn]['Default Priority']
    source_address = 0

    pgn_label = (f"PGN {pgn} - CAN ID: {priority << 26 | pgn << 8 | source_address:08X} "
                 f"- {J1939[pgn]['Acronym']} - {J1939[pgn]['Parameter Group Label']}")
    with (dpg.collapsing_header(label=pgn_label, default_open=True)):

        continuous_signals_present = False
        enum_signals_present = False

        for spn in spns:
            if J1939[pgn]['SPNs'][spn]['scale'] not in ['ENUM']:
                continuous_signals_present = True
            if J1939[pgn]['SPNs'][spn]['scale'] == 'ENUM':
                enum_signals_present = True

        if continuous_signals_present:
            with dpg.table(header_row=True, resizable=True,
                           borders_outerV=True, borders_outerH=True, borders_innerH=True, borders_innerV=True):
                dpg.add_table_column(label='SIGNAL', width_fixed=True)
                dpg.add_table_column(label='UNIT', width_fixed=True)
                dpg.add_table_column(label='RAW HEX', width_fixed=True)
                dpg.add_table_column(label='RAW DECIMAL')

                for spn in spns:
                    if J1939[pgn]['SPNs'][spn]['scale'] not in ['ENUM']:
                        with dpg.table_row():
                            # SIGNAL - decoded value, direct entry, decrement, decrement
                            max_value = (2 ** J1939[pgn]['SPNs'][spn]['length_bits'] - 1) \
                                        * J1939[pgn]['SPNs'][spn]['scale'] \
                                        + J1939[pgn]['SPNs'][spn]['offset']
                            if type(J1939[pgn]['SPNs'][spn]['scale']) is int:
                                dpg.add_input_int(tag=f'{pgn}_{spn}_input', width=140,
                                                  min_value=J1939[pgn]['SPNs'][spn]['offset'],
                                                  max_value=max_value,
                                                  min_clamped=True, max_clamped=True,
                                                  step=J1939[pgn]['SPNs'][spn]['scale'],
                                                  callback=set_signal_value, on_enter=True)
                            elif type(J1939[pgn]['SPNs'][spn]['scale']) is float:
                                dpg.add_input_float(tag=f'{pgn}_{spn}_input', width=140,
                                                    format=f"%.{J1939[pgn]['SPNs'][spn]['n_decimals']}f",
                                                    min_value=J1939[pgn]['SPNs'][spn]['offset'],
                                                    max_value=max_value,
                                                    min_clamped=True, max_clamped=True,
                                                    step=J1939[pgn]['SPNs'][spn]['scale'],
                                                    callback=set_signal_value, on_enter=True)
                            else:
                                raise TypeError

                            # UNIT
                            unit = J1939[pgn]['SPNs'][spn]['unit']
                            dpg.add_text(f"{unit if unit is not None else ''}".ljust(10))

                            # RAW HEX
                            dpg.add_text(tag=f'{spn}_hex')

                            # RAW DECIMAL
                            dpg.add_slider_int(tag=f'{spn}_raw_value', user_data=pgn,
                                               label=f"SPN {spn}: {J1939[pgn]['SPNs'][spn]['SPN Name']}",
                                               min_value=slider_min_value(pgn, spn),
                                               max_value=slider_max_value(pgn, spn),
                                               default_value=slider_min_value(pgn, spn))

        if enum_signals_present:
            with dpg.table(header_row=True, resizable=True,
                           borders_outerV=True, borders_outerH=True, borders_innerH=True, borders_innerV=True):
                dpg.add_table_column(label='DECIMAL', width_fixed=True)
                dpg.add_table_column(label='BINARY', width_fixed=True)
                dpg.add_table_column(label='HEX', width_fixed=True)
                dpg.add_table_column(label='OPTIONS')

                for spn in spns:
                    spn_spec = J1939[pgn]['SPNs'][spn]
                    if spn_spec['scale'] == 'ENUM':

                        with dpg.table_row():

                            # DECIMAL
                            dpg.add_input_int(tag=f'{spn}_raw_value', width=140, user_data=pgn,
                                              min_value=0, max_value=2 ** spn_spec['length_bits'] - 1,
                                              min_clamped=True, max_clamped=True,
                                              callback = set_label, on_enter = True)

                            # BINARY
                            dpg.add_text(tag=f'{spn}_bin')

                            # HEX
                            dpg.add_text(tag=f'{spn}_hex')

                            # OPTIONS
                            labels = [label for label in spn_spec['discrete_values'].values()]
                            dpg.add_combo(tag=f'{pgn}_{spn}_combo', items=labels,
                                          default_value=protocols.get_label(signal_spec=spn_spec, raw_value=0),
                                          label=f"SPN {spn}: {spn_spec['SPN Name']}",
                                          callback=set_signal_value)

        with dpg.group(horizontal=True):
            dpg.add_text('Tx mode:')
            dpg.add_checkbox(tag=f'{pgn} continuous tx', label='Continuous')
            dpg.add_button(label='Tx Once', user_data=pgn, callback=bus.add_pending_tx)

        dpg.add_spacer(height=10)

    bus.start_pgn_tx(pgn=pgn, priority=priority, source_address=source_address,
                     tx_rate_ms=J1939[pgn]['transmission_rate_ms'], spns=spns, get_value_fn=dpg.get_value)


def gui_main():
    akrocansim_dir = Path.home().joinpath('akrocansim')
    config = Config(akrocansim_dir)

    tx_PGNs_SPNs = {}

    config_loaded = False
    error_messages = ''

    if not config.config_toml.exists():
        config.bootstrap()
    else:
        config_loaded = True
        config.load()

        if not config.J1939_pickle.exists():
            error_messages += f'- J1939DA has not been parsed; {config.J1939_pickle} not found.\n'
        else:
            global J1939
            J1939 = protocols.J1939(config.J1939_pickle)
            try:
                bus = caninterface.Bus(J1939, **config['CAN_INTERFACE'])

            except CanError as e:
                error_messages += f'- CAN interface initialisation error: {e}\n'

        for pgn, spn_list in config['Tx_PGNs_SPNs'].items():
            tx_PGNs_SPNs[int(pgn)] = spn_list
        if not tx_PGNs_SPNs:
            error_messages += '- No Tx SPNs have been configured. Populate table [Tx_PGNs_SPNs] in configuration file.\n'

        if error_messages:
            error_messages = (f'The following errors have been detected:\n{error_messages}'
                              f'Follow the instructions in the configuration file and restart Akrocansim.')


    window_width = 1200
    window_height = 600
    dpg.create_context()
    dpg.create_viewport(title='Akro CAN Simulator', width=window_width, height=window_height, vsync=True)

    def make_init_buttons():
        with dpg.group(horizontal=True):
            dpg.add_button(label='Edit configuration', callback=config.ext_edit)
            dpg.add_button(label='Explore configuration folder', callback=config.ext_browse)
            if config_loaded:
                dpg.add_button(label='Parse J1939 Digital Annex',
                               callback=lambda s, a, u: dpg.set_value('parsing_result', config.parse_J1939DA()))
        dpg.add_text(tag='parsing_result')

    if not config_loaded:
        with dpg.window(label='Configuration required', width=window_width - 16, height=window_height, no_close=True):
            dpg.add_text(f'Configuration file created at: {config.config_toml}\n'
                         f'Follow the instructions in the configuration file and restart Akrocansim.')
            make_init_buttons()
    elif error_messages:
        with dpg.window(label='Configuration incomplete', width=window_width - 16, height=window_height, no_close=True):
            dpg.add_text(error_messages)
            make_init_buttons()

    # Everything correctly configured when below code runs
    else:
        try:
            window_label = ''
        except AttributeError:
            window_label = 'No Hardware Interface'
        with dpg.window(label=window_label, width=window_width - 16, no_close=True):
            with dpg.menu_bar():
                with dpg.menu(label="Settings"):
                    dpg.add_menu_item(label='Edit configuration', callback=config.ext_edit)
                    dpg.add_menu_item(label='Explore configuration folder', callback=config.ext_browse)
                    dpg.add_menu_item(label='Parse J1939 Digital Annex', callback=config.parse_J1939DA)
            with dpg.group(horizontal=True):
                dpg.add_text('Continuous J1939 PGN transmission:')
                dpg.add_radio_button(tag='mode', items=('Stop All', 'Tx All', 'Use PGN Settings'),
                                     default_value='Stop All', horizontal=True)
            dpg.add_button(label='Tx All PGNs Once', user_data='all PGNs', callback=bus.add_pending_tx)

        with dpg.window(label='J1939', width=window_width - 16, pos=(0, 100), height=500, no_close=True):
            for pgn, spns in tx_PGNs_SPNs.items():
                add_pgn(J1939, pgn, spns, bus)

    dpg.setup_dearpygui()
    dpg.show_viewport()

    if not config_loaded or error_messages:
        dpg.start_dearpygui()
    else:
        while dpg.is_dearpygui_running():
            for pgn, spns in tx_PGNs_SPNs.items():
                for spn in spns:
                    raw_value = dpg.get_value(f'{spn}_raw_value')
                    signal_spec = J1939[pgn]['SPNs'][spn]

                    if signal_spec['scale'] == 'ENUM':
                        pass
                    else:
                        decoded_value = protocols.decode(raw_value=raw_value,
                                                         scale=signal_spec['scale'],
                                                         offset=signal_spec['offset'])
                        # :4.{len(str(J1939[pgn]['SPNs'][spn]['scale']).split('.')[1])}f
                        dpg.set_value(f'{pgn}_{spn}_input', decoded_value)
                        # dpg.set_item_user_data(f'{pgn}_{spn}_input', decoded_value)

                    match signal_spec['length_bits'], signal_spec['scale']:
                        case 1 | 2 | 3 | 4 as length_bits, 'ENUM':
                            nibble = f'{raw_value:X}'
                            dpg.set_value(f'{spn}_bin', f"{raw_value:0{length_bits}b}".ljust(10))
                            dpg.set_value(f'{spn}_hex', f'    [{nibble}]            ')
                        case 5 | 6 | 7 | 8 as length_bits, 'ENUM':
                            byte = f'{raw_value:02X}'
                            dpg.set_value(f'{spn}_bin', f"{raw_value:0{length_bits}b}".ljust(10))
                            dpg.set_value(f'{spn}_hex', f'   [{byte}]            ')
                        case 1 | 2 | 3 | 4, scale if scale not in ['ENUM']:
                            nimble = f'{raw_value:X}'
                            dpg.set_value(f'{spn}_hex', f'   [{nimble}]             ')
                        case 5 | 6 | 7 | 8, scale if scale not in ['ENUM']:
                            byte = f'{raw_value:02X}'
                            dpg.set_value(f'{spn}_hex', f'   [{byte}]            ')
                        case 16, _:
                            all_bytes = f'{raw_value:04X}'
                            byte1 = all_bytes[2:4]
                            byte2 = all_bytes[0:2]
                            dpg.set_value(f'{spn}_hex', f'LSB[{byte1} {byte2}]MSB      ')
                        case 32, _:
                            all_bytes = f'{raw_value:08X}'
                            byte1 = all_bytes[6:8]
                            byte2 = all_bytes[4:6]
                            byte3 = all_bytes[2:4]
                            byte4 = all_bytes[0:2]
                            dpg.set_value(f'{spn}_hex', f'LSB[{byte1} {byte2} {byte3} {byte4}]MSB')

            dpg.render_dearpygui_frame()

    dpg.destroy_context()
    bus.shutdown()
