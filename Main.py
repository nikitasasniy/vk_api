import json
from VKUser import VKUser

def get_token(token_file):
    with open(token_file, 'r') as f:
        return f.read().strip()


def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)



token = get_token('token.txt')
user_id = input("Введите ID пользователя или никнейм (или нажмите Enter для использования 'geroykachalki'): ") or "geroykachalki"
output_file = input("Введите путь к файлу для сохранения информации (или нажмите Enter для использования 'user_info.json'): ") or 'user_info.json'

vk_user = VKUser(token, user_id)
user_data = vk_user.get_user_info()

if user_data:
    save_to_json(user_data, output_file)
    print(f"Информация сохранена в файл {output_file}")
