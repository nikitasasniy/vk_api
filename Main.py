import json
import requests


# Получение токена из файла
def get_token(token_file):
    with open(token_file, 'r') as f:
        return f.read().strip()


# Получение информации о пользователе
def get_user_info(token, user_id):
    # Если user_id - это никнейм, сначала получаем его ID
    if not user_id.isdigit():
        user_id = get_user_id_by_nickname(token, user_id)
        if not user_id:
            print("Не удалось получить ID пользователя по никнейму.")
            return

    # Запрос информации о пользователе
    user_info_url = f'https://api.vk.com/method/users.get?user_ids={user_id}&fields=followers_count&access_token={token}&v=5.131'
    user_info_response = requests.get(user_info_url)
    user_info_data = user_info_response.json()

    if 'error' in user_info_data:
        print(f"Ошибка при получении информации о пользователе: {user_info_data['error']}")
        return

    user_info = user_info_data.get('response', [None])[0]

    if user_info is None:
        print(f"Не удалось получить информацию о пользователе {user_id}. Проверьте правильность ID.")
        return

    # Получение количества фолловеров
    followers_response = requests.get(
        f'https://api.vk.com/method/users.getFollowers?user_id={user_info["id"]}&access_token={token}&v=5.131')
    followers_data = followers_response.json()

    if 'error' in followers_data:
        print(f"Ошибка при получении фолловеров: {followers_data['error']}")
        return

    followers_ids = followers_data.get('response', {}).get('items', [])

    # Получение информации о фолловерах
    followers = get_users_info(token, followers_ids)

    # Получение подписок пользователя (только группы)
    subscriptions_response = requests.get(
        f'https://api.vk.com/method/users.getSubscriptions?user_id={user_info["id"]}&extended=1&access_token={token}&v=5.131')
    subscriptions_data = subscriptions_response.json()
    # print("Ответ от API getSubscriptions:", subscriptions_data)  # Для отладки

    if 'error' in subscriptions_data:
        print(f"Ошибка при получении подписок: {subscriptions_data['error']}")
        return

    groups_data = subscriptions_data.get('response', {}).get('items', [])

    # # Проверяем, получили ли мы данные
    # if not groups_data:
    #     print("Нет подписок или информация о группах не найдена.")
    # else:
    #     print(f"Найдены группы: {groups_data}")

    # сохранить только id и name групп
    group_info = [{"id": group['id'], "name": group['name']} for group in groups_data]



    data = {
        "user": user_info,
        "followers_count": len(followers_ids),
        "subscriptions_count": len(groups_data) ,
        "followers": followers,
        "subscriptions": {
            "groups": group_info,
        }
    }

    return data


# Получение ID пользователя по никнейму
def get_user_id_by_nickname(token, nickname):
    user_info_url = f'https://api.vk.com/method/users.get?user_ids={nickname}&access_token={token}&v=5.131'
    user_info_response = requests.get(user_info_url)
    user_info_data = user_info_response.json()

    if 'error' in user_info_data:
        print(f"Ошибка при получении ID по никнейму: {user_info_data['error']}")
        return None

    user_info = user_info_data.get('response', [None])[0]
    return user_info['id'] if user_info else None


# Получение информации о фолловерах по их ID
def get_users_info(token, user_ids):
    if user_ids:
        user_ids_str = ','.join(map(str, user_ids))
        users_info_url = f'https://api.vk.com/method/users.get?user_ids={user_ids_str}&access_token={token}&v=5.131'
        users_info_response = requests.get(users_info_url)
        return [{"id": user['id'], "name": f"{user['first_name']} {user['last_name']}"} for user in
                users_info_response.json().get('response', [])]
    return []


# Получение информации о группах по их ID
def get_groups_info(token, group_ids):
    if group_ids:
        group_ids_str = ','.join(map(str, group_ids))
        groups_info_url = f'https://api.vk.com/method/groups.getById?group_ids={group_ids_str}&access_token={token}&v=5.131'
        groups_info_response = requests.get(groups_info_url)
        return [{"id": group['id'], "name": group['name']} for group in groups_info_response.json().get('response', [])]
    return []


# Сохранение информации в JSON-файл с отступами и читаемым текстом
def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def main():
    token = get_token('token.txt')  # Файл с токеном

    # Запрос ID пользователя или никнейма
    user_id = input(
        "Введите ID пользователя или никнейм (или нажмите Enter для использования 'geroykachalki'): ") or "geroykachalki"

    # Запрос пути к файлу
    output_file = input(
        "Введите путь к файлу для сохранения информации (или нажмите Enter для использования 'user_info.json'): ") or 'user_info.json'

    user_data = get_user_info(token, user_id)

    if user_data:
        save_to_json(user_data, output_file)
        print(f"Информация сохранена в файл {output_file}")


if __name__ == "__main__":
    main()
