import io
import logging

from feedpulse.logging import RedactingFormatter, configure_logging

TOKEN = "123456789:super-secret-token"


def test_formatter_redacts_token_from_message_and_exception():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(RedactingFormatter("%(message)s", (TOKEN,)))
    logger = logging.getLogger("feedpulse.test.redaction")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)

    try:
        raise RuntimeError(f"request failed: https://api.telegram.org/bot{TOKEN}/getMe")
    except RuntimeError:
        logger.exception("Bot request with token %s failed", TOKEN)

    output = stream.getvalue()
    assert TOKEN not in output
    assert output.count("[REDACTED]") == 2


def test_configure_logging_suppresses_http_request_logs():
    configure_logging("DEBUG", TOKEN)

    assert logging.getLogger().level == logging.DEBUG
    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("httpcore").level == logging.WARNING
