from VKUser import VKUser
import logging
from VKNeo4jDB import VKNeo4jDB

class DataCollector:
    def __init__(self, vk_user, db, depth=2):
        self.vk_user = vk_user
        self.db = db
        self.depth = depth

    def collect_user_data(self, collected_users=None):
        if collected_users is None:
            collected_users = {}
        self._collect_user_data_recursive(self.vk_user, self.depth, collected_users)

    def _collect_user_data_recursive(self, vk_user, depth, collected_users):
        if depth == 0:
            return

        user_data = vk_user.get_user_info()

        if "user" not in user_data:
            logging.error(f"Не удалось получить данные о пользователе: {user_data}")
            return

        user_info = user_data["user"]
        user_id = user_info.get("id")

        # Сохраняем пользователя в collected_users, если его еще нет
        if user_id not in collected_users:
            collected_users[user_id] = {
                "name": f"{user_info.get('first_name', 'Без имени')} {user_info.get('last_name', '')}",
                "followers_count": user_data.get("followers_count", 0),
                "subscriptions_count": user_data.get("subscriptions_count", 0),
                "screen_name": user_info.get("screen_name", "Нет ника"),
            }

            # Создаем узел пользователя в базе данных
            self._create_user_in_db(user_id, collected_users[user_id])
            logging.info(f"Пользователь {user_info['first_name']} {user_info['last_name']} добавлен в базу данных.")

        followers = vk_user.get_followers()
        subscriptions = vk_user.get_subscriptions()

        # Рекурсивно обрабатываем фолловеров
        for follower in followers:
            follower_id = follower.get("id")
            follower_first_name = follower.get("first_name", "Без имени")
            follower_last_name = follower.get("last_name", "")

            if follower_id is not None:
                follower_vk_user = VKUser(vk_user.token, follower_id)
                self._collect_user_data_recursive(follower_vk_user, depth - 1, collected_users)

                # Создаем отношение FOLLOWS
                self.db.create_follow_relationship(user_id, follower_id)
                logging.info(f"{user_info['first_name']} {user_info['last_name']} фолловит {follower_first_name} {follower_last_name}.")
            else:
                logging.warning(f"Фолловер не имеет ID: {follower}")

        # Рекурсивно обрабатываем подписки
        for subscription in subscriptions:
            group_vk_user = VKUser(vk_user.token, subscription["id"])
            self._collect_user_data_recursive(group_vk_user, depth - 1, collected_users)

            # Создаем узел группы в базе данных
            self._create_group_in_db(subscription)

            # Создаем отношение SUBSCRIBES
            self.db.create_subscribe_relationship(user_id, subscription["id"])
            logging.info(f"{user_info['first_name']} {user_info['last_name']} подписан на группу {subscription['name']}.")

    def _create_user_in_db(self, user_id, user_info):
        """Создает узел пользователя в базе данных Neo4j."""
        try:
            self.db.create_user_node({
                "id": user_id,
                "name": user_info["name"],
                "screen_name": user_info["screen_name"],
                "sex": user_info.get("sex", "unknown"),  # Добавлено поле sex
                "home_town": user_info.get("home_town", "unknown")  # Добавлено поле home_town
            })
        except ValueError as e:
            logging.error(f"Ошибка при создании узла пользователя: {e}")

    def _create_group_in_db(self, subscription):
        """Создает узел группы в базе данных Neo4j."""
        try:
            self.db.create_group_node({
                "id": subscription["id"],
                "name": subscription["name"],
                "screen_name": subscription.get("screen_name", "Нет ника")
            })
        except ValueError as e:
            logging.error(f"Ошибка при создании узла группы: {e}")
