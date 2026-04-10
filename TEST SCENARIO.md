

1. открыть http://127.0.0.1:8008/docs

1. попробуем ендпоинты, которые не требуют аутентификацию
    - `POST /user` . Создадим юзера. Нужно запомнить емейл и пароль.
**Response:** 200
    - кнопка Authorize. Ввести здесь емейл и пароль. Должна появиться надпись Authorized.

1. после авторизации попробуем создать заказ
    - `POST /order`
**Response:** 200

1. попробуем прочитать чужой заказ
    - `GET /order/1`
**Response:** 403

1. попробуем создать новую роль
    - `POST /role`
**Response:** 403

1. авторизуемся как админ
    - кнопка Authorize. Ввести здесь емейл "admin@example.com" и пароль "1". Должна появиться надпись Authorized.

1. попробуем создать новую роль "manager"
    - `POST /role` Нужно запомнить id новой роли
**Response:** 200

1. создадим пользователя с этой ролью
    - `POST /admin/user` Указать id новой роли. Запомнить емейл (например "manager@example.com") и пароль (например "1").
**Response:** 200

1. получим список всех бизнес элементов, запомним id элемента "Order Management"
    - `GET /admin/business_elements`
**Response:** 200

1. выдадим права для роли "manager" на чтение всех заказов
    - `POST /admin/access_rule`
json
{
  "role_id": 3,   это id роли "менеджер"
  "business_element_id": 2,  это id бизнес элемента "Order Management"
  "read_all_permission": true
}
**Response:** 200

1. авторизуемся как менеджер
    - кнопка Authorize. Ввести здесь емейл "manager@example.com" и пароль "1". Должна появиться надпись Authorized.

1. попробуем прочитать чужой заказ как менеджер
    - `GET /order/1`
**Response:** 200

1. попробуем удалить чужой заказ как менеджер
    - `DELETE /order/1`
**Response:** 403