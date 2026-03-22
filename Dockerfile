FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
COPY data/ships.json /usr/share/nginx/html/data/
