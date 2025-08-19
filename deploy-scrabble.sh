#!/bin/bash

# Script de déploiement automatisé Scrabble
# Usage: ./deploy-scrabble.sh [branch_name]

set -e  # Arrêt du script en cas d'erreur

# Configuration - À ADAPTER
REPO_URL="https://github.com/eloiseboudon/scrabble.git"
APP_DIR="/home/ubuntu/scrabble"
BRANCH="${1:-main}"
BACKUP_DIR="/home/ubuntu/backups_scrabble/deployments/$(date +%Y%m%d_%H%M%S)"
BACKEND_PORT="8001"
NGINX_PORT="8080"

# Base de données
DB_NAME="scrabble_db"
DB_USER="scrabble_user"
DB_PASSWORD="UnMotDePasseSecure2024!"  # À changer !

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Vérification des prérequis
check_prerequisites() {
    log "🔍 Vérification des prérequis..."
    
    if ! command -v git &> /dev/null; then
        error "Git n'est pas installé"
    fi
    
    if ! command -v python3 &> /dev/null; then
        error "Python3 n'est pas installé"
    fi
    
    if ! command -v npm &> /dev/null; then
        error "NPM n'est pas installé"
    fi
    
    if ! command -v nginx &> /dev/null; then
        error "Nginx n'est pas installé"
    fi
    
    if ! systemctl is-active --quiet postgresql; then
        error "PostgreSQL n'est pas en cours d'exécution"
    fi
    
    info "✅ Tous les prérequis sont satisfaits"
}

# Sauvegarde de la base de données
backup_database() {
    log "💾 Sauvegarde de la base de données..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Sauvegarde PostgreSQL
    local backup_file="$BACKUP_DIR/scrabble_db_backup.sql"
    if sudo -u postgres pg_dump "$DB_NAME" > "$backup_file" 2>/dev/null; then
        info "✅ Base de données sauvegardée : $backup_file"
    else
        warn "⚠️ Échec de la sauvegarde DB (peut-être que la DB n'existe pas encore)"
    fi
}

