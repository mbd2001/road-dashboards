def human_format_int(num: int) -> str:
    """
    This function takes a number and converts it into a string format where
    thousands are represented with 'K', millions with 'M', and so on.

    Args:
        num (int): The number to be formatted.

    Returns:
        str: The formatted string representation of the number with SI suffix.

    Examples:
        >>> human_format_int(1000)
        '1.00K'
        >>> human_format_int(1000000)
        '1.00M'
    """

    magnitude = 0
    suffixes = ["", "K", "M", "B", "T"]

    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0

    if magnitude == 0:
        format_str = f"{num:.0f}"
    elif magnitude == 1:
        format_str = f"{num:.1f}"
    else:
        format_str = f"{num:.2f}"

    return f"{format_str}{suffixes[magnitude]}"
