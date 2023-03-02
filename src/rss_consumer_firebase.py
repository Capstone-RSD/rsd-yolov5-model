import requests

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
#download_blob("https://firebasestorage.googleapis.com/v0/b/rss-client-21d3b.appspot.com/o/users%2FLVCRRtv1pgeCDusQC6lC9SrSSlp2%2Fuploads%2F1677022217697261.jpg?alt=media&token=9eb91437-0cca-4108-a486-71283f85bb31")
