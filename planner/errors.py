# свои ошибки, окно их ловит и показывает сообщение, программа не падает


class PlannerError(Exception):
    # общий класс для всех наших ошибок
    pass


class ValidationError(PlannerError):
    # пользователь ввёл неверное значение
    pass


class StorageError(PlannerError):
    # не получилось прочитать или записать файл
    pass
