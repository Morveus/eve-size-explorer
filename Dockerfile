FROM nginxinc/nginx-unprivileged:alpine
COPY index.html /usr/share/nginx/html/
COPY data/ships.json /usr/share/nginx/html/data/
EXPOSE 8080
