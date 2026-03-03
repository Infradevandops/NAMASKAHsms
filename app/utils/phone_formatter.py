"""Phone number formatting utilities."""


def format_us_phone(number: str) -> str:
    """Format US phone number to +1 (XXX) XXX-XXXX."""
    digits = "".join(c for c in str(number) if c.isdigit())

    if len(digits) == 10:
        return f"+1 ({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == "1":
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return f"+{digits}" if digits else number


def format_phone_display(number: str, country: str = "US") -> str:
    """Format phone number based on country."""
    if country.upper() == "US":
        return format_us_phone(number)

    digits = "".join(c for c in str(number) if c.isdigit())
    return f"+{digits}" if digits and not str(number).startswith("+") else str(number)


def get_plain_number(formatted: str) -> str:
    """Extract plain digits from formatted number."""
    return "".join(c for c in str(formatted) if c.isdigit())
