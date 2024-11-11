import argparse
import logging
from VKUser import VKUser
from VKNeo4jDB import VKNeo4jDB
from DataCollector import DataCollector
from JSONHandler import JSONHandler
from fastapi import FastAPI, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel
from neomodel import db

app = FastAPI()

def setup_logging(log_file):
    """Настройка логирования в файл."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def main(token_file, user_id, output_file, query_type):
    # Настройка логирования
    setup_logging("app.log")

    token = JSONHandler.get_token(token_file)
    vk_user = VKUser(token, user_id)
    user_data = vk_user.get_user_info()

    if user_data:
        # Сохранение данных в JSON
        JSONHandler.save_to_json(user_data, output_file)
        logging.info(f"Информация сохранена в файл {output_file}")

        # Подключение к Neo4j и сбор данных
        db = VKNeo4jDB("bolt://localhost:7687", "neo4j", "neo4jpassword")
        try:
            collector = DataCollector(vk_user, db)
            collector.collect_user_data()
            logging.info("Данные успешно собраны и сохранены в Neo4j.")

            # Выполнение запросов в зависимости от типа запроса
            if query_type == "total_users":
                total_users = db.get_total_users()
                print(f"Всего пользователей: {total_users}")
            elif query_type == "total_groups":
                total_groups = db.get_total_groups()
                print(f"Всего групп: {total_groups}")
            elif query_type == "top_users":
                top_users = db.get_top_users_by_followers(5)
                print(f"Топ 5 пользователей по количеству фолловеров: {top_users}")
            elif query_type == "top_groups":
                top_groups = db.get_top_groups(5)
                print(f"Топ 5 популярных групп: {top_groups}")
            elif query_type == "mutual_followers":
                mutual_followers = db.get_mutual_followers()
                print(f"Пользователи, которые фоллоуют друг друга: {mutual_followers}")

        finally:
            db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Получение информации о пользователе ВКонтакте.")
    parser.add_argument('token_file', type=str, help="Путь к файлу с токеном")
    parser.add_argument('--user_id', type=str, default="geroykachalki", help="ID пользователя или никнейм")
    parser.add_argument('--output_file', type=str, default='user_info.json', help="Путь к файлу для сохранения информации")
    parser.add_argument('--query_type', type=str, choices=[
        'total_users', 'total_groups', 'top_users', 'top_groups', 'mutual_followers'],
        help="Тип запроса для выполнения")

    args = parser.parse_args()
    main(args.token_file, args.user_id, args.output_file, args.query_type)
