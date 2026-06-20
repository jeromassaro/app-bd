FROM postgres:16-alpine

# Varibles de entorno por default
ENV POSTGRES_DB=personasdb
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres

# Script de inicialización: se ejecuta automáticamente la primera vez que
# el contenedor arranca con el volumen de datos vacío.
COPY init.sql /docker-entrypoint-initdb.d/

EXPOSE 5432
