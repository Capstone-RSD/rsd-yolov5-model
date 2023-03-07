import requests
from firebase_admin import credentials, initialize_app, storage

# Init firebase with your credentials
cred = credentials.Certificate("rss-client-21d3b-firebase-private-key.json")
initialize_app(cred, {'storageBucket': 'rss-client-21d3b.appspot.com'})
def download_blob(download_url):
    """
    Downloads the blob item from firebase storage
    """
    # https://stackoverflow.com/a/54617490
    res = requests.get(download_url)
    if(res.status_code != 200):
        return False
    else:
        return res.content



def upload_map_to_firebase():
    """
    Uploads the generated HTML markup to a firebase bucket
    """

    # Put your local file path
    # TODO: #14 replace file path to generated neo4j map cluster html markup
    fileName = "neo_map.html"
    bucket = storage.bucket()
    blob = bucket.blob("map-markup/"+fileName)
    blob.upload_from_filename(fileName)

    # Opt : if you want to make public access from the URL
    blob.make_public()

    return blob.public_url
