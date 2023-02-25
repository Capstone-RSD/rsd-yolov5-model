import json
from neo4j import GraphDatabase

# 'json' library to parse JSON -> create nodes and relationships

# Initialize connection to Neo4j using uri, username, and password
class JsonToNeo4j:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
    def close(self):
        self.driver.close()
    
    # Method creates nodes in database
    def create_nodes(self, json_data):
        with self.driver.session() as session:
            data = json.loads(json_data)
            for key, value in data.items():
                query = f"CREATE (:Node {{ name: '{key}', value: '{value}'}})"
                session.run(query)
    
    # Method creates relationship between nodes
    def create_relationships(self, json_data):
        with self.driver.session() as session:
            data = json.loads(json_data)
            for key, value in data.items():
                if isinstance(value, dict):
                    for k, v in value.items():
                        query = f"MATCH (n1:Node {{ name: '{key}' }}), (n2:Node {{name: '{k}}}) CREATE (n1)-[:RELATED_TO {{ value: '{v}' }}]->(n2)"
                        session.run(query)

json_data = '{"name": "Name", "email": "name@gmail.com", "damageLocation": {"LatLng": {"latitude": 43.9569614, "longitude": -78.9014442}}}'

json_to_neo4j = JsonToNeo4j("bolt://localhost:7687", "neo4j", "password")
json_to_neo4j.create_nodes(json_data)
json_to_neo4j.create_relationships(json_data)
json_to_neo4j.close()