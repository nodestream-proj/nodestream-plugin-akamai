# Overview
This repo contains the scripts necessary to ingest Akamai property and redirect configs
and ingest them into Neo4j.  It is a starting point to help visualize your external attack surface
within Akamai.

# Setup Neo4j
1. Download and install Neo4j: https://neo4j.com/docs/desktop-manual/current/installation/download-installation/
1. Create a database: https://neo4j.com/docs/desktop-manual/current/operations/create-dbms/

# Download Akamai credentials
1. Create and download akamai credentials: https://techdocs.akamai.com/developer/docs/set-up-authentication-credentials

NOTE: These values will be used in your `.env` 

# Install and run the app
1. Install python3: https://www.python.org/downloads/ 
1. Install poetry: https://python-poetry.org/docs/#installation 
1. Setup `.env` file: (copy .env.example and update values)
1. Install necessary dependencies: `poetry install`
1. Source necessary Environment Variables: `source ./.env`
1. Run the app: `poetry run python main.py`

# Authors
* Zach Probst
* Chad Cloes
* Bryan Norman
* Gabe Gallagher
