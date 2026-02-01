"""Phone number formatting utilities."""


def format_us_phone(number: str) -> str:

    """Format US phone number to +1 (XXX) XXX-XXXX.

    Args:
        number: Phone number string (with or without country code)

    Returns:
        Formatted phone number string
    """
    # Extract only digits
    digits = "".join(c for c in str(number) if c.isdigit())

    # Handle 10-digit US number
if len(digits) == 10:
        return f"+1 ({digits[:3]}) {digits[3:6]}-{digits[6:]}"

    # Handle 11-digit with leading 1
elif len(digits) == 11 and digits[0] == "1":
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"

    # Fallback for international or malformed
else:
        return f"+{digits}" if digits else number


def format_phone_display(number: str, country: str = "US") -> str:

    """Format phone number based on country.

    Args:
        number: Phone number string
        country: Country code (default US)

    Returns:
        Formatted phone number
    """
if country.upper() == "US":
        return format_us_phone(number)

    # For other countries, just ensure + prefix
    digits = "".join(c for c in str(number) if c.isdigit())
    return f"+{digits}" if digits and not str(number).startswith("+") else str(number)


def get_plain_number(formatted: str) -> str:

    """Extract plain digits from formatted number.

    Args:
        formatted: Formatted phone number

    Returns:
        Plain digit string
    """
    return "".join(c for c in str(formatted) if c.isdigit())