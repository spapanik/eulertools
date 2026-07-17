from eulertools.lib.constants import NamedArgType, Prefix


def test_str() -> None:
    assert str(NamedArgType.NONE) == "none"


def test_eq_with_string() -> None:
    assert NamedArgType.SHORT == "short"


def test_eq_with_non_string() -> None:
    assert (NamedArgType.SHORT == 1) is False


def test_ne_with_string() -> None:
    assert NamedArgType.SHORT != "long"


def test_ne_with_equal_string() -> None:
    assert (NamedArgType.SHORT != "short") is False


def test_ne_with_non_string() -> None:
    assert NamedArgType.SHORT != 1


def test_hash() -> None:
    assert hash(Prefix.SUCCESS) == hash("🟢 ")
