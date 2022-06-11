"""Мои исключения."""


class HomeworksBotError(Exception):
    """Общий класс ошибок HomeworkBot."""

    pass


class ErrorApi(HomeworksBotError):
    """Общая ошибка ответа API."""

    pass


class ErrorSendMessage(HomeworksBotError):
    """Ошибка при отправке сообщения."""

    pass


class StatusCodeError(HomeworksBotError):
    """Ошибка при запросе к основному API.
    Статус_код не 200.
    """

    pass
