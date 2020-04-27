# Crawl of Duty

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The goal of this programming assignment is to build a standalone crawler that will crawl only .gov.si web sites.

## Installation instructions

Before running the project you will have to install the following dependencies.

```
pip install selenium
pip install beautifulsoup4
pip install aiohttp
pip install SQLAlchemy
pip install psycopg2
pip install w3lib
pip install tldextract
pip install w3lib
pip install urllib3
pip install requests
pip install tldextract
pip install html5lib
```

Dependencies needed for visualization to work.
```
pip install matplotlib
pip install numpy
pip install networkx
pip install scipy
```

## How to setup the database with Docker

```
$ docker pull zanozbot/crawl-of-duty-postgres
$ docker run -d -p 5432:5432 zanozbot/crawl-of-duty-postgres
>> CONTAINER_ID
$ docker logs CONTAINER_ID
$ docker stop CONTAINER_ID
```

Several programs can be used to navigate through the database. The instructions for using pgAdmin are provided below.

* Open pgAdmin website
* Right click on "Servers"
* Choose a name
* In the "Connection" tab under "Host name" copy the IP of your running Docker instance (if you are using Docker Toolbox the IP should be `192.168.99.100`)
* Under "Maintenance database" put `postgres`
* Under "Port" put `5432`
* Under "Username" and "Password" put `docker`

## Import dumped  database into container

```
docker exec -i CONTAINER_NAME mkdir /database_dump
docker cp seedListCrawled.sql CONTAINER_NAME:/database_dump/seedListCrawled.sql
docker exec -i CONTAINER_NAME pg_restore -U docker -d postgres /database_dump/seedListCrawled.sql
docker exec -i CONTAINER_NAME psql -U docker -d postgres -f database_dump/seedListCrawled.sql
```
