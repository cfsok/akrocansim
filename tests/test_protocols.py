from .. src.akrocansim.protocols.protocols import decode, encode


def test_decode():
    assert -40 == decode(raw_value=0, scale=0.5, offset=-40)
    assert -40 == decode(raw_value=0, scale=1, offset=-40)
    assert -40 == decode(raw_value=0, scale=2, offset=-40)
    assert -20 == decode(raw_value=40, scale=0.5, offset=-40)
    assert 0 == decode(raw_value=40, scale=1, offset=-40)
    assert 40 == decode(raw_value=40, scale=2, offset=-40)
    assert -38 == decode(raw_value=1, scale=2, offset=-40)

def test_encode():
    assert 0 == encode(decoded_value=-40, scale=0.5, offset=-40)
    assert 0 == encode(decoded_value=-40, scale=1, offset=-40)
    assert 0 == encode(decoded_value=-40, scale=2, offset=-40)
    assert 40 == encode(decoded_value=-20, scale=0.5, offset=-40)
    assert 40 == encode(decoded_value=0, scale=1, offset=-40)
    assert 40 == encode(decoded_value=40, scale=2, offset=-40)
    assert 1 == encode(decoded_value=-38, scale=2, offset=-40)
