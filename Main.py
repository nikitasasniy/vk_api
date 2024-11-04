import json
import argparse
from VKUser import VKUser

def get_token(token_file):
    with open(token_file, 'r') as f:
        return f.read().strip()

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def main(token_file, user_id, output_file):
    token = get_token(token_file)
    vk_user = VKUser(token, user_id)
    user_data = vk_user.get_user_info()

    if user_data:
        save_to_json(user_data, output_file)
        print(f"Информация сохранена в файл {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Получение информации о пользователе ВКонтакте.")
    parser.add_argument('token_file', type=str, help="Путь к файлу с токеном")
    parser.add_argument('--user_id', type=str, default="geroykachalki", help="ID пользователя или никнейм (по умолчанию 'geroykachalki')")
    parser.add_argument('--output_file', type=str, default='user_info.json', help="Путь к файлу для сохранения информации (по умолчанию 'user_info.json')")

    args = parser.parse_args()
    main(args.token_file, args.user_id, args.output_file)
