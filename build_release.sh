#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <version>"
  exit 1
fi

version=$1

docker build -t littleorange666/apcs_tool:$version .
docker push littleorange666/apcs_tool:$version