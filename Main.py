import logging
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Начинается процесс сбора данных")
    uri = "bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=("neo4j", "test"))

    try:
        with driver.session() as session:
            # Ваш код работы с Neo4j
            result = session.run("MATCH (n) RETURN n LIMIT 5")
            for record in result:
                print(record)
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
    finally:
        driver.close()
        logger.info("Программа завершена")

if __name__ == "__main__":
    main()
