# webshop-product-search

This repository contains the code for an internal product search for a webshop, based on Docker YAML.

## Overview

This repository includes the following components:

- **Nginx Reverse Proxy** - A web server which acts as a reverse proxy for the other components.
- **Let's Encrypt** - An open source certificate authority, providing free TLS certificates.
- **Cache Engine** - A Redis instance for caching search results.
- **Search Engine** - An Elasticsearch instance for indexing and searching products.
- **Redis Commander** - A web-based Redis GUI.
- **Kibana** - A web-based analytics and visualization platform.
- **API** - A Python web application for handling search requests.
- **Web** - An Nginx instance for serving static webpages.

## Setup

To set up the repository, you need to install Docker and Docker Compose. Once these tools are installed, you can clone this repository and run the following command to start the environment:

```
docker-compose up -d
```

## Usage

The API can be accessed at `localhost:5000` and the webpages can be accessed at `localhost:80`.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
