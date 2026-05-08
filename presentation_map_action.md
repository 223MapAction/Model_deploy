# 🌍 Map Action Impact Engine : Présentation Technique & Stratégique

Ce document détaille l'architecture, l'innovation technique et la vision stratégique du projet **Map Action Impact Engine**. Il a été conçu pour servir de support de présentation technique et métier.

---

## 1. 🎯 La Vision : Ce que permet Map Action

Dans le domaine humanitaire et environnemental, le temps de réaction est le facteur le plus critique. L'évaluation de l'impact d'une catastrophe (pollution, inondation, incendie) nécessite habituellement le croisement manuel de données complexes (satellites, recensements, météo).

**Map Action Impact Engine** révolutionne ce processus. À partir d'une simple **photo** et d'une **coordonnée GPS**, le système est capable de générer en quelques secondes un rapport complet comprenant :
*   La classification précise de l'incident.
*   Un "Rayon d'Impact" calculé dynamiquement selon la physique de l'environnement.
*   L'estimation chiffrée de la population exposée (démographie détaillée).
*   L'inventaire des infrastructures critiques menacées (écoles, hôpitaux, points d'eau).
*   Un score de gravité global et des recommandations d'intervention immédiates.

---

## 2. 🚀 La Prouesse Technique : Comment le système fonctionne-t-il ?

L'innovation majeure de Map Action réside dans sa **"Logique Hybride Multimodale"**. Le système ne se contente pas d'interroger une IA ; il orchestre un ballet complexe entre des modèles d'intelligence artificielle de pointe et des bases de données géospatiales en temps réel.

### A. L'Analyse Visuelle Deep Learning (Gemini Vision)
Dès la réception de l'image, le système interroge le modèle Gemini pour extraire une compréhension sémantique de la scène.
*   **Identification des vecteurs de propagation** : L'IA ne dit pas juste "C'est de l'eau sale". Elle identifie si la pollution peut se propager par le vent, par le courant d'eau, ou par des vecteurs biologiques (moustiques/rongeurs).

### B. Le Moteur de Physique Environnementale
Contrairement aux outils traditionnels qui tracent des cercles arbitraires (ex: rayon fixe de 1km), Map Action calcule un **rayon dynamique et factuel**.
*   **Logique de propagation** : Si le vecteur est l'eau, le moteur calcule la distance en fonction de la **pente du terrain** et des **précipitations**. S'il ne pleut pas mais qu'il y a un courant, un étalement de base (ex: 600m) est appliqué.
*   **Alerte Secondaire** : Le système distingue le rayon d'impact "immédiat" et génère une alerte quantifiée pour la zone de "propagation potentielle".

### C. La Logique Hybride Satellite-OSM (L'intelligence de la donnée)
Dans des pays comme le Mali, les cartes (OpenStreetMap) sont souvent incomplètes. Map Action contourne ce problème grâce à un arbitrage intelligent :
*   **Micro-ciblage** : Le système croise les coordonnées avec OSM pour compter les bâtiments réels.
*   **Arbitrage Satellite (Google Earth Engine)** : Si OSM est vide mais que le satellite (NDVI / Land Use) détecte une zone "Urbaine / Bâti", le système prend le relais. Il estime automatiquement une densité de bâtiments basée sur la surface du rayon et injecte de manière probabiliste les infrastructures sociales (marchés, points d'eau) qui existent nécessairement dans une telle zone.
*   **Modélisation démographique** : Les bâtiments (réels ou estimés) sont convertis en population exposée en utilisant des ratios stricts basés sur les données de l'INSTAT Mali.

### D. Le Chatbot Stratégique (DeepSeek V4-Pro)
Pour accompagner la décision, un assistant expert est intégré. Il reçoit en **cotexte caché** l'intégralité du rapport chiffré (météo, population, risques). Grâce à un système de **Streaming Temps Réel** (affichage mot à mot), l'utilisateur bénéficie d'une réactivité immédiate et de conseils ultra-ciblés, formatés professionnellement.

---

## 3. ⚙️ Architecture Technologique (Stack)

*   **Backend** : Python / FastAPI (Hautes performances, asynchrone).
*   **IA Visuelle** : Google Gemini (Modèle 3.1 Flash Lite Preview pour l'équilibre vitesse/coût).
*   **IA Chatbot** : DeepSeek V4-Pro (Excellence dans le raisonnement stratégique et la génération de texte structuré).
*   **Géospatial** : 
    *   API Overpass (OpenStreetMap) pour le tissu social.
    *   Google Earth Engine (GEE) & API Météo (Open-Meteo) pour le contexte topographique.
*   **Interface (Frontend)** : HTML5 / CSS Vanilla / Vanilla JS, injecté dynamiquement avec des animations fluides (glassmorphism, indicateurs de frappe) pour une expérience utilisateur premium.

---

## 4. 🚧 Limites Actuelles

Toute technologie d'avant-garde possède ses défis :
1.  **Dépendance aux API tierces** : Le système repose sur la disponibilité des serveurs de Google (Gemini, GEE) et d'OpenStreetMap. Une erreur "503 Service Unavailable" côté fournisseur peut bloquer temporairement l'analyse.
2.  **Angle mort de l'image** : L'IA évalue la sévérité d'après ce qui est *visible* sur la photo. Une pollution chimique incolore ou souterraine ne sera pas correctement évaluée sans capteurs physiques supplémentaires.
3.  **Estimation probabiliste** : Dans les zones non cartographiées, la population reste une *estimation* probabiliste basée sur la surface. Elle ne remplace pas un recensement exact.

---

## 5. 🔮 Perspectives & Avenir

Map Action Impact Engine pose les bases d'un système prédictif révolutionnaire :
*   **Analyse Temporelle (Time-lapse)** : Intégrer l'historique satellite pour comparer automatiquement l'état de la zone *avant* et *après* l'incident.
*   **Intégration de Capteurs de Qualité de l'Air (IoT)** : Connecter le système à des réseaux de capteurs au sol pour mesurer en temps réel les PM2.5, PM10 et les gaz toxiques, permettant de valider les alertes visuelles par des données physiques précises.
*   **Couches de Données Personnalisées** : Permettre aux ONG ou aux gouvernements d'injecter leurs propres bases de données (ex: cadastre local, recensement de la protection civile) pour remplacer les estimations probabilistes par des données certifiées.
*   **Génération de Rapports PDF Automatiques** : Transformer l'analyse et les conseils du chatbot en un rapport PDF formaté, prêt à être envoyé aux ministères ou aux bailleurs de fonds.

---
*Ce document résume le travail d'ingénierie avancée réalisé pour rendre l'analyse environnementale à la fois hyper-réaliste, rigoureuse et accessible.*
