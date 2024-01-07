from pathlib import Path
import pickle


class J1939:
    def __init__(self, J1939_pickle: Path):
        with J1939_pickle.open('rb') as f:
            self.spec = pickle.load(f)

    def __getitem__(self, item):
        return self.spec[item]


def decode(*, raw_value, scale, offset):
    return raw_value * scale + offset

def encode(*, decoded_value, scale, offset):
    return round((decoded_value - offset) / scale)

def get_label(*, signal_spec: dict, raw_value: int):
    try:
        return signal_spec['discrete_values'][raw_value]
    except KeyError:
        return ''

def get_label_value(*, signal_spec: dict, label: str):
    for value, _label in signal_spec['discrete_values'].items():
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