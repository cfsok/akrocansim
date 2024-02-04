def start_bit(*, signal_spec: dict):
    return signal_spec['start_byte'] * 8 + signal_spec['start_bit']

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
