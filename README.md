A simple flask app to provide meta information like Title, OG, Meta:description of a given URL

# Usage
GET /{url}?parse={og|html|both}

Example localhost:8088/https://github.com/wannamit/siteinfo?parse=both


OG Parse code used from: https://github.com/erikriver/opengraph
