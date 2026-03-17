from abstract_webtools import *
import httpx

resp = httpx.get("https://www.usatoday.com/gcdn/authoring/authoring-images/2026/03/17/USAT/89192508007-20210918-t-171500-z-2069261537-rc-2-gsp-94-kqu-7-rtrmadp-3-usacapitolsecurity.JPG?width=660&height=440&fit=crop&format=pjpg&auto=webp", headers={"Range": "bytes=0-261"})
content_type = resp.headers.get("content-type")  # e.g. "image/png"

 # e.g. "image/png"
input(content_type)

url = 'thedailydialectics.com'
url_mgr = urlManager(url, valid_variants=True)
url_mgr.update_url(url)
input(title_variants_from_domain(url))
