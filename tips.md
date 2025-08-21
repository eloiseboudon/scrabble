
postgres=# create database scrabble;
CREATE DATABASE
postgres=# CREATE USER scrabble_user WITH PASSWORD 'UnMotDePasseSecure2024!';
CREATE ROLE
postgres=# GRANT ALL PRIVILEGES ON DATABASE scrabble_db TO scrabble_user;
ERROR:  database "scrabble_db" does not exist
postgres=# GRANT ALL PRIVILEGES ON DATABASE scrabble TO scrabble_user;
GRANT




sudo ss -tlnp | grep :80




google oauth https://console.cloud.google.com/


git rm --cached tips.md

sudo nano home/ubuntu/scrabble/.env

chmod +x deploy-scrabble.sh
