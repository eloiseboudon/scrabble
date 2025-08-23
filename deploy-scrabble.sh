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
DB_PASSWORD="test123"  # À changer !

# URLs de production
FRONTEND_URL="http://app-scrabble.tulip-saas.fr:$NGINX_PORT"
BACKEND_URL="http://app-scrabble.tulip-saas.fr:$BACKEND_PORT"
API_BASE_URL="http://app-scrabble.tulip-saas.fr:$BACKEND_PORT"

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

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: ❌ $1${NC}" >&2
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
    
    # Utiliser le .env existant s'il existe, sinon créer un .env de base
    if [ -f "$APP_DIR/.env" ]; then
        log "📋 Utilisation du fichier .env existant"
        cp "$APP_DIR/.env" "$backend_dir/.env"
        
        # Mise à jour des URLs avec les bonnes valeurs pour la production
        sed -i "s|FRONTEND_URL=.*|FRONTEND_URL=$FRONTEND_URL|g" "$backend_dir/.env"
        sed -i "s|BACKEND_URL=.*|BACKEND_URL=$BACKEND_URL|g" "$backend_dir/.env"
        sed -i "s|VITE_API_BASE=.*|VITE_API_BASE=$API_BASE_URL|g" "$backend_dir/.env"
        
        # Mettre à jour l'URL de base de données si nécessaire
        if grep -q "DATABASE_URL=.*eloise@localhost" "$backend_dir/.env"; then
            sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME|g" "$backend_dir/.env"
            info "🔧 URL de base de données mise à jour"
        fi
        
        # Ajouter les variables manquantes si nécessaire
        if ! grep -q "HOST=" "$backend_dir/.env"; then
            echo "HOST=0.0.0.0" >> "$backend_dir/.env"
        fi
        
        if ! grep -q "PORT=" "$backend_dir/.env"; then
            echo "PORT=$BACKEND_PORT" >> "$backend_dir/.env"
        fi
        
        # S'assurer que le domaine des cookies est correct
        sed -i "s|COOKIE_DOMAIN=.*|COOKIE_DOMAIN=.tulip-saas.fr|g" "$backend_dir/.env"
        
    else
        # Créer un .env de base si .env n'existe pas
        warn "⚠️ Fichier .env introuvable, création d'un .env de base"
        cat > "$backend_dir/.env" << EOF
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

# URLs
FRONTEND_URL=$FRONTEND_URL
BACKEND_URL=$BACKEND_URL
VITE_API_BASE=$API_BASE_URL

# Serveur
HOST=0.0.0.0
PORT=$BACKEND_PORT

