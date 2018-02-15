#!/bin/bash

cd services
for d in `ls -d */`; do 
  echo $d; 
  cd $d; 
  docker build -f Dockerfile -t myapp_${d::-1} .;
  cd ..;
done

docker swarm init
