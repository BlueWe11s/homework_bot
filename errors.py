class UndocumentedStatusError(Exception):
    """Недокументированный статус."""


class IncorrectStatusRequest(Exception):
    """Статус запроса не 200."""


class IncorrectAPIRequest(Exception):
    """Ошибка при выполнении запроса."""


class MessageSendError(Exception):
    """Ошибка отправки сообщения."""
