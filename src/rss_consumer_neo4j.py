import json
from neo4j import GraphDatabase
import folium
import logging
from folium.plugins import MarkerCluster
from rss_consumer_firebase import upload_map_to_firebase

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - (%(filename)s:%(funcName)s) %(levelname)s %(name)s:\t%(message)s",
)

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
            self.create_markers(map=map, session=session)

    # Query to retrieve nodes that have lat and long properties. Returns list of dictionaries.
    def get_nodes_with_location(self, session):
      with self.driver.session() as session:
        query = """
        MATCH (n) RETURN n.data
        """
        result = session.run(query)
        nodes = []
        for record in result:
          node = json.loads(record["n.data"])
          nodes.append(node)
        return nodes

    def create_markers(self, map, session):
      nodes = self.get_nodes_with_location(session)
      cluster = MarkerCluster(options={'showCoverageOnHover': False,
                                        'zoomToBoundsOnClick': True,
                                        'spiderfyOnMaxZoom': False,
                                        'disableClusteringAtZoom': 16}).add_to(map)
      for node in nodes:
        try:
          if node["latitude"] is not None and node["longitude"] is not None:
            lat = float(node["latitude"])
            lon = float(node["longitude"])
            popup = folium.Popup(str(node), max_width=600, max_height=600)
            marker = folium.Marker(location=[lat, lon], popup=popup)
            marker.add_to(cluster)
            logger.info("Adding location marker")
        except (ValueError, TypeError):
          logging.exception("Value/type error occured during map creation")
          break
      map.save("neo_map.html")
      upload_map_to_firebase()
      logger.info("Generating and uploading map")