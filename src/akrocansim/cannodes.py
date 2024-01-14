import threading
import time
import can


class Transmitter:
    def __init__(self, J1939: dict, bus: can.BusABC):
        self._J1939 = J1939
        self._bus = bus
        self.PGNs_pending_tx = {}

    def add_pending_tx(self, sender, app_data, pgn):
        if pgn == 'all PGNs':
            self.PGNs_pending_tx = dict.fromkeys(self.PGNs_pending_tx, True)
        else:
            self.PGNs_pending_tx[pgn] = True

    def register_tx_PGN(self, *, pgn, priority, source_address, tx_rate_ms, spns: list[int], get_data_callback):
        can_id = priority << 26 | pgn << 8 | source_address
        tx_rate_s = tx_rate_ms / 1000

        self.PGNs_pending_tx[pgn] = False

        data = [0 for _ in range(self._J1939[pgn]['PGN Data Length'])]

        def tx_pgn():
            while True:
                time.sleep(tx_rate_s)

                match get_data_callback('mode'), get_data_callback(f'{pgn} continuous tx'), self.PGNs_pending_tx[pgn]:
                    case ['Tx All', _, _] | ['Use PGN Settings', True, _]:
                        # Transmit PGN
                        pass
                    case [_, _, True]:
                        # Transmit PGN
                        self.PGNs_pending_tx[pgn] = False
                    case ['Use PGN Settings', False, False] | ['Stop All', _, False]:
                        # Do not transmit PGN
                        continue
                    case _:
                        raise ValueError('Unknown tx arbitration error')

                for spn in spns:
                    spn_raw_value_tag = str(spn)
                    spn_spec = self._J1939[pgn]['SPNs'][spn]
                    start_byte = spn_spec['start_byte']
                    match spn_spec['length_bits']:
                        case 1 | 2 | 3 | 4 | 5 | 6 | 7:
                            start_bit = spn_spec['start_bit']
                            length_bits = spn_spec['length_bits']
                            mask = 0x00
                            for i in range(length_bits):
                                mask = mask | 1 << start_bit + i
                            data[start_byte] = data[start_byte] & ~mask | get_data_callback(spn_raw_value_tag) << start_bit & mask
                        case 8:
                            data[start_byte] = get_data_callback(spn_raw_value_tag)
                        case 16:
                            data[start_byte] = get_data_callback(spn_raw_value_tag) & 0x00FF
                            data[start_byte + 1] = get_data_callback(spn_raw_value_tag) >> 8
                        case 32:
                            data[start_byte] = get_data_callback(spn_raw_value_tag) & 0x0000_00FF
                            data[start_byte + 1] = get_data_callback(spn_raw_value_tag) >> 8 & 0x00_00FF
                            data[start_byte + 2] = get_data_callback(spn_raw_value_tag) >> 16 & 0x00FF
                            data[start_byte + 3] = get_data_callback(spn_raw_value_tag) >> 24

                self._bus.send(can.Message(arbitration_id=can_id, is_extended_id=True, data=data))

        threading.Thread(target=tx_pgn, daemon=True).start()
