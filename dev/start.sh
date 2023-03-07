docker run -it --log-opt max-size=10m --log-opt max-file=5 \
 --name dev \
 --network host \
 -v $(pwd):/home/hummingbot/app \
 dev:latest