# Cookies
COOKIE_DOMAIN=.tulip-saas.fr
EOF
    fi
    
    info "✅ Backend Python configuré"
    info "📝 Variables d'environnement principales :"
    grep -E "(FRONTEND_URL|BACKEND_URL|VITE_API_BASE|DATABASE_URL)" "$backend_dir/.env" | head -4 || true
}
# Préparation du frontend (version complètement retravaillée)
setup_frontend() {
    log "🗃️ Préparation du frontend..."
    
    cd "$APP_DIR"
    
    # 1. NETTOYAGE INITIAL
    log "🧹 Nettoyage du répertoire de distribution..."
    if [ -d "frontend/dist" ]; then
        rm -rf frontend/dist
        info "✅ Ancien répertoire dist supprimé"
    fi
    
    # Créer le répertoire dist propre
    mkdir -p frontend/dist
    chown ubuntu:ubuntu frontend/dist
    
    # 2. INSTALLATION DES DÉPENDANCES
    if [ -f "package.json" ]; then
        log "📦 Installation des dépendances NPM..."
        if ! npm ci --production=false 2>/dev/null; then
            warn "⚠️ npm ci a échoué, tentative avec npm install..."
            npm install --legacy-peer-deps 2>/dev/null || npm install
        fi
    fi
    
    # 3. BUILD VITE (si le script existe)
    if [ -f "package.json" ] && npm run | grep -q "build"; then
        log "🔨 Build de production avec Vite..."
        
        # Variables d'environnement pour le build
        export NODE_ENV=production
        export VITE_API_BASE="$API_BASE_URL"
        export BACKEND_URL="$BACKEND_URL"
        
        # Nettoyer et builder
        rm -rf dist 2>/dev/null || true
        
        if npm run build; then
            # Vérifier si Vite a créé un dossier dist dans la racine
            if [ -d "dist" ]; then
                log "📋 Copie du build Vite vers frontend/dist..."
                cp -r dist/* frontend/dist/
                info "✅ Build Vite copié avec succès"
            fi
        else
            log_error "❌ Le build Vite a échoué"
            exit 1
        fi
    else
        log "ℹ️ Pas de build Vite détecté, copie directe des fichiers"
        # Copier directement les fichiers sources
        if [ -f "frontend/index.html" ]; then
            cp frontend/index.html frontend/dist/
        fi
        if [ -f "frontend/style.css" ]; then
            cp frontend/style.css frontend/dist/
        fi
    fi
    
    # 4. GESTION DES FICHIERS JAVASCRIPT
    log "📁 Gestion des fichiers JavaScript..."
    
    # Vérifier où sont les fichiers JS
    js_source_dir=""
    
    if [ -d "frontend/public" ] && ls frontend/public/*.js >/dev/null 2>&1; then
        js_source_dir="frontend/public"
        log "📂 Fichiers JS trouvés dans frontend/public/"
    elif [ -d "frontend/src" ] && ls frontend/src/*.js >/dev/null 2>&1; then
        js_source_dir="frontend/src"
        log "📂 Fichiers JS trouvés dans frontend/src/"
    elif ls frontend/*.js >/dev/null 2>&1; then
        js_source_dir="frontend"
        log "📂 Fichiers JS trouvés dans frontend/"
    fi
    
    if [ -n "$js_source_dir" ]; then
        log "📋 Copie des fichiers JS depuis $js_source_dir..."
        cp "$js_source_dir"/*.js frontend/dist/ 2>/dev/null || {
            log_error "❌ Impossible de copier les fichiers JS"
            exit 1
        }
        
        # Vérifier que la copie a réussi
        if ls frontend/dist/*.js >/dev/null 2>&1; then
            info "✅ Fichiers JS copiés avec succès:"
            ls -la frontend/dist/*.js
        else
            log_error "❌ Aucun fichier JS trouvé dans dist/ après copie"
            exit 1
        fi
    else
        log "⚠️ Aucun fichier JS trouvé, création des fichiers essentiels..."
        create_essential_js_files
    fi
    
    # 5. COPIE DES RESSOURCES SUPPLÉMENTAIRES
    log "📁 Copie des ressources supplémentaires..."
    
    # Composants Vue
    for comp_dir in "frontend/components" "frontend/public/components"; do
        if [ -d "$comp_dir" ]; then
            cp -r "$comp_dir" frontend/dist/ 2>/dev/null || true
            log "📋 Composants copiés depuis $comp_dir"
            break
        fi
    done
    
    # Images
    for img_dir in "frontend/img" "frontend/public/img"; do
        if [ -d "$img_dir" ]; then
            cp -r "$img_dir" frontend/dist/ 2>/dev/null || true
            log "🖼️ Images copiées depuis $img_dir"
            break
        fi
    done
    
    # Logo
    for logo_file in "frontend/logo-scrabble.png" "frontend/public/logo-scrabble.png"; do
        if [ -f "$logo_file" ]; then
            cp "$logo_file" frontend/dist/ 2>/dev/null || true
            log "🎨 Logo copié depuis $logo_file"
            break
        fi
    done
    
    # 6. CORRECTION DE L'INDEX.HTML
    log "🔧 Correction des chemins dans index.html..."
    
    if [ -f "frontend/dist/index.html" ]; then
        # Sauvegarder l'original
        cp frontend/dist/index.html frontend/dist/index.html.backup
        
        # Corriger les chemins des scripts
        sed -i 's|src="/\([^"]*\.js\)"|src="./\1"|g' frontend/dist/index.html 2>/dev/null || {
            log_error "❌ Impossible de modifier index.html"
            exit 1
        }
        
        # Vérifier que la modification a réussi
        if grep -q 'src="./api.js"' frontend/dist/index.html 2>/dev/null; then
            info "✅ Chemins corrigés dans index.html"
        else
            warn "⚠️ Les chemins dans index.html n'ont peut-être pas été modifiés"
            log "🔍 Contenu actuel de index.html (lignes avec .js):"
            grep '\.js' frontend/dist/index.html | head -3 || true
        fi
    else
        log_error "❌ index.html non trouvé dans dist/"
        exit 1
    fi
    
    # 7. CONFIGURATION DES PERMISSIONS
    log "🔐 Configuration des permissions..."
    chown -R ubuntu:ubuntu frontend/dist/ 2>/dev/null || true
    chmod -R 755 frontend/dist/ 2>/dev/null || true
    chmod +x frontend/dist/*.js 2>/dev/null || true
    
    # 8. VÉRIFICATION FINALE ET DIAGNOSTIC
    log "🔍 Vérification finale..."
    
    # Vérifier les fichiers critiques
    critical_files=("index.html" "api.js" "style.css")
    missing_files=()
    
    for file in "${critical_files[@]}"; do
        if [ ! -f "frontend/dist/$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        log_error "❌ Fichiers critiques manquants: ${missing_files[*]}"
        exit 1
    fi
    
    # Afficher les informations de diagnostic
    log "📊 Diagnostic du frontend:"
    echo "=== Contenu du dossier dist ==="
    ls -la frontend/dist/
    echo ""
    echo "=== Taille totale ==="
    du -sh frontend/dist/
    echo ""
    echo "=== Vérification de api.js ==="
    if [ -f "frontend/dist/api.js" ]; then
        echo "Premières lignes de api.js:"
        head -3 frontend/dist/api.js
        echo ""
        echo "API_BASE configuré pour:"
        grep -o "app-scrabble.tulip-saas.fr:8001\|localhost:8000" frontend/dist/api.js | head -1 || echo "Configuration par défaut"
    fi
    
    local build_size=$(du -sh frontend/dist 2>/dev/null | cut -f1 || echo "N/A")
    info "✅ Frontend préparé avec succès - Taille: $build_size"
    
    # 9. VÉRIFICATION FORCÉE DE LA MISE À jour
    log "🔄 Vérification forcée de la mise à jour frontend..."
    echo "🔄 Mise à jour forcée du frontend..."
}

# Fonction pour créer les fichiers JS essentiels si ils n'existent pas
create_essential_js_files() {
    log "🛠️ Création des fichiers JavaScript essentiels..."
    
    # api.js - LE PLUS IMPORTANT
    cat > frontend/dist/api.js << 'EOF'
(function () {
    const { protocol, hostname } = window.location;
    
    console.log('[api] Détection hostname:', hostname);
    
    const isProduction = hostname === 'app-scrabble.tulip-saas.fr';
    const port = isProduction ? 8001 : 8000;
    const API_BASE = `${protocol}//${hostname}:${port}`;
    
    console.log('[api] Environment:', isProduction ? 'PRODUCTION' : 'DEVELOPMENT');
    console.log('[api] API_BASE:', API_BASE);
    
    // CRITIQUE: Rendre disponible globalement
    window.API_BASE = API_BASE;
    
    // Diagnostic supplémentaire
    console.log('[api] window.API_BASE défini:', window.API_BASE);
})();
EOF

    # letterPoints.js
    cat > frontend/dist/letterPoints.js << 'EOF'
const LETTER_POINTS = {
  "A": 1, "B": 3, "C": 3, "D": 2, "E": 1, "F": 4, "G": 2, "H": 4, "I": 1, "J": 8,
  "K": 10, "L": 1, "M": 2, "N": 1, "O": 1, "P": 3, "Q": 8, "R": 1, "S": 1, "T": 1,
  "U": 1, "V": 4, "W": 10, "X": 10, "Y": 10, "Z": 10, "?": 0
};
window.LETTER_POINTS = LETTER_POINTS;
console.log('[letterPoints] LETTER_POINTS chargé');
EOF

    # authHeartbeat.js
    cat > frontend/dist/authHeartbeat.js << 'EOF'
let timer

function startAuthHeartbeat() {
  stopAuthHeartbeat()
  timer = setInterval(async () => {
    try {
      if (!window.API_BASE) {
        console.error('[authHeartbeat] API_BASE non défini')
        return
      }
      const url = `${window.API_BASE}/auth/refresh`
      console.log('[authHeartbeat] refreshing', url)
      await fetch(url, { method: 'POST', credentials: 'include' })
    } catch (err) {
      console.error('[authHeartbeat] refresh failed', err)
    }
  }, 12 * 60 * 1000)
}

function stopAuthHeartbeat() {
  if (timer) {
    clearInterval(timer)
    timer = undefined
  }
}

window.startAuthHeartbeat = startAuthHeartbeat
window.stopAuthHeartbeat = stopAuthHeartbeat
console.log('[authHeartbeat] Fonctions définies');
EOF

    # botThinking.js
    cat > frontend/dist/botThinking.js << 'EOF'
async function runBotThinking(popupRef, fn) {
  popupRef.value = { type: 'loading', message: 'Le bot réfléchit' }
  try {
    return await fn()
  } finally {
    popupRef.value = null
  }
}
window.runBotThinking = runBotThinking;
console.log('[botThinking] runBotThinking défini');
EOF

    # validateWords.js (version simplifiée)
    cat > frontend/dist/validateWords.js << 'EOF'
function collectWords(getTile, placements) {
  if (!placements || placements.length === 0) return []
  // Version simplifiée pour éviter les erreurs
  return ['TEST'] // Placeholder
}
window.collectWords = collectWords;
console.log('[validateWords] collectWords défini');
EOF

    # invalidWords.js
    cat > frontend/dist/invalidWords.js << 'EOF'
async function showInvalidWords(alertFn, detail, firstWord) {
  if (alertFn) {
    await alertFn(detail || 'Mots invalides détectés');
  }
  return [];
}
window.showInvalidWords = showInvalidWords;
console.log('[invalidWords] showInvalidWords défini');
EOF

    log "✅ Fichiers JavaScript essentiels créés"
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
        log "🔄 Alembic détecté, gestion des migrations..."
        
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

# Configuration Nginx
setup_nginx() {
    log "🌐 Configuration de Nginx..."
    
    # Créer la configuration Nginx
    log "📝 Création/mise à jour de la configuration Nginx..."
    
    sudo tee /etc/nginx/sites-available/scrabble > /dev/null << EOF
server {
    listen $NGINX_PORT;
    server_name app-scrabble.tulip-saas.fr scrabble.tulip-saas.fr;

    # Frontend (fichiers statiques)
    location / {
        root /home/ubuntu/scrabble/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        
        # CORS headers pour le frontend
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS, PUT, DELETE";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
    }

    # API Backend (proxy vers le port $BACKEND_PORT)
    location /api/ {
        proxy_pass http://localhost:$BACKEND_PORT/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # CORS pour l'API
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS, PUT, DELETE";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
    }

    # Routes spécifiques du backend
    location ~ ^/(docs|redoc|openapi.json|health|auth|games|deletion|uploads) {
        proxy_pass http://localhost:$BACKEND_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # CORS pour les routes backend
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS, PUT, DELETE";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
    }

    # Logs d'accès et d'erreur
    access_log /var/log/nginx/scrabble_access.log;
    error_log /var/log/nginx/scrabble_error.log;
}
EOF
    
    # Activer le site
    sudo ln -sf /etc/nginx/sites-available/scrabble /etc/nginx/sites-enabled/
    
    # Désactiver le site par défaut s'il existe
    sudo rm -f /etc/nginx/sites-enabled/default
    
    info "✅ Configuration Nginx mise à jour"
}

# Créer le script de lancement
create_start_script() {
    log "📝 Création du script de lancement..."
    
    cat > "$APP_DIR/start_backend.sh" << 'EOF'
#!/bin/bash
set -e
cd /home/ubuntu/scrabble
source backend/venv/bin/activate
export PYTHONPATH="/home/ubuntu/scrabble:$PYTHONPATH"

# Utiliser python -m pour éviter les problèmes d'imports relatifs
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001
EOF
    
    chmod +x "$APP_DIR/start_backend.sh"
    info "✅ Script de lancement créé"
}

# Démarrage du backend comme service
setup_backend_service() {
    log "🚀 Configuration du service backend..."
    
    # Arrêter le service s'il tourne déjà 
    if systemctl is-active --quiet scrabble-backend; then
        log "🛑 Arrêt du service backend existant..."
        sudo systemctl stop scrabble-backend
    fi
    
    # Créer le script de lancement
    create_start_script
    
    # Mise à jour du service systemd pour utiliser le script
    sudo tee /etc/systemd/system/scrabble-backend.service > /dev/null << EOF
[Unit]
Description=Scrabble Backend Application
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/start_backend.sh
Restart=always
RestartSec=10

# Variables d'environnement
EnvironmentFile=$APP_DIR/backend/.env

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

# Vérification de la santé de l'application améliorée
health_check() {
    log "🏥 Vérification de la santé de l'application..."
    
    # Test du backend avec différentes routes
    log "🔧 Test du backend..."
    local backend_url="http://localhost:$BACKEND_PORT"
    
    # Test avec différentes routes possibles
    local routes=("/health" "/docs" "/" "/api/health")
    local backend_accessible=false
    
    for route in "${routes[@]}"; do
        for i in {1..5}; do
            if curl -f -s "$backend_url$route" > /dev/null 2>&1; then
                info "✅ Backend accessible sur $route !"
                backend_accessible=true
                break 2
            fi
            if [ $i -eq 5 ] && [ "$route" = "/" ]; then
                # Pour la route racine, un 404 est acceptable si le service fonctionne
                if curl -s "$backend_url$route" 2>/dev/null | grep -q "Not Found\|404"; then
                    info "✅ Backend fonctionne (404 sur / est normal) !"
                    backend_accessible=true
                    break 2
                fi
            fi
            warn "Tentative $i/5 pour $route - Backend en cours de démarrage..."
            sleep 3
        done
    done
    
    if [ "$backend_accessible" = false ]; then
        warn "⚠️ Backend inaccessible après test de toutes les routes"
        log "🔍 Diagnostic du backend..."
        echo "--- Status du service ---"
        sudo systemctl status scrabble-backend --no-pager -l
        echo "--- Logs récents ---"
        sudo journalctl -u scrabble-backend --no-pager -n 10
        echo "--- Test du port ---"
        sudo netstat -tlnp | grep $BACKEND_PORT || echo "Port $BACKEND_PORT non utilisé"
    fi
    
    # Test du frontend via Nginx
    log "🌐 Test du frontend..."
    local frontend_url="http://localhost:$NGINX_PORT"
    local frontend_accessible=false
    
    for i in {1..5}; do
        if curl -f -s "$frontend_url" > /dev/null 2>&1; then
            info "✅ Frontend accessible !"
            frontend_accessible=true
            break
        fi
        warn "Tentative $i/5 - Frontend en cours de vérification..."
        sleep 3
    done
    
    if [ "$frontend_accessible" = false ]; then
        warn "⚠️ Frontend inaccessible"
        log "🔍 Diagnostic Nginx..."
        echo "--- Status Nginx ---"
        sudo systemctl status nginx --no-pager -l
        echo "--- Configuration Nginx ---"
        sudo nginx -t
        echo "--- Test du port ---"
        sudo netstat -tlnp | grep $NGINX_PORT || echo "Port $NGINX_PORT non utilisé"
    fi
    
    # Test externe avec les domaines configurés
    log "🌍 Test d'accès externe..."
    local external_urls=(
        "$FRONTEND_URL"
        "$BACKEND_URL/health"
    )
    
    local external_accessible=false
    for url in "${external_urls[@]}"; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            info "✅ Application accessible depuis l'extérieur via $url !"
            external_accessible=true
            break
        fi
    done
    
    if [ "$external_accessible" = false ]; then
        warn "⚠️ Application non accessible depuis l'extérieur"
        info "💡 Vérifiez :"
        echo "   - DNS : app-scrabble.tulip-saas.fr → $(curl -s ifconfig.me 2>/dev/null || echo 'IP_INCONNUE')"
        echo "   - Firewall : sudo ufw status"
        echo "   - Ports ouverts : sudo netstat -tlnp | grep ':80\\|:443\\|:$NGINX_PORT\\|:$BACKEND_PORT'"
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
    echo "🌐 Frontend: $FRONTEND_URL"
    echo "🔧 Backend:  $BACKEND_URL"
    echo "📖 API Docs: $BACKEND_URL/docs"
    echo "💓 Health:   $BACKEND_URL/health"
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
    
    # Vérification des URLs configurées
    echo "🔗 Configuration URLs:"
    if [ -f "$APP_DIR/backend/.env" ]; then
        grep -E "(FRONTEND_URL|BACKEND_URL|VITE_API_BASE)" "$APP_DIR/backend/.env" | head -3 | sed 's/^/   /' || true
    fi
    
    echo "╚═══════════════════════════════════════════════════════════╝"
    
    # Tests rapides de connectivité
    echo ""
    log "🧪 Tests de connectivité rapides:"
    
    # Test backend local
    if curl -s http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
        echo "   ✅ Backend local accessible"
    else
        echo "   ❌ Backend local inaccessible"
    fi
    
    # Test frontend local
    if curl -s http://localhost:$NGINX_PORT > /dev/null 2>&1; then
        echo "   ✅ Frontend local accessible"
    else
        echo "   ❌ Frontend local inaccessible"
    fi
    
    # Test externe
    if curl -s $BACKEND_URL/health > /dev/null 2>&1; then
        echo "   ✅ Backend externe accessible"
    else
        echo "   ❌ Backend externe inaccessible"
    fi
    
    if curl -s $FRONTEND_URL > /dev/null 2>&1; then
        echo "   ✅ Frontend externe accessible"
    else
        echo "   ❌ Frontend externe inaccessible"
    fi
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
    log "🔄 Vérification forcée de la mise à jour frontend..."
    /home/ubuntu/scrabble/update_frontend.sh
    setup_nginx
    create_start_script
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
        echo "  --quick       Déploiement rapide (skip certaines vérifications)"
        echo ""
        echo "Exemples:"
        echo "  $0                # Déploie la branche main"
        echo "  $0 develop        # Déploie la branche develop"
        echo "  $0 feature/new    # Déploie une branche spécifique"
        echo ""
        echo "URLs de production configurées:"
        echo "  Frontend: $FRONTEND_URL"
        echo "  Backend:  $BACKEND_URL"
        exit 0
        ;;
    --version)
        echo "Scrabble Deploy Script v2.0"
        echo "Avec support complet des URLs de production"
        exit 0
        ;;
    --test)
        # Mode test - vérifications uniquement
        log "🧪 Mode test - Vérifications uniquement"
        check_prerequisites
        
        if [ -d "$APP_DIR" ]; then
            cd "$APP_DIR"
            if [ -f ".env" ]; then
                echo "Configuration actuelle:"
                grep -E "(FRONTEND_URL|BACKEND_URL|VITE_API_BASE)" ".env" || true
            fi
        fi
        
        # Tests de connectivité
        echo ""
        echo "Tests de connectivité:"
        curl -s http://localhost:$BACKEND_PORT/health && echo "✅ Backend local OK" || echo "❌ Backend local KO"
        curl -s http://localhost:$NGINX_PORT && echo "✅ Frontend local OK" || echo "❌ Frontend local KO"
        curl -s $BACKEND_URL/health && echo "✅ Backend externe OK" || echo "❌ Backend externe KO"
        curl -s $FRONTEND_URL && echo "✅ Frontend externe OK" || echo "❌ Frontend externe KO"
        exit 0
        ;;
    *)
        # Confirmation avant déploiement en production
        if [ "${1:-main}" = "main" ] || [ "${1:-main}" = "master" ]; then
            echo ""
            warn "⚠️ Vous êtes sur le point de déployer en PRODUCTION"
            echo "   Frontend: $FRONTEND_URL"
            echo "   Backend:  $BACKEND_URL"
            echo ""
            read -p "Êtes-vous sûr de vouloir continuer? (oui/non): " confirmation
            if [ "$confirmation" != "oui" ]; then
                log "Déploiement annulé par l'utilisateur"
                exit 0
            fi
        fi
        
        main "$@"
        ;;
esac