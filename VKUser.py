import requests

class VKUser:
    BASE_URL = 'https://api.vk.com/method/'
    API_VERSION = '5.131'

    def __init__(self, token, user_id="geroykachalki"):
        self.token = token
        self.user_id = self.get_user_id_by_nickname(user_id) if not user_id.isdigit() else user_id

    def _make_request(self, method, params):
        url = f"{self.BASE_URL}{method}"
        params.update({'access_token': self.token, 'v': self.API_VERSION})
        response = requests.get(url, params=params).json()

        if 'error' in response:
            error = response['error']
            raise ValueError(f"Ошибка {error['error_code']}: {error.get('error_msg', 'Неизвестная ошибка')}")
        return response.get('response', [])

    def get_user_id_by_nickname(self, nickname):
        response = self._make_request('users.get', {'user_ids': nickname})
        return response[0]['id'] if response else None

    def get_user_info(self):
        user_info = self._make_request('users.get', {
            'user_ids': self.user_id,
            'fields': 'followers_count'
        })[0]

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
        response = self._make_request('users.getFollowers', {'user_id': self.user_id})
        follower_ids = response.get('items', [])
        return self.get_users_info(follower_ids)

    def get_users_info(self, user_ids):
        if user_ids:
            response = self._make_request('users.get', {'user_ids': ','.join(map(str, user_ids))})
            return [{"id": user['id'], "name": f"{user['first_name']} {user['last_name']}"} for user in response]
        return []

    def get_subscriptions(self):
        response = self._make_request('users.getSubscriptions', {'user_id': self.user_id, 'extended': 1})
        return [{"id": group['id'], "name": group['name']} for group in response.get('items', [])]
