🧱 Étapes du plan de développement
🔹 1. Setup local de l’environnement
🔧 Objectif : pouvoir lancer le frontend et le backend en local avec persistance des données.

🆗 Init backend avec FastAPI (ou Flask si tu préfères)

🆗 Init frontend avec Vue 3 + Vite

🆗 Setup BDD PostgreSQL locale avec ORM (SQLAlchemy) ou Prisma (si besoin d’un layer JS)

 Dockeriser l’ensemble pour développement simplifié

🆗 Créer repo GitHub avec branche main et dev

✅ 2. Grille de Scrabble (UI + logique)
🎯 MVP 1 : Affichage et interaction simple

🆗 Afficher la grille Scrabble standard (15x15)

🆗 Permettre le placement de lettres (drag & drop ou clic + clavier)

🆗 Afficher le score temporaire d’un mot placé

🆗 Bonus : lecture du fichier ODS8 pour vérification d’un mot placé

🔹 3. Intégration du dictionnaire ODS8
🆗 Récupérer la base de mots ODS8 (GitHub, CSV ou autre)

🆗 Charger en BDD ou dans un système de recherche optimisé (Trie, Redis, etc.)

🆗 Endpoint is_valid_word(word: str) dans le backend

🔹 4. Création du système utilisateur
🎯 MVP 2 : Authentification

 Auth backend avec FastAPI Users (ou maison) + JWT

 Intégrer Google OAuth (sign in with Google)

 Front : formulaire de login + bouton Google

 Gestion des sessions côté front

🔹 5a. Gestion des parties contre bot
🆗 Création d’une partie (1v1 ou contre IA plus tard)

🆗 Placement des lettres

🆗 Calcul des scores

 Fin de partie, sauvegarde

 Historique des parties (rejouer, consulter, supprimer)

 🔹 5b. Gestion des parties 1v1
 Création d’une partie (1v1 ou contre IA plus tard)

 Placement des lettres

 Calcul des scores

 Fin de partie, sauvegarde

 Historique des parties (rejouer, consulter, supprimer)

  🔹 5c. Gestion des parties multijoueur
 Création d’une partie (1v1 ou contre IA plus tard)

 Placement des lettres

 Calcul des scores

 Fin de partie, sauvegarde

 Historique des parties (rejouer, consulter, supprimer)

🔹 6. Interface mobile (web responsive d''abord)
🆗 Adapter le frontend Vue en responsive (taille mobile)

 Tester comportement tactile (placement, scroll, zoom)

 Bonus : transformer en PWA ou wrapper via Capacitor pour Android/iOS

🔹 7. Déploiement -- solution à trouver (simple sans Docker en premier)
 Déploiement sur un VPS (OVH ou autre) avec Docker Compose

 HTTPS avec Let’s Encrypt

 Utilisation de services comme Railway, Fly.io ou Render (facultatif pour POC)

 Nom de domaine et configuration DNS

