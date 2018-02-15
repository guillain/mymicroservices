# *myMicroServices* provided by Docker swarm

## Presentation

### Why

Moving on DevOps technologies we need to have usable and fast tools for deployment.
In that case we've creating and will continue to improve the app management via container and micro-service features.

### What

As example, the idea is to provide the full set of tools that require an web application.
Coming from the DB until the DB management himself, each image provide the necessary piece of the DevOps puzzle in containers and micro-services world.

### How

Used from MyHero example provided by Hank Preston, the API design has been adapted and merged to reply to the template and automatisation that we can expect for an API µservice design on docker environment.

## Images (docker)

MyHero as µservice design based on API
* https://github.com/hpreston/myhero_demo
* https://hub.docker.com/u/hpreston/?page=2

Mosca as MQTT server
* https://hub.docker.com/r/matteocollina/mosca/

MySQL
* https://hub.docker.com/mysql

PhpMyAdmin
* https://hub.docker.com/r/phpmyadmin/phpmyadmin/

Docker and by preference in Swarm mode... to move maybe after on Kubernetes ;-)
* https://platform9.com/blog/kubernetes-docker-swarm-compared

### List of docker images build

* myapp_data
* myapp_api
* myapp_mqttpub
* myapp_mqttsub
* myapp_web
* myapp_ui
* myapp_spark
* myapp_tropo

### List of docker images used as-it-is

* mysql
* phpmyadmin

## Port

### Public

* 20201: myapp_api
* 20301: myapp_web
* 20401: myapp_ui
* 20501: myapp_spark
* 20601: myapp_tropo
* 28080: phpmyadmin

### Private

* 20101: myapp_data
* 20701: myapp_mqttpub
* 20801: myapp_mqttsub
* 80  : phpmyadmin
* 3306: mysql

## Usage

### Docker stack (Swarm mode)

#### Prerequisite

* docker
* docker-compose
* docker swarm
* download the docker-stack.yml file
  * ie: `git clone https://scm.dimensiondata.com/guillain.sanchez/myapp-docker`

#### Setup

* `cp docker-stack.yml.sample docker-stack.yml`
* `vi docker-stack.yml` modify it according to your settings


* docker swarm init (only on the swarm host)
* build app images

Or execute the setup sript

* `./setup.sh`

#### Start

* `./start.sh`

or

* `docker stack deploy -c docker-stack.yml myapp`

#### Restart

* `./restart.sh`

#### Stop

* `./stop.sh`

or

* `docker stack rm myapp`

#### Status

* `docker stack ls`
* `docker service ls`
* `docker network inspect myapp_default`

## Docker hand up

### List of the docker's container

* `docker ps`

Have an eye on the CONTAINER ID, will be useful to execute command arround container....


### Exec command in the container

To display the NIC configuration

* `docker exec -it [CONTAINER ID] ifconfig`

### Enter in the container (like exec a command)

To depend of the container...

* `docker exec -it [CONTAINER ID] sh`
* `docker exec -it [CONTAINER ID] bash`

### Service list

```
# docker service ls
ID            NAME              MODE        REPLICAS  IMAGE
2xm89dnxkajm  myapp_tropo       replicated  1/1       myapp_tropo
9ch6jvgjxvk9  myapp_web         replicated  1/1       myapp_web
c6p0k3nhr7ea  myapp_spark       replicated  1/1       myapp_spark
f82nll988kko  myapp_mqttsub     replicated  1/1       myapp_mqttsub
j1aum829s7dk  myapp_api         replicated  1/1       myapp_api
o42jbv3o6qzn  myapp_phpmyadmin  replicated  1/1       phpmyadmin/phpmyadmin:latest
on6ay74jhgoe  myapp_ui          replicated  1/1       myapp_ui
quvlcyi02ukj  myapp_data        replicated  1/1       myapp_data
t6gyef80j07t  myapp_mysql       replicated  1/1       mysql:latest
vgw95obs6okh  myapp_mqttpub     replicated  1/1       myapp_mqttpub
```

#### Scale the services

```
# docker service scale myapp_web=2 myapp_ui=3
myapp_web scaled to 2
myapp_ui scaled to 3

# docker service ls
ID            NAME              MODE        REPLICAS  IMAGE
2xm89dnxkajm  myapp_tropo       replicated  1/1       myapp_tropo
9ch6jvgjxvk9  myapp_web         replicated  2/2       myapp_web
c6p0k3nhr7ea  myapp_spark       replicated  1/1       myapp_spark
f82nll988kko  myapp_mqttsub     replicated  1/1       myapp_mqttsub
j1aum829s7dk  myapp_api         replicated  1/1       myapp_api
o42jbv3o6qzn  myapp_phpmyadmin  replicated  1/1       phpmyadmin/phpmyadmin:latest
on6ay74jhgoe  myapp_ui          replicated  3/3       myapp_ui
quvlcyi02ukj  myapp_data        replicated  1/1       myapp_data
t6gyef80j07t  myapp_mysql       replicated  1/1       mysql:latest
vgw95obs6okh  myapp_mqttpub     replicated  1/1       myapp_mqttpub
```

