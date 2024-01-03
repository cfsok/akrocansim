import threading
import time
import can


bus: can.BusABC = None
J1939 = {}
PGNs_pending_tx = {}


def add_pending_tx(sender, app_data, pgn):
    global PGNs_pending_tx
    if pgn == 'all PGNs':
        PGNs_pending_tx = dict.fromkeys(PGNs_pending_tx, True)
    else:
        PGNs_pending_tx[pgn] = True


def start_pgn_tx(*, pgn, priority, source_address, tx_rate_ms, spns: list[int], get_value_fn):
    can_id = priority << 26 | pgn << 8 | source_address
    tx_rate_s = tx_rate_ms / 1000

    PGNs_pending_tx[pgn] = False

    data = [0 for _ in range(J1939[pgn]['PGN Data Length'])]

    def tx_pgn():
        while True:
            time.sleep(tx_rate_s)

            match get_value_fn('mode'), get_value_fn(f'{pgn} continuous tx'), PGNs_pending_tx[pgn]:
                case ['Tx All', _, _] | ['Use PGN Settings', True, _]:
                    # Transmit PGN
                    pass
                case [_, _, True]:
                    # Transmit PGN
                    PGNs_pending_tx[pgn] = False
                case ['Use PGN Settings', False, False] | ['Stop All', _, False]:
                    # Do not transmit PGN
                    continue
                case _:
                    raise ValueError('Unknown tx arbitration error')

            for spn in spns:
                spn_raw_value_tag = f'{spn}_raw_value'
                spn_spec = J1939[pgn]['SPNs'][spn]
                start_byte = spn_spec['start_byte']
                match spn_spec['length_bits']:
                    case 1 | 2 | 3 | 4 | 5 | 6 | 7:
                        start_bit = spn_spec['start_bit']
                        length_bits = spn_spec['length_bits']
                        mask = 0x00
                        for i in range(length_bits):
                            mask = mask | 1 << start_bit + i
                        data[start_byte] = data[start_byte] & ~mask | get_value_fn(spn_raw_value_tag) << start_bit & mask
                    case 8:
                        data[start_byte] = get_value_fn(spn_raw_value_tag)
                    case 16:
                        data[start_byte] = get_value_fn(spn_raw_value_tag) & 0x00FF
                        data[start_byte + 1] = get_value_fn(spn_raw_value_tag) >> 8
                    case 32:
                        data[start_byte] = get_value_fn(spn_raw_value_tag) & 0x0000_00FF
                        data[start_byte + 1] = get_value_fn(spn_raw_value_tag) >> 8 & 0x00_00FF
                        data[start_byte + 2] = get_value_fn(spn_raw_value_tag) >> 16 & 0x00FF
                        data[start_byte + 3] = get_value_fn(spn_raw_value_tag) >> 24

            if bus is not None:
                bus.send(can.Message(arbitration_id=can_id, is_extended_id=True, data=data))
            else:
                print('CAN ID:', f'{can_id:08X}', '  DATA:', data)

    threading.Thread(target=tx_pgn, daemon=True).start()
