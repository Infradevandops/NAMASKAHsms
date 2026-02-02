
from app.utils.sanitization import (

    sanitize_email_content,
    sanitize_filename,
    sanitize_html,
    sanitize_user_input,
    validate_and_sanitize_response,
)


def test_sanitize_html():

    assert sanitize_html("<div>Safe</div>") == "&lt;div&gt;Safe&lt;/div&gt;"
    assert sanitize_html("<script>alert('xss')</script>") == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
    # Note: the regex in sanitize_html runs AFTER html.escape.
    # html.escape converts < to &lt;, so regex <script> won't match &lt;script&gt;.
    # The current implementation of sanitize_html seems to double-sanitize or expect unescaped input that regex catches...
    # BUT wait, lines 18-22 in sanitization.py run on 'sanitized' which is ALREADY escaped.
    # So valid HTML tags are already safe. The regexes might be redundant or looking for missed things?
    # Actually, simplistic regex for <script> won't match &lt;script&gt;.
    # But let's test what it does.

    assert "&lt;" in sanitize_html("<b>Bold</b>")


def test_sanitize_user_input():

    data = {
        "text": "<script>alert(1)</script>",
        "nested": {"key": "<b>bold</b>"},
        "list": ["<i>italic</i>", 123],
    }
    sanitized = sanitize_user_input(data)
    assert "&lt;script&gt;" in sanitized["text"]
    assert "&lt;b&gt;" in sanitized["nested"]["key"]
    assert "&lt;i&gt;" in sanitized["list"][0]
    assert sanitized["list"][1] == 123


def test_sanitize_email_content():

    content = "<p>Hello <b>User</b></p><script>bad</script>"
    sanitized = sanitize_email_content(content)
    assert "<p>" in sanitized  # Allowed
    assert "<b>" in sanitized  # Allowed
    assert "&lt;script&gt;" in sanitized  # Escaped


def test_validate_and_sanitize_response():

    resp = {
        "message": "<img src=x onerror=alert(1)>",
        "id": 123,
        "nested": {"description": "<b>Desc</b>"},
    }
    sanitized = validate_and_sanitize_response(resp)
    assert "&lt;img" in sanitized["message"]
    assert sanitized["id"] == 123
    assert "&lt;b&gt;" in sanitized["nested"]["description"]


def test_sanitize_filename():

    assert sanitize_filename("path/to/file.txt") == "file.txt"
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("my file?.txt") == "myfile.txt"
    assert sanitize_filename("") == "unnamed_file"
    long_name = "a" * 300 + ".txt"
    assert len(sanitize_filename(long_name)) <= 255