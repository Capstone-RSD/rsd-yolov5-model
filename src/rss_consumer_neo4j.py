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
    
    # Method creates relationship between nodes
    # def create_relationships(self, json_data):
        # with self.driver.session() as session:
            #data = json.loads(json_data)
            # data = json_data
            # for key, value in data.items():
                # if isinstance(value, dict):
                    # for k, v in value.items():
                        # query = f"MATCH (n1:Node {{ name: '{key}' }}), (n2:Node {{name: '{k}}}) CREATE (n1)-[:RELATED_TO {{ value: '{v}' }}]->(n2)"
                        # session.run(query)
    
    uri = "neo4j+s://b9fcdf96.databases.neo4j.io:7687"
    username = "neo4j"
    password = "34MNGQ5IQM38tozXI6E7Hd7ANdIo_VjuWBwlNA1YjWs"
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
     
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
      for node in nodes:
        try:
          lat = float(node["latitude"])
          lon = float(node["longitude"])
          popup_content = f"Latitude: {lat}, Longitude: {lon}"
          popup = folium.Popup(popup_content, max_width=250)
          marker = folium.Marker(location=[lat, lon], popup=popup)
          marker.add_to(map)
        except (ValueError, TypeError):
          pass 
    
json_data = {
  "name": "Name",
  "email": "name@gmail.com",
      "latitude": 43.9569614,
      "longitude": -78.9014442,
  "speed": 0,
      "blobUrl": "https://firebasestorage.googleapis.com/v0/b/rss-client-21d3b.appspot.com/o/users%2F4G1rZANEQ8Odr13XQP3rFAwQ6zb2%2Fuploads%2F1677261733673487.jpg?alt=media&token=b8ff52b8-55d7-4f42-90c6-95e6e77fb079",
      "image": "image"
}

map = folium.Map(location=[43.9569614, -78.9014442], zoom_start=13)
marker = folium.Marker(location=[json_data["latitude"], json_data["longitude"]])
marker.add_to(map)
map.save("map.html")

#res_json = json.dumps(json_data)

json_to_neo4j = JsonToNeo4j("neo4j+s://b9fcdf96.databases.neo4j.io:7687", "neo4j", "34MNGQ5IQM38tozXI6E7Hd7ANdIo_VjuWBwlNA1YjWs")
json_to_neo4j.create_nodes(json_data)
# json_to_neo4j.create_relationships(json_data)
json_to_neo4j.close()