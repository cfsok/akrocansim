J1939 = {}

def decode(*, raw_value, scale, offset):
    return raw_value * scale + offset

def encode(*, decoded_value, scale, offset):
    return round((decoded_value - offset) / scale)

def get_label(*, pgn, spn, raw_value):
    try:
        return J1939[pgn]['SPNs'][spn]['discrete_values'][raw_value]
    except KeyError:
        return ''

def get_label_value(*, pgn, spn, label):
    for value, _label in J1939[pgn]['SPNs'][spn]['discrete_values'].items():
        if label == _label:
            return value

if __name__ == '__main__':
    assert -40 == decode(raw_value=0, scale=0.5, offset=-40)
    assert -40 == decode(raw_value=0, scale=1, offset=-40)
    assert -40 == decode(raw_value=0, scale=2, offset=-40)
    assert -20 == decode(raw_value=40, scale=0.5, offset=-40)
    assert 0 == decode(raw_value=40, scale=1, offset=-40)
    assert 40 == decode(raw_value=40, scale=2, offset=-40)
    assert -38 == decode(raw_value=1, scale=2, offset=-40)

    assert 0 == encode(decoded_value=-40, scale=0.5, offset=-40)
    assert 0 == encode(decoded_value=-40, scale=1, offset=-40)
    assert 0 == encode(decoded_value=-40, scale=2, offset=-40)
    assert 40 == encode(decoded_value=-20, scale=0.5, offset=-40)
    assert 40 == encode(decoded_value=0, scale=1, offset=-40)
    assert 40 == encode(decoded_value=40, scale=2, offset=-40)
    assert 1 == encode(decoded_value=-38, scale=2, offset=-40)
