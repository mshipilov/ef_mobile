
Иерархия проверки:
Если user.is_active — False → Отказ.
Поиск в user.role.permissions → Если найдена пара resource_name + action → Доступ разрешен.

Сценарии
Регистрация нового юзера
1. POST /profile - регистрация
2. POST /token - Получение токена
3. GET /profile - получение данных своего профайла
4. PATCH /profile - изменение данных своего профайла

Инструкция по запуску
uvicorn app.api:app  