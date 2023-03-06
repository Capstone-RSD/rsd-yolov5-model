import json
from neo4j import GraphDatabase
import folium

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
            query = "CREATE (r:Report { data: $data })"
            session.run(query, data=json.dumps(json_data))
        map = folium.Map(location=[43.945082, -78.896740], zoom_start=13)
        self.create_markers(map=map)

    # Query to retrieve nodes that have lat and long properties. Returns list of dictionaries.
    def get_nodes_with_location(self):
      with self.driver.session() as session:
        query = """
          MATCH (n:Node)
          WHERE EXISTS(n.latitude) AND EXISTS(n.longitude)
          RETURN n
        """
      result = session.run(query)
      nodes = []
      for record in result:
        node = record["n"]
        nodes.append(node)
      return nodes

    def create_markers(self, map):
      nodes = self.get_nodes_with_location()
      print("Nodes: ",nodes)
      for node in nodes:
        try:
          lat = float(node["latitude"])
          lon = float(node["longitude"])
          marker = folium.Marker(location=[lat, lon])
          print("Longitude: %s",lon)
          marker.add_to(map)
        except (ValueError, TypeError):
          print("Value/type error occured during map creation")
          break
      map.save("neo_map.html")