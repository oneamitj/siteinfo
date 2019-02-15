A simple flask app to provide meta information like Title, OG, Meta:description of a given URL

# Usage
GET /{url}?parse={og|html|both}

Example http://localhost:8088/https://github.com/wannamit/siteinfo?parse=both

# Docker Run
docker run -p 8088:8088 wannamit/siteinfo:latest


OG Parse code used from: https://github.com/erikriver/opengraph
