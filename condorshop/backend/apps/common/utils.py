from typing import Union

Number = Union[int, float, str, None]


def format_clp(value: Number) -> str:
    """
    Convert any numeric-like value to Chilean peso format without decimals.
    Examples:
        19990      -> "$19.990"
        19990.4    -> "$19.990"
        "24990"    -> "$24.990"
        None       -> "$0"
    """
    if value in (None, "", "None"):
        number = 0
    else:
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = 0

    rounded = int(round(number))
    formatted = f"{rounded:,}".replace(",", ".")
    return f"${formatted}"


