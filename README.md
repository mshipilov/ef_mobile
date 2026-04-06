
Иерархия проверки:
Если user.is_active — False → Отказ.
Поиск в user.role.permissions → Если найдена пара resource_name + action → Доступ разрешен.