# Sauvegarde de l'application actuelle
backup_current_version() {
    log "📦 Sauvegarde de la version actuelle..."
    
    if [ -d "$APP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        tar --exclude='*/node_modules' \
            --exclude='*/dist' \
            --exclude='*/build' \
            --exclude='*/.git' \
            --exclude='*/venv' \
            --exclude='*/__pycache__' \
            -czf "$BACKUP_DIR/app_backup.tar.gz" \
            -C "$(dirname "$APP_DIR")" "$(basename "$APP_DIR")"
        
        info "Sauvegarde créée : $BACKUP_DIR/app_backup.tar.gz"
    fi
}

# Récupération du code depuis Git
fetch_code() {
    log "📥 Récupération du code depuis Git (branche: $BRANCH)..."
    
    if [ ! -d "$APP_DIR" ]; then
        log "🆕 Premier déploiement - clonage du repository..."
        git clone "$REPO_URL" "$APP_DIR"
        cd "$APP_DIR"
        git checkout "$BRANCH"
    else
        cd "$APP_DIR"
        
        # Vérification du statut Git
        if ! git status &>/dev/null; then
            error "Le répertoire n'est pas un repository Git valide"
        fi
        
        # Sauvegarde des changements locaux potentiels
        if ! git diff --quiet; then
            warn "Des changements locaux détectés, création d'un stash..."
            git stash push -m "Auto-stash before deploy $(date)"
        fi
        
        # Mise à jour du code
        git fetch origin
        git checkout "$BRANCH"
        git pull origin "$BRANCH"
    fi
    
    local commit_hash=$(git rev-parse --short HEAD)
    local commit_msg=$(git log -1 --pretty=%B | head -1)
    
    info "✅ Code mis à jour - Commit: $commit_hash"
    info "📝 Message: $commit_msg"
}

# Configuration du backend Python
setup_backend() {
    log "🐍 Configuration du backend Python..."
    
    cd "$APP_DIR"
    
    # Déterminer le répertoire backend
    local backend_dir="$APP_DIR"
    if [ -d "$APP_DIR/backend" ]; then
        backend_dir="$APP_DIR/backend"
        cd "$backend_dir"
    fi
    
    # Création de l'environnement virtuel
    if [ ! -d "venv" ]; then
        log "🆕 Création de l'environnement virtuel Python..."
        python3 -m venv venv
    fi
    
    # Activation de l'environnement virtuel
    source venv/bin/activate
    
    # Mise à jour pip
    pip install --upgrade pip
    
    # Installation des dépendances
    if [ -f "requirements.txt" ]; then
        log "📦 Installation des dépendances Python..."
        pip install -r requirements.txt
    else
        warn "⚠️ Fichier requirements.txt introuvable"
    fi
    
    # Configuration des variables d'environnement
    log "⚙️ Configuration des variables d'environnement..."
    cat > .env << EOF
# Base de données
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
DB_HOST=localhost
DB_PORT=5432
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD

# Application
FASTAPI_ENV=production
DEBUG=False
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

# Serveur
HOST=0.0.0.0
PORT=$BACKEND_PORT
EOF
    
    info "✅ Backend Python configuré"
}

# Préparation du frontend
setup_frontend() {
    log "🗃️ Préparation du frontend..."
    
    # Le package.json est à la racine
    if [ -f "$APP_DIR/package.json" ]; then
        cd "$APP_DIR"
        
        # Installation des dépendances NPM si nécessaire
        log "📦 Installation des dépendances NPM..."
        if ! npm ci --production=false 2>/dev/null; then
            warn "⚠️ npm ci a échoué, tentative avec npm install..."
            npm install --legacy-peer-deps 2>/dev/null || npm install
        fi
        
        # Vérifier s'il y a un script de build
        if npm run | grep -q "build"; then
            log "🔨 Build de production..."
            npm run build
            
            # Copier les fichiers buildés si un dossier dist existe
            if [ -d "dist" ]; then
                mkdir -p "$APP_DIR/frontend/dist"
                cp -r dist/* "$APP_DIR/frontend/dist/"
            fi
        else
            info "ℹ️ Pas de script de build détecté"
        fi
    fi
    
    # Le frontend semble être du HTML/JS statique
    # Créer le répertoire dist et copier les fichiers frontend
    mkdir -p "$APP_DIR/frontend/dist"
    
    if [ -d "$APP_DIR/frontend" ]; then
        # Copier tous les fichiers du frontend vers le répertoire dist
        cp -r "$APP_DIR/frontend"/* "$APP_DIR/frontend/dist/" 2>/dev/null || true
        
        # S'assurer qu'il y a un index.html
        if [ ! -f "$APP_DIR/frontend/dist/index.html" ] && [ -f "$APP_DIR/frontend/index.html" ]; then
            cp "$APP_DIR/frontend/index.html" "$APP_DIR/frontend/dist/"
        fi
    fi
    
    local build_size=$(du -sh "$APP_DIR/frontend/dist" 2>/dev/null | cut -f1 || echo "N/A")
    info "✅ Frontend préparé avec succès - Taille: $build_size"
}

# Configuration de la base de données
setup_database() {
    log "🗄️ Configuration de la base de données..."
    
    # Vérifier si la base existe
    if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        info "✅ Base de données $DB_NAME existe déjà"
    else
        log "🆕 Création de la base de données $DB_NAME..."
        sudo -u postgres createdb "$DB_NAME"
        sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
        sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
        info "✅ Base de données créée"
    fi
}

# Gestion des migrations (si Alembic est utilisé)
run_database_migrations() {
    log "🗃️ Vérification des migrations de base de données..."
    
    cd "$APP_DIR"
    local backend_dir="$APP_DIR"
    if [ -d "$APP_DIR/backend" ]; then
        backend_dir="$APP_DIR/backend"
    fi
    
    cd "$backend_dir"
    source venv/bin/activate
    
    # Vérifier si Alembic est configuré
    if [ -f "alembic.ini" ] && [ -d "alembic" ]; then
        log "🔍 Alembic détecté, gestion des migrations..."
        
        # Vérifier l'état actuel
        local current_migration=""
        if alembic current >/dev/null 2>&1; then
            current_migration=$(alembic current 2>/dev/null | grep -E "^[a-f0-9]+" || echo "Aucune")
            info "Migration actuelle: $current_migration"
        else
            warn "Alembic pas encore initialisé"
        fi
        
        # Générer une migration automatique si nécessaire
        local migration_name="auto_migrate_$(date +%Y%m%d_%H%M%S)"
        if alembic revision --autogenerate -m "$migration_name" 2>/dev/null; then
            info "🆕 Migration générée: $migration_name"
        else
            info "ℹ️ Aucun changement de schéma détecté"
        fi
        
        # Appliquer les migrations
        log "⬆️ Application des migrations..."
        alembic upgrade head
        
        info "✅ Migrations appliquées avec succès"
    else
        info "ℹ️ Alembic non configuré, pas de migrations à appliquer"
    fi
}

# Démarrage du backend comme service
setup_backend_service() {
    log "🚀 Configuration du service backend..."
    
    # Arrêter le service s'il tourne déjà
    if systemctl is-active --quiet scrabble-backend; then
        log "🛑 Arrêt du service backend existant..."
        sudo systemctl stop scrabble-backend
    fi
    
    # Déterminer le fichier principal et le répertoire
    local backend_dir="$APP_DIR"
    local main_file="app.py"
    
    if [ -d "$APP_DIR/backend" ]; then
        backend_dir="$APP_DIR/backend"
    fi
    
    # Chercher le fichier principal
    cd "$backend_dir"
    for file in main.py app.py server.py run.py; do
        if [ -f "$file" ]; then
            main_file="$file"
            break
        fi
    done
    
    if [ ! -f "$main_file" ]; then
        error "Fichier principal Python introuvable (main.py, app.py, server.py, run.py)"
    fi
    
    info "Fichier principal détecté: $main_file"
    
    # Pour FastAPI, utiliser uvicorn comme serveur ASGI
    local exec_command=""
    if [ "$main_file" = "main.py" ]; then
        # Vérifier si c'est du FastAPI
        if grep -q "FastAPI\|fastapi" "$main_file"; then
            exec_command="$backend_dir/venv/bin/uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT --workers 1"
        else
            exec_command="$backend_dir/venv/bin/python $main_file"
        fi
    else
        exec_command="$backend_dir/venv/bin/python $main_file"
    fi
    
    # Mise à jour du service systemd
    sudo tee /etc/systemd/system/scrabble-backend.service > /dev/null << EOF
[Unit]
Description=Scrabble Backend Application
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$backend_dir
Environment=PATH=$backend_dir/venv/bin
Environment=PYTHONPATH=$backend_dir
ExecStart=$exec_command
Restart=always
RestartSec=3

# Variables d'environnement
EnvironmentFile=$backend_dir/.env

# Logs
StandardOutput=append:/home/ubuntu/scrabble/logs/backend.log
StandardError=append:/home/ubuntu/scrabble/logs/backend-error.log

[Install]
WantedBy=multi-user.target
EOF

    # Créer le répertoire des logs
    mkdir -p /home/ubuntu/scrabble/logs
    
    # Recharger systemd et démarrer le service
    sudo systemctl daemon-reload
    sudo systemctl enable scrabble-backend
    sudo systemctl start scrabble-backend
    
    # Vérifier que le service démarre
    sleep 5
    if systemctl is-active --quiet scrabble-backend; then
        info "✅ Service backend démarré avec succès"
    else
        error "❌ Échec du démarrage du service backend"
    fi
}

# Rechargement de Nginx
reload_nginx() {
    log "🔄 Rechargement de Nginx..."
    
    # Test de la configuration
    if sudo nginx -t; then
        sudo systemctl reload nginx
        info "✅ Nginx rechargé avec succès"
    else
        error "❌ Erreur dans la configuration Nginx"
    fi
}

# Vérification de la santé de l'application
health_check() {
    log "🏥 Vérification de la santé de l'application..."
    
    # Test du backend
    log "🔧 Test du backend..."
    local backend_url="http://localhost:$BACKEND_PORT"
    for i in {1..10}; do
        if curl -f -s "$backend_url" > /dev/null 2>&1; then
            info "✅ Backend accessible !"
            break
        fi
        if [ $i -eq 10 ]; then
            warn "⚠️ Backend inaccessible après 10 tentatives"
            sudo systemctl status scrabble-backend
            break
        fi
        warn "Tentative $i/10 - Backend en cours de démarrage..."
        sleep 5
    done
    
    # Test du frontend via Nginx
    log "🌐 Test du frontend..."
    local frontend_url="http://localhost:$NGINX_PORT"
    for i in {1..5}; do
        if curl -f -s "$frontend_url" > /dev/null 2>&1; then
            info "✅ Frontend accessible !"
            break
        fi
        if [ $i -eq 5 ]; then
            warn "⚠️ Frontend inaccessible"
            break
        fi
        warn "Tentative $i/5 - Frontend en cours de vérification..."
        sleep 3
    done
    
    # Test externe
    log "🌍 Test d'accès externe..."
    if curl -f -s "http://scrabble.tulip-saas.fr:$NGINX_PORT" > /dev/null 2>&1; then
        info "✅ Application accessible depuis l'extérieur !"
    else
        warn "⚠️ Application non accessible depuis l'extérieur (vérifiez le DNS/firewall)"
    fi
}

# Rollback en cas d'échec
rollback() {
    error "💥 Échec du déploiement, rollback en cours..."
    
    if [ -f "$BACKUP_DIR/app_backup.tar.gz" ]; then
        log "🔄 Restauration de la version précédente..."
        
        # Arrêter le service
        sudo systemctl stop scrabble-backend || true
        
        # Restaurer les fichiers
        cd "$(dirname "$APP_DIR")"
        rm -rf "$APP_DIR"
        tar -xzf "$BACKUP_DIR/app_backup.tar.gz"
        
        # Redémarrer le service
        sudo systemctl start scrabble-backend || true
        sudo systemctl reload nginx || true
        
        warn "⚠️ Rollback terminé - Vérifiez l'état de l'application"
    else
        error "❌ Impossible de faire le rollback - Pas de sauvegarde disponible"
    fi
}

# Nettoyage des anciennes sauvegardes
cleanup_old_backups() {
    log "🧹 Nettoyage des anciennes sauvegardes..."
    
    local backup_base_dir="/home/ubuntu/backups_scrabble/deployments"
    if [ -d "$backup_base_dir" ]; then
        find "$backup_base_dir" -maxdepth 1 -type d -name "20*" | sort -r | tail -n +6 | xargs rm -rf 2>/dev/null || true
        info "✅ Nettoyage terminé (conservation des 5 dernières)"
    fi
}

# Affichage des informations post-déploiement
show_deployment_info() {
    log "📋 Informations de déploiement:"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "🌐 Frontend: http://scrabble.tulip-saas.fr:$NGINX_PORT"
    echo "🔧 Backend:  http://localhost:$BACKEND_PORT"
    echo "🗄️ Database: PostgreSQL sur le port 5432"
    echo "📊 Service:  sudo systemctl status scrabble-backend"
    echo "📝 Logs:     tail -f /home/ubuntu/scrabble/logs/backend.log"
    echo "🔧 Nginx:    sudo nginx -t && sudo systemctl reload nginx"
    echo "╚═══════════════════════════════════════════════════════════╝"
    
    # Informations Git
    cd "$APP_DIR"
    local commit_hash=$(git rev-parse --short HEAD)
    local branch=$(git branch --show-current)
    local commit_date=$(git log -1 --format=%cd --date=short)
    
    echo "📝 Version déployée:"
    echo "   Branche: $branch"
    echo "   Commit:  $commit_hash"
    echo "   Date:    $commit_date"
    
    # Status des services
    echo "🔧 Status des services:"
    echo "   Backend: $(systemctl is-active scrabble-backend)"
    echo "   Nginx:   $(systemctl is-active nginx)"
    echo "   PostgreSQL: $(systemctl is-active postgresql)"
    
    echo "╚═══════════════════════════════════════════════════════════╝"
}

# Fonction principale
main() {
    log "🚀 Début du déploiement automatisé Scrabble"
    
    # Trap pour gérer les erreurs et faire un rollback
    trap rollback ERR
    
    check_prerequisites
    backup_database
    backup_current_version
    fetch_code
    setup_database
    setup_backend
    run_database_migrations
    setup_frontend
    setup_backend_service
    reload_nginx
    health_check
    cleanup_old_backups
    show_deployment_info
    
    log "🎉 Déploiement terminé avec succès !"
    info "⏰ Durée totale: $SECONDS secondes"
}

# Gestion des arguments
case "${1:-}" in
    -h|--help)
        echo "Usage: $0 [branche] [options]"
        echo ""
        echo "Options:"
        echo "  -h, --help    Affiche cette aide"
        echo "  --no-backup   Skip la sauvegarde"
        echo ""
        echo "Exemples:"
        echo "  $0                # Déploie la branche main"
        echo "  $0 develop        # Déploie la branche develop"
        echo "  $0 feature/new    # Déploie une branche spécifique"
        exit 0
        ;;
    --version)
        echo "Scrabble Deploy Script v1.0"
        exit 0
        ;;
    *)
        # Confirmation avant déploiement en production
        if [ "${1:-main}" = "main" ] || [ "${1:-main}" = "master" ]; then
            echo ""
            warn "⚠️ Vous êtes sur le point de déployer en PRODUCTION"
            read -p "Êtes-vous sûr de vouloir continuer? (oui/non): " confirmation
            if [ "$confirmation" != "oui" ]; then
                log "Déploiement annulé par l'utilisateur"
                exit 0
            fi
        fi
        
        main "$@"
        ;;
esac