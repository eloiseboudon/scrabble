# 🧱 Plan de Développement du Projet Scrabble

## 🔹 1. Setup Local de l'Environnement
**🔧 Objectif** : Pouvoir lancer le frontend et le backend en local avec persistance des données.

- [x] Init backend avec FastAPI (ou Flask si tu préfères)
- [x] Init frontend avec Vue 3 + Vite
- [x] Setup BDD PostgreSQL locale avec ORM (SQLAlchemy) ou Prisma
- [ ] Dockeriser l'ensemble pour développement simplifié
- [x] Créer repo GitHub avec branche main et dev

## ✅ 2. Grille de Scrabble (UI + Logique)
**🎯 MVP 1** : Affichage et interaction simple

- [x] Afficher la grille Scrabble standard (15x15)
- [x] Permettre le placement de lettres (drag & drop ou clic + clavier)
- [x] Afficher le score temporaire d'un mot placé
- [x] Bonus : lecture du fichier ODS8 pour vérification d'un mot placé

## 🔹 3. Intégration du dictionnaire ODS8
**🆗 Récupérer la base de mots ODS8 (GitHub, CSV ou autre)**

- [ ] Charger en BDD ou dans un système de recherche optimisé (Trie, Redis, etc.)
- [ ] Endpoint is_valid_word(word: str) dans le backend

## 🔹 4. Création du système utilisateur
**🎯 MVP 2** : Authentification

- [ ] Auth backend avec FastAPI Users (ou maison) + JWT
- [ ] Intégrer Google OAuth (sign in with Google)
- [ ] Front : formulaire de login + bouton Google
- [ ] Gestion des sessions côté front

## 🔹 5a. Gestion des parties contre bot

- [x] Placement des lettres
- [x] Calcul des scores
- [ ] Gestion du niveau de l'IA (très facile : < 15pts, facile : < 20pts, moyen : < 25pts, difficile : < 30pts, hardcore : > 100pts)
- [ ] Fin de partie, sauvegarde
- [ ] Historique des parties (rejouer, consulter, supprimer)

## 🔹 5b. Gestion des parties 1v1

- [ ] Placement des lettres
- [ ] Calcul des scores
- [ ] Fin de partie, sauvegarde
- [ ] Historique des parties

## 🔸 5c. Mode Multijoueur
- [ ] Création d'une partie
- [ ] Placement des lettres
- [ ] Calcul des scores
- [ ] Fin de partie, sauvegarde
- [ ] Historique des parties

## 🔹 5d. Mode Duplicate

- [ ] Création d'une partie
- [ ] Placement des lettres
- [ ] Calcul des scores
- [ ] Fin de partie, sauvegarde
- [ ] Historique des parties

## 🔹 Transverse

- [ ] Message dans pop-up
- [ ] Si mot non valide croix sinon bouton valider + nombre de point affiché
- [ ] Si pas de tuiles posées bouton valider masqué et bouton passé

## 🧪 6. Tests
- [ ] Tests unitaires
- [ ] Tests d'intégration
- [ ] Tests backend
- [ ] Tests frontend

## 📱 7. Interface Mobile
- [x] Adapter le frontend Vue en responsive (taille mobile)
- [ ] Tester comportement tactile (placement, scroll, zoom)
- [ ] Bonus : transformer en PWA ou wrapper via Capacitor pour Android/iOS

## 🚀 8. Déploiement
**Solution à trouver (simple sans Docker en premier)**
- [ ] Déploiement sur VPS (OVH ou autre) avec Docker Compose
- [ ] Configuration HTTPS avec Let's Encrypt
- [ ] Services alternatifs : Railway, Fly.io ou Render (facultatif)
- [ ] Configuration du nom de domaine et DNS
