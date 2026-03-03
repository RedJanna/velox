"""WhatsApp message formatting helpers."""


class WhatsAppFormatter:
    """Formatter for WhatsApp-friendly output strings."""

    MAX_LENGTH = 4096

    @staticmethod
    def format_options(options: list[str]) -> str:
        """Format numbered options list for WhatsApp."""
        return "\n".join(f"{index}. {option}" for index, option in enumerate(options, start=1))

    @staticmethod
    def bold(text: str) -> str:
        """Wrap text in WhatsApp bold markup."""
        return f"*{text}*"

    @staticmethod
    def italic(text: str) -> str:
        """Wrap text in WhatsApp italic markup."""
        return f"_{text}_"

    @staticmethod
    def truncate(text: str, max_len: int = MAX_LENGTH) -> str:
        """Truncate text to WhatsApp max message length."""
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."
