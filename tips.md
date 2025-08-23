# Lancer déploiement
./lanceur.sh


# Qui a til sur le port 80
sudo ss -tlnp | grep :80



# Google Ouath
google oauth https://console.cloud.google.com/


# Pour supprimer le fichier du repository mais le garder localement :
git rm --cached nom_du_fichier.txt
git rm --cached tips.md


# Connexion serveur 
sshpass -p '3k56b5iEhI0k' ssh ubuntu@51.77.231.101



# Suivre les logs backend
tail -f /home/ubuntu/scrabble/logs/backend.log /home/ubuntu/scrabble/logs/backend-error.log

# Accès a la base 
PGPASSWORD='test123' psql -h localhost -p 5433 -U scrabble_user -d scrabble_db -c "\d users"
PGPASSWORD='test123' psql -h localhost -p 5432 -U scrabble_user -d scrabble_db -c 'select current_user, current_database();'


postgres=# create database scrabble;
CREATE DATABASE
postgres=# CREATE USER scrabble_user WITH PASSWORD 'r-7SX5nWpedJB#%F';
CREATE ROLE
postgres=# GRANT ALL PRIVILEGES ON DATABASE scrabble_db TO scrabble_user;
ERROR:  database "scrabble_db" does not exist
postgres=# GRANT ALL PRIVILEGES ON DATABASE scrabble TO scrabble_user;
GRANT
