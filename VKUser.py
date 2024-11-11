import requests
import logging

class VKUser:
    BASE_URL = 'https://api.vk.com/method/'
    API_VERSION = '5.131'

    def __init__(self, token, user_id="geroykachalkalki"):
        self.token = token
        user_id_str = str(user_id)
        self.user_id = self.get_user_id_by_nickname(user_id_str) if not user_id_str.isdigit() else user_id_str
        logging.info(f"Создан VKUser для ID пользователя: {self.user_id}")

    def _make_request(self, method, params):
        """Вспомогательный метод для выполнения запросов к VK API."""
        url = f"{self.BASE_URL}{method}"
        params.update({'access_token': self.token, 'v': self.API_VERSION})
        logging.debug(f"Запрос к VK API: {url} с параметрами {params}")
        response = requests.get(url, params=params).json()

        # Проверка на ошибки
        if 'error' in response:
            error = response['error']
            logging.error(f"Ошибка {error['error_code']}: {error.get('error_msg', 'Неизвестная ошибка')}")
            if error['error_code'] == 18:
                logging.warning(f"Пользователь с ID {params.get('user_ids')} был удален или заблокирован.")
                return None
            raise ValueError(f"Ошибка {error['error_code']}: {error.get('error_msg', 'Неизвестная ошибка')}")

        return response.get('response', [])

    def get_user_id_by_nickname(self, nickname):
        """Получить ID пользователя по никнейму."""
        response = self._make_request('users.get', {'user_ids': nickname})
        if response:
            user_id = response[0].get('id')
            logging.info(f"Получен ID пользователя: {user_id} для никнейма: {nickname}")
            return user_id
        logging.warning(f"Не удалось получить ID для никнейма: {nickname}")
        return None

    def get_user_info(self):
        """Получить основную информацию о пользователе и его подписках и фолловерах."""
        user_info = self._make_request('users.get', {
            'user_ids': self.user_id,
            'fields': 'followers_count,home_town,sex,first_name,last_name,screen_name'
        })

        # Проверяем, что информация получена корректно
        if not user_info or 'id' not in user_info[0]:
            logging.error(f"Не удалось получить информацию о пользователе с ID: {self.user_id}")
            return {}

        user_info = user_info[0]
        logging.debug(f"Получена информация о пользователе: {user_info}")

        # Проверка имени и фамилии
        first_name = user_info.get('first_name', 'Без имени')
        last_name = user_info.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()

        # Логируем, что получены имя и фамилия
        # logging.info(f"Полное имя пользователя: {full_name}")

        # # Проверка имени и фамилии
        # if not first_name and not last_name:
        #     logging.warning(f"Имя и фамилия отсутствуют для пользователя с ID: {self.user_id}")

        followers = self.get_followers()
        subscriptions = self.get_subscriptions()

        return {
            "user": {
                "id": user_info.get("id"),
                "first_name": user_info.get('first_name', 'Без имени'),
                "last_name":user_info.get('last_name', ''),
                "home_town": user_info.get("home_town", "Не указан"),
                "sex": "Мужской" if user_info.get("sex") == 2 else "Женский" if user_info.get(
                    "sex") == 1 else "Не указан",
                "screen_name": user_info.get("screen_name", "Не указан")
            },
            "followers_count": len(followers),
            "subscriptions_count": len(subscriptions),
            "followers": followers,
            "subscriptions": {"groups": subscriptions}
        }


    def get_followers(self):
        """Получить фолловеров пользователя с пагинацией."""
        followers = []
        offset = 0
        while True:
            response = self._make_request('users.getFollowers', {
                'user_id': self.user_id, 'offset': offset, 'count': 200
            })
            if not response:
                break
            follower_ids = response.get('items', [])
            followers.extend(self.get_users_info(follower_ids))
            if len(follower_ids) < 200:
                break
            offset += 200
        logging.info(f"Получено {len(followers)} фолловеров для пользователя {self.user_id}")
        return followers

    def get_users_info(self, user_ids):
        """Получить информацию о нескольких пользователях по их ID."""
        if not user_ids:
            return []  # Возвращаем пустой список, если user_ids пустой

        response = self._make_request('users.get', {'user_ids': ','.join(map(str, user_ids))})
        if response is None:
            return []
        users_info = [{"id": user['id'], "name": f"{user.get('first_name', 'Без имени')} {user.get('last_name', '')}"} for user in response]
        logging.debug(f"Получена информация о пользователях: {users_info}")
        return users_info

    def get_subscriptions(self):
        """Получить группы, на которые подписан пользователь с пагинацией."""
        subscriptions = []
        offset = 0
        while True:
            response = self._make_request('users.getSubscriptions', {
                'user_id': self.user_id, 'extended': 1, 'offset': offset, 'count': 200
            })
            if not response:
                break
            group_ids = [group['id'] for group in response.get('items', [])]
            subscriptions.extend(self.get_groups_info(group_ids))
            if len(group_ids) < 200:
                break
            offset += 200
        logging.info(f"Получено {len(subscriptions)} подписок для пользователя {self.user_id}")
        return subscriptions

    def get_groups_info(self, group_ids):
        """Получить информацию о группах по ID."""
        if not group_ids:  # Проверка на пустой список group_ids
            logging.warning("Список group_ids пуст. Не удается получить информацию о группах.")
            return []

        group_ids_str = ','.join(map(str, group_ids))  # Преобразуем список в строку с разделителями
        response = self._make_request('groups.getById', {'group_ids': group_ids_str})

        if not response:
            logging.warning(f"Не удалось получить информацию о группах для group_ids: {group_ids_str}")
            return []

        groups_info = [
            {"id": group['id'], "name": group.get('name', 'Неизвестная группа'),
             "screen_name": group.get('screen_name', 'Не указан')}
            for group in response
        ]
        logging.debug(f"Получена информация о группах: {groups_info}")
        return groups_info

    def get_network_recursive(self, depth=2):
        """Рекурсивно получить фолловеров и подписки до указанной глубины."""
        result = {
            "followers": [],
            "subscriptions": []
        }
        to_process = [(self.user_id, depth)]
        processed_users = set()

        while to_process:
            current_id, current_depth = to_process.pop(0)
            if current_depth == 0 or current_id in processed_users:
                continue

            processed_users.add(current_id)

            followers = self.get_followers()
            subscriptions = self.get_subscriptions()

            result["followers"].extend(followers)
            result["subscriptions"].extend(subscriptions)

            # Добавляем фолловеров и подписчиков следующего уровня в очередь
            to_process.extend([(user['id'], current_depth - 1) for user in followers if 'id' in user])
            to_process.extend([(group['id'], current_depth - 1) for group in subscriptions if 'id' in group])

        logging.info(f"Завершено рекурсивное получение данных на глубину {depth}")
        return result