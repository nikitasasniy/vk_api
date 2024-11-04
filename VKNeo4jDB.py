from neo4j import GraphDatabase


class VKNeo4jDB:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_user_node(self, user_data):
        # Проверка на наличие обязательных параметров
        required_fields = ['id', 'screen_name', 'name', 'sex', 'home_town']
        for field in required_fields:
            if field not in user_data:
                raise ValueError(f"Missing required field: {field}")

        query = """
        MERGE (u:User {id: $id})
        SET u.screen_name = $screen_name, 
            u.name = $name, 
            u.sex = $sex, 
            u.home_town = $home_town
        RETURN u
        """
        self._execute_query(query, user_data)

    def create_group_node(self, group_data):
        query = """
        MERGE (g:Group {id: $id})
        SET g.name = $name, 
            g.screen_name = $screen_name
        RETURN g
        """
        self._execute_query(query, group_data)

    def create_follow_relationship(self, user_id, follower_id):
        query = """
        MATCH (u:User {id: $user_id}), (f:User {id: $follower_id})
        MERGE (f)-[:FOLLOWS]->(u)
        """
        self._execute_query(query, {"user_id": user_id, "follower_id": follower_id})

    def create_subscribe_relationship(self, user_id, group_id):
        query = """
        MATCH (u:User {id: $user_id}), (g:Group {id: $group_id})
        MERGE (u)-[:SUBSCRIBES]->(g)
        """
        self._execute_query(query, {"user_id": user_id, "group_id": group_id})

    def get_total_users(self):
        query = "MATCH (u) RETURN COUNT(u) AS count"
        with self.driver.session() as session:
            result = session.run(query)
            return result.single()['count']

    def get_total_groups(self):
        query = "MATCH (g:Group) RETURN COUNT(g) AS count"
        with self.driver.session() as session:
            result = session.run(query)
            return result.single()['count']

    def get_top_users(self, limit=5):
        query = """
        MATCH (u:User)<-[:FOLLOWS]-(f:User)
        RETURN u.id AS user_id, u.name AS user_name, COUNT(f) AS followers_count
        ORDER BY followers_count DESC
        LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(query, {"limit": limit})
            return [{"user_id": record["user_id"], "user_name": record["user_name"],
                     "followers_count": record["followers_count"]} for record in result]

    def get_top_groups(self, limit=5):
        query = """
        MATCH (u:User)-[:SUBSCRIBES]->(g:Group)
        RETURN g.id AS group_id, g.name AS group_name, COUNT(u) AS subscribers_count
        ORDER BY subscribers_count DESC
        LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(query, {"limit": limit})
            return [{"group_id": record["group_id"], "group_name": record["group_name"],
                     "subscribers_count": record["subscribers_count"]} for record in result]

    def get_mutual_followers(self, user_id1, user_id2):
        query = """
        MATCH (u1:User {id: $user_id1})<-[:FOLLOWS]-(f:User)-[:FOLLOWS]->(u2:User {id: $user_id2})
        RETURN f.id AS follower_id, f.name AS follower_name
        """
        with self.driver.session() as session:
            result = session.run(query, {"user_id1": user_id1, "user_id2": user_id2})
            return [{"follower_id": record["follower_id"], "follower_name": record["follower_name"]} for record in
                    result]

    def _execute_query(self, query, parameters=None):
        with self.driver.session() as session:
            try:
                session.run(query, parameters or {})
            except Exception as e:
                print(f"Error executing query: {query} with params: {parameters}. Exception: {str(e)}")
                raise
