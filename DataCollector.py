from VKUser import VKUser
import logging
from VKNeo4jDB import VKNeo4jDB

class DataCollector:
    def __init__(self, vk_user, db, depth=2):
        self.vk_user = vk_user
        self.db = db
        self.depth = depth

    def collect_user_data(self, collected_users=None):
        """Собирает данные о пользователе и его связях рекурсивно."""
        if collected_users is None:
            collected_users = {}
        self._collect_user_data_recursive(self.vk_user, self.depth, collected_users)

    def _collect_user_data_recursive(self, vk_user, depth, collected_users):
        """Рекурсивно собирает данные о пользователе ВКонтакте до заданной глубины."""
        if depth == 0:
            return

        user_data = vk_user.get_user_info()
        if "user" not in user_data:
            logging.error(f"Не удалось получить данные о пользователе с ID: {vk_user.user_id}")
            return

        user_info = user_data["user"]
        user_id = user_info.get("id")

        # Проверка имени и фамилии
        first_name = user_info.get("first_name", 'Без имени')
        last_name = user_info.get("last_name", '')
        full_name = f"{first_name} {last_name}".strip()

        logging.info(f"______________First Name: {first_name}, Last Name: {last_name}")

        # Логируем, что получены имя и фамилия
        logging.info(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!Полное имя пользователя: {full_name}")

        # Проверка на случай, если имя или фамилия отсутствуют
        if not first_name and not last_name:
            logging.warning(f"Имя и фамилия отсутствуют для пользователя с ID: {user_id}")

        if user_id not in collected_users:
            collected_users[user_id] = {
                "name": full_name if full_name else 'Без имени',
                "followers_count": user_data.get("followers_count", 0),
                "subscriptions_count": user_data.get("subscriptions_count", 0),
                "screen_name": user_info.get("screen_name", "Нет ника"),
                "sex": user_info.get("sex", "Неизвестно"),
                "home_town": user_info.get("home_town", "Не указан"),
            }

            # Создаем узел пользователя в базе данных
            self._create_user_in_db(user_id, collected_users[user_id])
            logging.info(f"Пользователь {first_name} {last_name} добавлен в базу данных.")

        followers = vk_user.get_followers()
        subscriptions = vk_user.get_subscriptions()

        for follower in followers:
            follower_id = follower.get("id")
            if follower_id is not None:
                follower_vk_user = VKUser(vk_user.token, follower_id)
                self._collect_user_data_recursive(follower_vk_user, depth - 1, collected_users)

                # Создаем отношение FOLLOWS
                self.db.create_follow_relationship(user_id, follower_id)
                logging.info(f"Создано отношение FOLLOWS между пользователем {user_id} и фолловером {follower_id}.")
            else:
                logging.warning(f"Фолловер без ID: {follower}")

        for subscription in subscriptions:
            group_id = subscription.get("id")
            if group_id is not None:
                # Создаем группу в базе данных
                self._create_group_in_db(subscription)
                # Создаем отношение SUBSCRIBES
                self.db.create_subscribe_relationship(user_id, group_id)
                logging.info(f"Создано отношение SUBSCRIBES между пользователем {user_id} и группой {group_id}.")
            else:
                logging.warning(f"Подписка без ID: {subscription}")

    def _create_user_in_db(self, user_id, user_info):
        """Создает узел пользователя в базе данных Neo4j, добавляя все доступные данные."""
        try:
            self.db.create_user_node({
                "id": user_id,
                "name": user_info["name"],
                "screen_name": user_info["screen_name"],
                "sex": user_info.get("sex", "unknown"),
                "home_town": user_info.get("home_town", "unknown"),
                "followers_count": user_info.get("followers_count", 0),
                "subscriptions_count": user_info.get("subscriptions_count", 0),
            })
        except ValueError as e:
            logging.error(f"Ошибка при создании узла пользователя с ID {user_id}: {e}")

    def _create_group_in_db(self, subscription):
        """Создает узел группы в базе данных Neo4j, добавляя все доступные данные о группе."""
        try:
            self.db.create_group_node({
                "id": subscription["id"],
                "name": subscription["name"],
                "screen_name": subscription.get("screen_name", "Нет ника")
            })
        except ValueError as e:
            logging.error(f"Ошибка при создании узла группы с ID {subscription.get('id')}: {e}")
