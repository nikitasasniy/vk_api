import json
import requests

class VKUser:
    def __init__(self, token, user_id="geroykachalki"):
        self.token = token
        self.user_id = user_id

    def get_user_id_by_nickname(self, nickname):
        user_info_url = f'https://api.vk.com/method/users.get?user_ids={nickname}&access_token={self.token}&v=5.131'
        user_info_response = requests.get(user_info_url)
        user_info_data = user_info_response.json()

        if 'error' in user_info_data:
            print(f"Ошибка при получении ID по никнейму: {user_info_data['error']}")
            return None

        user_info = user_info_data.get('response', [None])[0]
        return user_info['id'] if user_info else None

    def get_user_info(self):
        if not self.user_id.isdigit():
            self.user_id = self.get_user_id_by_nickname(self.user_id)
            if not self.user_id:
                print("Не удалось получить ID пользователя по никнейму.")
                return

        user_info_url = f'https://api.vk.com/method/users.get?user_ids={self.user_id}&fields=followers_count&access_token={self.token}&v=5.131'
        user_info_response = requests.get(user_info_url)
        user_info_data = user_info_response.json()

        if 'error' in user_info_data:
            print(f"Ошибка при получении информации о пользователе: {user_info_data['error']}")
            return

        user_info = user_info_data.get('response', [None])[0]

        if user_info is None:
            print(f"Не удалось получить информацию о пользователе {self.user_id}. Проверьте правильность ID.")
            return

        followers = self.get_followers(user_info["id"])
        subscriptions = self.get_subscriptions(user_info["id"])

        data = {
            "user": user_info,
            "followers_count": len(followers),
            "subscriptions_count": len(subscriptions),
            "followers": followers,
            "subscriptions": {"groups": subscriptions}
        }

        return data

    def get_followers(self, user_id):
        followers_response = requests.get(
            f'https://api.vk.com/method/users.getFollowers?user_id={user_id}&access_token={self.token}&v=5.131')
        followers_data = followers_response.json()

        if 'error' in followers_data:
            print(f"Ошибка при получении фолловеров: {followers_data['error']}")
            return []

        followers_ids = followers_data.get('response', {}).get('items', [])
        return self.get_users_info(followers_ids)

    def get_users_info(self, user_ids):
        if user_ids:
            user_ids_str = ','.join(map(str, user_ids))
            users_info_url = f'https://api.vk.com/method/users.get?user_ids={user_ids_str}&access_token={self.token}&v=5.131'
            users_info_response = requests.get(users_info_url)
            return [{"id": user['id'], "name": f"{user['first_name']} {user['last_name']}"} for user in
                    users_info_response.json().get('response', [])]
        return []

    def get_subscriptions(self, user_id):
        subscriptions_response = requests.get(
            f'https://api.vk.com/method/users.getSubscriptions?user_id={user_id}&extended=1&access_token={self.token}&v=5.131')
        subscriptions_data = subscriptions_response.json()

        if 'error' in subscriptions_data:
            print(f"Ошибка при получении подписок: {subscriptions_data['error']}")
            return []

        groups_data = subscriptions_data.get('response', {}).get('items', [])
        return [{"id": group['id'], "name": group['name']} for group in groups_data]
