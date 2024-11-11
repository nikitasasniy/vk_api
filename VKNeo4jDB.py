from neo4j import GraphDatabase
import logging


class VKNeo4jDB:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """Закрытие соединения с базой данных Neo4j."""
        self.driver.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create_user_node(self, user_data):
        query = """
        CREATE (u:User {
            id: $id,
            name: $name,
            screen_name: $screen_name,
            sex: $sex,
            home_town: $home_town,
            followers_count: $followers_count,
            subscriptions_count: $subscriptions_count
        })
        """
        parameters = {
            "id": user_data["id"],
            "name": user_data["name"],
            "screen_name": user_data["screen_name"],
            "sex": user_data["sex"],
            "home_town": user_data["home_town"],
            "followers_count": user_data["followers_count"],
            "subscriptions_count": user_data["subscriptions_count"]
        }
        self._execute_query(query, parameters)

    def create_group_node(self, group_data: dict):
        """Создаёт узел группы в базе данных."""
        query = """
        MERGE (g:Group {id: $id})
        SET g.name = $name, 
            g.screen_name = $screen_name
        RETURN g
        """
        self._execute_query(query, group_data)

    def create_follow_relationship(self, user_id: int, follower_id: int):
        """Создаёт отношение FOLLOWS между пользователями."""
        query = """
        MATCH (u:User {id: $user_id}), (f:User {id: $follower_id})
        MERGE (f)-[:FOLLOWS]->(u)
        """
        self._execute_query(query, {"user_id": user_id, "follower_id": follower_id})

    def create_subscribe_relationship(self, user_id: int, group_id: int):
        """Создаёт отношение SUBSCRIBES между пользователем и группой."""
        query = """
        MATCH (u:User {id: $user_id}), (g:Group {id: $group_id})
        MERGE (u)-[:SUBSCRIBES]->(g)
        """
        self._execute_query(query, {"user_id": user_id, "group_id": group_id})

    def get_total_users(self):
        query = "MATCH (u) RETURN COUNT(u) AS count"
        with self.driver.session() as session:
            result = session.run(query)
            # Получаем результат сразу и возвращаем его
            record = result.single()
            if record:
                return record['count']
            return 0  # На случай, если результат пустой

    def get_total_groups(self):
        query = "MATCH (g:Group) RETURN COUNT(g) AS count"
        with self.driver.session() as session:
            result = session.run(query)
            record = result.single()
            if record:
                return record['count']
            return 0

    def get_top_users(self, limit=5):
        query = """
        MATCH (u:User)<-[:FOLLOWS]-(f:User)
        RETURN u.id AS user_id, u.name AS user_name, COUNT(f) AS followers_count
        ORDER BY followers_count DESC
        LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(query, {"limit": limit})
            # Преобразуем результаты сразу в список
            return [
                {"user_id": record["user_id"], "user_name": record["user_name"],
                 "followers_count": record["followers_count"]}
                for record in result
            ]

    def get_top_groups(self, limit=5):
        query = """
        MATCH (u:User)-[:SUBSCRIBES]->(g:Group)
        RETURN g.id AS group_id, g.name AS group_name, COUNT(u) AS subscribers_count
        ORDER BY subscribers_count DESC
        LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(query, {"limit": limit})
            return [
                {"group_id": record["group_id"], "group_name": record["group_name"],
                 "subscribers_count": record["subscribers_count"]}
                for record in result
            ]

    def get_mutual_followers(self, user_id1: int, user_id2: int) -> list:
        """Возвращает список взаимных подписчиков между двумя пользователями."""
        query = """
        MATCH (u1:User {id: $user_id1})<-[:FOLLOWS]-(f:User)-[:FOLLOWS]->(u2:User {id: $user_id2})
        RETURN f.id AS follower_id, f.name AS follower_name
        """
        result = self._execute_query(query, {"user_id1": user_id1, "user_id2": user_id2})
        return [{"follower_id": record["follower_id"], "follower_name": record["follower_name"]} for record in result]

    def _execute_query(self, query: str, parameters: dict = None):
        """Выполняет запрос к базе данных и возвращает результат."""
        with self.driver.session() as session:
            try:
                return session.run(query, parameters or {})
            except Exception as e:
                logging.error(f"Ошибка выполнения запроса: {query} с параметрами: {parameters}. Исключение: {e}")
                raise
