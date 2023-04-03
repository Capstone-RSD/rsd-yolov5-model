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

            iframe_damagePayload = ""
            for item in node["damagePayload"]:
              iframe_damagePayload += "<h5 style=\"font-size: 20px;\"><h5 style=\"font-weight: bold;\">Class:</h5>"+str(item["damage_class"])+",</h5>"
              iframe_damagePayload += "<h5 style=\"font-size: 20px;\"><h5 style=\"font-weight: bold;\">Width:</h5>"+str(item["damage_width"])+",</h5>"
              iframe_damagePayload += "<h5 style=\"font-size: 20px;\"><h5 style=\"font-weight: bold;\">Length:</h5>"+str(item["damage_length"])+",</h5><br><hr>"

            iframe = folium.Html(
                f"""
                <html>
                  <div class="accordion" id="accordionExample" style="width: 400px">
                  
                    <div class="accordion-item">
                      <h2 class="accordion-header" id="headingOne">
                        <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseOne" aria-expanded="false" aria-controls="collapseOne">
                          Coordinates
                        </button>
                      </h2>
                      
                      <div id="collapseOne" class="accordion-collapse collapse" aria-labelledby="headingOne">
                        <div class="accordion-body">
                          <h5 style="font-size: 20px;"><h5 style="font-weight: bold;">Latitude:</h5> {node["latitude"]}</h5><br>
                          <h5 style="font-size: 20px;"><h5 style="font-weight: bold;">Longitude:</h5> {node["longitude"]}</h5>
                        </div>
                      </div>  
                    </div>
                    
                    <div class="accordion-item">
                      <h2 class="accordion-header" id="headingTwo">
                        <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseTwo" aria-expanded="false" aria-controls="collapseTwo">
                          Deterioration Image
                        </button>
                      </h2>
                      
                      <div id="collapseTwo" class="accordion-collapse collapse" aria-labelledby="headingTwo">
                        <div class="accordion-body">
                          <a href="{node["blob_url"]}"><img src="{node["blob_url"]}" alt="Image" width="350" height="300"></a>
                        </div>
                      </div>
                    </div>

                    <div class="accordion-item">
                      <h2 class="accordion-header" id="headingThree">
                        <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseThree" aria-expanded="false" aria-controls="collapseThree">
                          Damage
                        </button>
                      </h2>
                      
                      <div id="collapseThree" class="accordion-collapse collapse" aria-labelledby="headingThree">
                        <div class="accordion-body">
                          {iframe_damagePayload}
                        </div>
                      </div>
                    </div>

                    <div class="accordion-item">
                      <h2 class="accordion-header" id="headingFour">
                        <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseFour" aria-expanded="false" aria-controls="collapseFour">
                          BoundedBox Image
                        </button>
                      </h2>
                      
                      <div id="collapseFour" class="accordion-collapse collapse" aria-labelledby="headingFour">
                        <div class="accordion-body">
                          <a href="{node["boundedbox_image_url"]}"><img src="{node["boundedbox_image_url"]}" alt="Image" width="350" height="300"></a>
                        </div>
                      </div>
                    </div>

                  </div>
                </html>
                """, 
              script=True)

            popup = folium.Popup(iframe, str(node), max_width=500)
            marker = folium.Marker(location=[lat, lon], popup=popup)
            marker.add_to(cluster)
            logger.info("Adding location marker")
        except (ValueError, TypeError):
          logging.exception("Value/type error occured during map creation")
          break
        
      map.save("neo_map.html")
      upload_map_to_firebase()
      logger.info("Generating and uploading map")