import vk_api
import json


# Авторизация через токен
def auth(token):
    vk_session = vk_api.VkApi(token=token)
    return vk_session.get_api()


# Получение информации о подписчиках по их ID
def get_users_info(vk, user_ids):
    if user_ids:
        users_info = vk.users.get(user_ids=','.join(map(str, user_ids)))
        return [{"id": user['id'], "name": f"{user['first_name']} {user['last_name']}"} for user in users_info]
    return []


# Получение информации о группах по их ID
def get_groups_info(vk, group_ids):
    if group_ids:
        groups_info = vk.groups.getById(group_ids=','.join(map(str, group_ids)))
        return [{"id": group['id'], "name": group['name']} for group in groups_info]
    return []


# Получение информации о пользователе, фолловерах, подписках и группах
def get_user_info(vk, user_id):
    # Получаем информацию о пользователе
    user_info = vk.users.get(user_ids=user_id, fields="followers_count")[0]

    # Получаем список ID подписчиков
    followers_ids = vk.users.getFollowers(user_id=user_info['id'])['items']

    # Получаем информацию о подписчиках (их имена)
    followers = get_users_info(vk, followers_ids)

    # Получаем подписки пользователя (люди и группы)
    subscriptions = vk.users.getSubscriptions(user_id=user_info['id'])

    # Получаем информацию о группах, на которые подписан пользователь
    group_ids = subscriptions.get('groups', {}).get('items', [])
    group_info = get_groups_info(vk, group_ids) if group_ids else []

    # Добавляем количество подписчиков и подписок
    data = {
        "user": user_info,
        "followers_count": len(followers),
        "subscriptions_count": len(subscriptions.get('groups', {}).get('items', [])),
        "followers": followers,
        "subscriptions": {
            "groups": group_info
        }
    }

    return data


# Сохранение информации в JSON-файл с отступами и читаемым текстом
def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def main():
    token = "vk1.a.X533zSrleAIV9ckSzy4vu8B7fbGFeMo785bLk7fUYAIlfT74Gn9E-8TdW0KbfCPGQ7ZwHoC6cJv45RcjZy5AzIK4BN8Q2xPvPt7-EZls5U7VjbtpBZ8RtfykeMdnUuNYVcpdeyL7wckG4OcXibdQSxBWsLFTMQK7gDer2crhsrN5Hg-L7Z-x5GnjEQA5hn3_"  # Вставьте сюда свой токен
    user_id = "geroykachalki"  # Укажите короткое имя пользователя

    vk = auth(token)
    user_data = get_user_info(vk, user_id)

    save_to_json(user_data, 'user_info.json')
    print("Информация сохранена в файл user_info.json")


if __name__ == "__main__":
    main()
