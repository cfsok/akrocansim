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
