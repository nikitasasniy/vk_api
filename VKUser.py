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
        if response is None:
            return None
        user_id = response[0].get('id')
        logging.info(f"Получен ID пользователя: {user_id} для никнейма: {nickname}")
        return user_id

    def get_user_info(self):
        """Получить основную информацию о пользователе и его подписках и фолловерах."""
        user_info = self._make_request('users.get', {
            'user_ids': self.user_id,
            'fields': 'followers_count'
        })

        if not user_info or 'id' not in user_info[0]:
            logging.error(f"Не удалось получить информацию о пользователе с ID: {self.user_id}")
            return {}

        user_info = user_info[0]
        followers = self.get_followers()
        subscriptions = self.get_subscriptions()

        return {
            "user": user_info,
            "followers_count": len(followers),
            "subscriptions_count": len(subscriptions),
            "followers": followers,
            "subscriptions": {"groups": subscriptions}
        }

    def get_followers(self):
        """Получить фолловеров пользователя."""
        response = self._make_request('users.getFollowers', {'user_id': self.user_id})
        if response is None:
            return []
        follower_ids = response.get('items', [])
        followers = self.get_users_info(follower_ids)
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
        """Получить группы, на которые подписан пользователь."""
        response = self._make_request('users.getSubscriptions', {'user_id': self.user_id, 'extended': 1})
        if response is None:
            return []
        subscriptions = [{"id": group['id'], "name": group.get('name', 'Неизвестная группа')} for group in response.get('items', [])]
        logging.info(f"Получено {len(subscriptions)} подписок для пользователя {self.user_id}")
        return subscriptions

    def get_followers_and_subscriptions_recursive(self, depth=2):
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
