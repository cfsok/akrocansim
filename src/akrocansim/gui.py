import webbrowser
import os

import dearpygui.dearpygui as dpg

from .__init__ import __version__, __app_name__
from .transmitter import Transmitter
from .config import Config
from . import J1939

VIEWPORT_WIDTH = 1500
VIEWPORT_HEIGHT = 650
WINDOW_WIDTH = VIEWPORT_WIDTH - 16


def _hyperlink(text, address):
    b = dpg.add_button(label=text, callback=lambda: webbrowser.open(address))
    dpg.bind_item_theme(b, "__demo_hyperlinkTheme")

class AkrocansimGui:
    def __init__(self):
        self.config = Config()
        self.transmitter = None
        self.J1939: dict = None

        self.gui_main()

    def gui_main(self):
        dpg.create_context()
        icon = os.path.join(os.path.dirname(__file__), 'resources', 'akrocansim.ico')
        dpg.create_viewport(title=__app_name__, width=VIEWPORT_WIDTH, height=VIEWPORT_HEIGHT, vsync=True,
                            small_icon=icon, large_icon=icon)

        with dpg.theme(tag="__demo_hyperlinkTheme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, [0, 0, 0, 0])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [0, 0, 0, 0])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [29, 151, 236, 25])
                dpg.add_theme_color(dpg.mvThemeCol_Text, [29, 151, 236])

        logo = os.path.join(os.path.dirname(__file__), 'resources', 'akrocansim_logo_dark.png')
        logo_width, logo_height, logo_channels, logo_data = dpg.load_image(logo)
        with dpg.texture_registry():
            dpg.add_static_texture(logo_width, logo_height, logo_data, tag='logo')

        self.make_menu_bar()
        self.load_config()

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()

        dpg.destroy_context()
        if self.config.bus is not None:
            self.config.bus.shutdown()

    def make_menu_bar(self):
        with dpg.viewport_menu_bar():
            with dpg.menu(label="Settings"):
                dpg.add_menu_item(tag='folder_explore', label='Explore configuration folder', callback=self.config.ext_browse)
                dpg.add_menu_item(tag='config_edit', label='Edit configuration', callback=self.config.ext_edit)
                dpg.add_menu_item(tag='J1939_parse', label='Parse J1939 Digital Annex', callback=self.parse_J1939DA)
                dpg.add_menu_item(tag='config_load', label='Load configuration', callback=self.load_config)
            with dpg.menu(label='Help'):
                dpg.add_menu_item(label='Talk to us',
                                  callback=lambda: webbrowser.open('https://github.com/cfsok/akrocansim/discussions'))
                dpg.add_menu_item(label='Report a problem',
                                  callback=lambda: webbrowser.open('https://github.com/cfsok/akrocansim/issues'))
                dpg.add_menu_item(label='About', callback=self.make_about_window)
            dpg.add_text('  |  ')
            dpg.add_text(tag='status_bar')

    def make_about_window(self):
        with dpg.window(label=f'About {__app_name__}', pos=(200, 100), modal=True, no_resize=True, no_move=True, autosize=True):
            with dpg.group(horizontal=True):
                with dpg.group():
                    dpg.add_text('\n\n\n\n\nakrocansim\n'
                                 f'Version {__version__}\n'
                                 'Copyright 2023 Socrates Vlassis\n\n')
                    _hyperlink('Homepage (PyPI)', 'https://pypi.org/project/akrocansim/')
                dpg.add_spacer(width=20)
                dpg.add_image('logo')
            dpg.add_separator()
            dpg.add_spacer(height=20)
            dpg.add_text('akrocansim is make possible by the following open source projects:\n')
            _hyperlink('python-can', 'https://github.com/hardbyte/python-can')
            _hyperlink('DearPyGui', 'https://github.com/hoffstadt/DearPyGui')
            _hyperlink('openpyxl', 'https://openpyxl.readthedocs.io/')

    def load_config(self):
        status_message, error_messages = self.config.load()

        dpg.set_value(item='status_bar', value=status_message)
        if 'new configuration file created' in status_message:
            instructions = 'Use the Settings menu to edit the configuration file.'
            self.show_messages([instructions])
        elif 'J1939DA has not been parsed' in status_message:
            instructions = 'Use the Settings menu to parse J1939DA and reload configuration.'
            self.show_messages([instructions])
        elif error_messages:
            if dpg.does_item_exist('J1939_window'):
                dpg.delete_item('J1939_window')
            self.show_messages(error_messages)
        else:
            self.J1939 = self.config.J1939_spec
            self.transmitter = Transmitter(self.J1939, self.config.bus)
            self.make_PGN_global_tx_management_window()
            self.make_J1939_window()

    def parse_J1939DA(self):
        parsing_result = self.config.parse_J1939DA()
        dpg.set_value(item='status_bar', value=parsing_result)

    def show_messages(self, messages: list[str]):
        if not dpg.does_item_exist('config_messages'):
            with dpg.window(pos=(0, 19), width=WINDOW_WIDTH, height=VIEWPORT_HEIGHT - 58,
                            no_move=True, no_resize=True, no_title_bar=True, no_close=True):
                dpg.add_text(tag='config_messages')
        error_text = ''
        for message in messages:
            error_text += message + '\n'*2
        dpg.set_value(item='config_messages', value=error_text)

    def make_PGN_global_tx_management_window(self):  # put user_data='all PGNs' to tag
        with dpg.window(label=self.config.bus.channel_info, width=570, no_close=True):
            with dpg.group(horizontal=True):
                dpg.add_text('Continuous J1939 PGN transmission:')
                dpg.add_radio_button(tag='global_tx_mode', items=('Stop All', 'Tx All', 'Use PGN Settings'),
                                     default_value='Stop All', horizontal=True,
                                     callback=self.global_tx_mode_changed)
            dpg.add_button(tag='global_tx_once', label='Tx All PGNs Once', callback=self.global_tx_once_invoked)

    def global_tx_mode_changed(self, sender, tx_mode, user_data):
        match tx_mode:
            case 'Stop All':
                dpg.show_item('global_tx_once')
                self.transmitter.set_tx_mode_stop()
            case 'Tx All':
                dpg.hide_item('global_tx_once')
                self.transmitter.set_tx_mode_continuous()
            case 'Use PGN Settings':
                dpg.show_item('global_tx_once')
                self.transmitter.set_tx_mode_per_PGN()

    def global_tx_once_invoked(self, sender, app_data, user_data):
        self.transmitter.set_tx_once()

    def make_J1939_window(self):
        with dpg.window(tag='J1939_window', label='J1939', width=WINDOW_WIDTH, pos=(0, 119), height=500, no_close=True):
            for pgn, spns in self.config.tx_PGNs_SPNs.items():
                self.add_pgn(pgn, spns)

    def add_pgn(self, pgn, spns: list):
        priority = self.J1939[pgn]['Default Priority']
        source_address = 0
        self.transmitter.register_tx_PGN(pgn=pgn, priority=priority, source_address=source_address,
                                         tx_rate_ms=self.J1939[pgn]['transmission_rate_ms'])

        pgn_label = (f"PGN {pgn} - CAN ID: {priority << 26 | pgn << 8 | source_address:08X} "
                     f"- {self.J1939[pgn]['Acronym']} - {self.J1939[pgn]['Parameter Group Label']}")
        with (dpg.collapsing_header(label=pgn_label, default_open=True)):

            continuous_signals_present = False
            enum_signals_present = False

            for spn in spns:
                spn_spec = self.J1939[pgn]['SPNs'][spn]
                if spn_spec['scale'] not in ['ENUM']:
                    continuous_signals_present = True
                if spn_spec['scale'] == 'ENUM':
                    enum_signals_present = True

            if continuous_signals_present:
                with dpg.table(header_row=True, resizable=True,
                               borders_outerV=True, borders_outerH=True, borders_innerH=True, borders_innerV=True):
                    dpg.add_table_column(label='REAL VALUE', width_fixed=True)
                    dpg.add_table_column(label='UNIT', width_fixed=True)
                    dpg.add_table_column(label='RAW HEX', width_fixed=True)
                    dpg.add_table_column(label='RAW DECIMAL')

                    for spn in spns:
                        spn_spec = self.J1939[pgn]['SPNs'][spn]
                        if spn_spec['scale'] not in ['ENUM']:
                            with dpg.table_row():
                                # SIGNAL - decoded value, direct entry, decrement, decrement
                                max_value = (2 ** spn_spec['length_bits'] - 1) * spn_spec['scale'] + spn_spec['offset']
                                if type(spn_spec['scale']) is int:
                                    dpg.add_input_int(tag=f'{pgn}_{spn}_input', width=140,
                                                      user_data=(pgn, spn, spn_spec),
                                                      default_value=spn_spec['min_value'],
                                                      min_value=spn_spec['offset'],
                                                      max_value=max_value,
                                                      min_clamped=True, max_clamped=True,
                                                      step=spn_spec['scale'],
                                                      callback=self.continuous_spn_input_int_changed,
                                                      on_enter=True)
                                elif type(spn_spec['scale']) is float:
                                    dpg.add_input_float(tag=f'{pgn}_{spn}_input', width=140,
                                                        user_data=(pgn, spn, spn_spec),
                                                        format=f"%.{spn_spec['n_decimals']}f",
                                                        default_value=spn_spec['min_value'],
                                                        min_value=spn_spec['offset'],
                                                        max_value=max_value,
                                                        min_clamped=True, max_clamped=True,
                                                        step=spn_spec['scale'],
                                                        callback=self.continuous_spn_input_int_changed,
                                                        on_enter=True)
                                else:
                                    raise TypeError

                                # UNIT
                                unit = spn_spec['unit']
                                dpg.add_text(f"{unit if unit is not None else ''}".ljust(10))

                                # RAW HEX
                                dpg.add_text(tag=f'{spn}_hex')

                                # RAW DECIMAL
                                min_value = J1939.raw_min_value(signal_spec=spn_spec)
                                dpg.add_slider_int(tag=str(spn), user_data=(pgn, spn, spn_spec),
                                                   label=f"SPN {spn}: {spn_spec['SPN Name']}",
                                                   min_value=min_value,
                                                   max_value=J1939.raw_max_value(signal_spec=spn_spec),
                                                   default_value=J1939.raw_min_value(signal_spec=spn_spec),
                                                   callback=self.continuous_spn_slider_changed)
                            self.continuous_spn_slider_changed(str(spn), min_value, (pgn, spn, spn_spec))

            if enum_signals_present:
                with dpg.table(header_row=True, resizable=True,
                               borders_outerV=True, borders_outerH=True, borders_innerH=True, borders_innerV=True):
                    dpg.add_table_column(label='DECIMAL', width_fixed=True)
                    dpg.add_table_column(label='BINARY', width_fixed=True)
                    dpg.add_table_column(label='HEX', width_fixed=True)
                    dpg.add_table_column(label='OPTIONS')

                    for spn in spns:
                        spn_spec = self.J1939[pgn]['SPNs'][spn]
                        if spn_spec['scale'] == 'ENUM':
                            with dpg.table_row():
                                # DECIMAL
                                dpg.add_input_int(tag=str(spn), width=140, user_data=(pgn, spn, spn_spec),
                                                  min_value=0, max_value=2 ** spn_spec['length_bits'] - 1,
                                                  min_clamped=True, max_clamped=True,
                                                  callback=self.discrete_spn_input_int_changed,
                                                  on_enter=True)

                                # BINARY
                                dpg.add_text(tag=f'{spn}_bin')

                                # HEX
                                dpg.add_text(tag=f'{spn}_hex')

                                # OPTIONS
                                labels = [label for label in spn_spec['discrete_values'].values()]
                                dpg.add_combo(tag=f'{pgn}_{spn}_combo', items=labels, user_data=(pgn, spn, spn_spec),
                                              default_value=J1939.get_label(signal_spec=spn_spec, value=0),
                                              label=f"SPN {spn}: {spn_spec['SPN Name']}",
                                              callback=self.discrete_spn_combo_changed)
                            self.discrete_spn_input_int_changed(str(spn), 0, (pgn, spn, spn_spec))

            with dpg.group(horizontal=True):
                dpg.add_text('Tx mode:')
                dpg.add_checkbox(tag=f'{pgn}_tx_mode', label='Continuous',
                                 user_data=pgn, callback=self.pgn_tx_mode_changed)
                dpg.add_spacer(width=10)
                dpg.add_input_int(label='ms', default_value=self.J1939[pgn]['transmission_rate_ms'],
                                  min_value=10, max_value=50000, min_clamped=True, max_clamped=True,
                                  step=10, step_fast=100, width=90,
                                  user_data=pgn, callback=self.pgn_tx_rate_changed)
                dpg.add_spacer(width=10)
                dpg.add_button(tag=f'{pgn}_tx_once', label='Tx Once',
                               user_data=pgn, callback=self.pgn_tx_once_invoked)

            dpg.add_spacer(height=10)

    def pgn_tx_mode_changed(self, sender, cont_tx, pgn):
        if cont_tx:
            dpg.hide_item(f'{pgn}_tx_once')
            self.transmitter.set_tx_mode_continuous(pgn)
        else:
            dpg.show_item(f'{pgn}_tx_once')
            self.transmitter.set_tx_mode_stop(pgn)

    def pgn_tx_once_invoked(self, sender, app_data, pgn):
        self.transmitter.set_tx_once(pgn)

    def pgn_tx_rate_changed(self, sender, tx_rate_ms, pgn):
        self.transmitter.modify_pgn_tx_rate(pgn, tx_rate_ms)

    def continuous_spn_slider_changed(self, sender, raw_value, pgn__spn__spn_spec):
        pgn, spn, signal_spec = pgn__spn__spn_spec
        self.transmitter.modify_pgn_data(pgn, spn, raw_value)

        decoded_value = J1939.decode(raw_value=raw_value,
                                     scale=signal_spec['scale'],
                                     offset=signal_spec['offset'])
        # :4.{len(str(J1939[pgn]['SPNs'][spn]['scale']).split('.')[1])}f
        dpg.set_value(f'{pgn}_{spn}_input', decoded_value)
        # dpg.set_item_user_data(f'{pgn}_{spn}_input', decoded_value)

        match signal_spec['length_bits']:
            case 1 | 2 | 3 | 4:
                nimble = f'{raw_value:X}'
                dpg.set_value(f'{spn}_hex', f'   [{nimble}]             ')
            case 5 | 6 | 7 | 8:
                byte = f'{raw_value:02X}'
                dpg.set_value(f'{spn}_hex', f'   [{byte}]            ')
            case 16:
                all_bytes = f'{raw_value:04X}'
                byte1 = all_bytes[2:4]
                byte2 = all_bytes[0:2]
                dpg.set_value(f'{spn}_hex', f'LSB[{byte1} {byte2}]MSB      ')
            case 32:
                all_bytes = f'{raw_value:08X}'
                byte1 = all_bytes[6:8]
                byte2 = all_bytes[4:6]
                byte3 = all_bytes[2:4]
                byte4 = all_bytes[0:2]
                dpg.set_value(f'{spn}_hex', f'LSB[{byte1} {byte2} {byte3} {byte4}]MSB')

    def continuous_spn_input_int_changed(self, sender, real_value, pgn__spn__spn_spec):
        pgn, spn, spn_spec = pgn__spn__spn_spec
        raw_value = J1939.encode(decoded_value=real_value, scale=spn_spec['scale'], offset=spn_spec['offset'])
        slider_tag = str(spn)
        dpg.set_value(slider_tag, raw_value)
        self.continuous_spn_slider_changed(slider_tag, raw_value, pgn__spn__spn_spec)

        #if new_value > old_value:
        #    ...
        #else:
        #    ...
        #    dpg.set_value(spn, dpg.get_value(spn) - 1)
        #    dpg.set_item_user_data(sender, new_value)

    def discrete_spn_input_int_changed(self, sender, raw_value, pgn__spn__spn_spec):
        pgn, spn, signal_spec = pgn__spn__spn_spec
        self.transmitter.modify_pgn_data(pgn, spn, raw_value)
        dpg.set_value(f'{pgn}_{spn}_combo', J1939.get_label(signal_spec=signal_spec, value=raw_value))

        match signal_spec['length_bits']:
            case 1 | 2 | 3 | 4 as length_bits:
                nibble = f'{raw_value:X}'
                dpg.set_value(f'{spn}_bin', f"{raw_value:0{length_bits}b}".ljust(10))
                dpg.set_value(f'{spn}_hex', f'    [{nibble}]            ')
            case 5 | 6 | 7 | 8 as length_bits:
                byte = f'{raw_value:02X}'
                dpg.set_value(f'{spn}_bin', f"{raw_value:0{length_bits}b}".ljust(10))
                dpg.set_value(f'{spn}_hex', f'   [{byte}]            ')

    def discrete_spn_combo_changed(self, sender, real_value, pgn__spn__spn_spec):
        pgn, spn, spn_spec = pgn__spn__spn_spec
        raw_value = J1939.get_label_value(signal_spec=spn_spec, label=real_value)
        input_int_widget = str(spn)
        dpg.set_value(input_int_widget, raw_value)
        self.discrete_spn_input_int_changed(input_int_widget, raw_value, pgn__spn__spn_spec)
