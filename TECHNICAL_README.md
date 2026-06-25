# 🚀 Synthèse Technique : Mises à Jour Architecture & Déploiement

Ce document résume les récentes évolutions architecturales et techniques apportées au backend **Map Action Impact Engine (Model_Deploy)**. Il est destiné à la Lead Dev afin d'avoir une vue d'ensemble sur les choix d'implémentation, la sécurité et la configuration du déploiement.

---

## 1. 🧠 Moteur d'Analyse IA & Multimodalité

### Moteur DeepSeek & Traitement du Langage
* **Raisonnement IA :** Intégration et ajustement du moteur basé sur DeepSeek pour la qualification des incidents humanitaires et environnementaux.
* **Pipeline ASR/NLP :** Mise en place d'un flux d'ingestion multimodal permettant de traiter les notes vocales (reconnaissance vocale) et d'en extraire le contexte en langues locales.

### Analyse Spatiale
* **Calcul des Rayons d'Impact :** Implémentation d'une logique de calcul permettant d'évaluer les risques secondaires sur les populations et infrastructures.
* **Intégration Google Earth Engine :** Les requêtes géospatiales sont fonctionnelles mais les accès ont été sécurisés (voir section Sécurité).

---

## 2. 📊 Taxonomie & Fiabilisation des Données

Afin de pallier les hallucinations de l'IA sur les métriques critiques, une approche hybride (Heuristique + IA) a été mise en place :

* **Filtre Anti-Bruit (Faux Positifs) :** L'IA a été instruite avec une taxonomie stricte pour rejeter immédiatement les images de test non pertinentes (environnements intérieurs, objets du quotidien).
* **Déterminisme des Scores :** Le `global impact score` et les rayons de risque ne sont plus laissés à la libre interprétation du LLM. Ils sont désormais calculés via un mapping strict basé sur les paramètres de sévérité de la taxonomie qualifiée par l'IA.

---

## 3. 🔒 Sécurité & Gestion des Dépendances

* **Offuscation API :** Les clés sensibles, en particulier le fichier de compte de service `gee-key.json` (Google Earth Engine), ont été isolées. Les dépendances aux API tierces ont été encapsulées pour éviter les fuites d'informations concurrentielles.
* **Sécurisation des variables :** Nettoyage de l'environnement et gestion stricte des variables via le `.env`.

---

## 4. ⚙️ CI/CD & Déploiement

* **Dockerisation :** Consolidation des fichiers `Dockerfile` et `Dockerfile.CI` pour assurer une reproductibilité exacte entre les environnements de staging et de production.
* **Pipeline GitHub Actions :** Le workflow dans `.github/workflows/ci_cd.yml` a été révisé pour orchestrer le build et le déploiement de manière automatisée. (Un fichier externe `_cd_pipeline.yaml` est également présent dans l'arborescence pour la gestion des runners/déploiements spécifiques).
* **Git Worktrees :** Résolution des conflits de configuration interne liés à Git pour stabiliser la branche de déploiement.

---

## 5. 💻 Environnement de Développement Local (Important)

**Note pour l'équipe sur Windows :**
* Le projet a rencontré des problèmes avec les environnements virtuels cross-platform. Le dossier `myenv` actuel contient des binaires Linux (`bin/`, `lib/`) incompatibles avec PowerShell.
* VS Code a tendance à auto-activer un environnement vide (`winenv`), ce qui provoque l'erreur `No module named uvicorn`.
* **Standard de lancement local actuel :** Ne pas utiliser de venv local sous Windows si les dépendances sont en global. Lancer directement le serveur via le module Python global :
  ```powershell
  python.exe -m uvicorn app.main:app --port 8000 --reload
  ```
