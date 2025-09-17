# lasur-ws

EPFL LASUR web services:

* Typologie Modale


## Redis

The backend uses Redis to cache the results of the S3 bucket queries. The Redis server is started in a Docker container.

Run Redis
```
make redis-up
```

Stop Redis
```
make redis-stop
```