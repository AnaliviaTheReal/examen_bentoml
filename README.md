# Examen BentoML

Voici comment est construit le dossier de rendu de l'examen:

```bash       
├── examen_bentoml          
│   ├── data       
│   │   ├── processed      
│   │   └── raw           
│   ├── models      
│   ├── src       
│   └── README.md
```

# Projet BentoML -- Prédiction d'admission universitaire

Auteur : Analivia Valery

Cette API BentoML permet de prédire la probabilité d'admission d'un
étudiant à partir de variables académiques. Ce document décrit les
commandes nécessaires pour lancer l'API conteneurisée et exécuter les
tests unitaires.

------------------------------------------------------------------------

# Contenu de l’archive

- `valery_analivia_admissions_service.tar` : image Docker de l’API BentoML
- `src/service.py` : service BentoML
- `tests/test_api.py` : tests unitaires pytest
- `bentofile.yaml`, `requirements.txt` : configuration BentoML
- `README.md` : ce fichier

# 1. Lancement de l'API conteneurisée

## 1.1. Charger l'image Docker fournie

Le fichier valery_analivia_admissions_service.tar doit être présent à la
racine du projet.

Commande :

docker load -i valery_analivia_admissions_service.tar

Vérifier que l'image est présente :

docker images | grep analivia_admissions_service

------------------------------------------------------------------------

## 1.2. Lancer l'API

docker run --rm -p 3000:3000 analivia_admissions_service:latest

L'API est alors disponible sur :

http://localhost:3000

------------------------------------------------------------------------

# 2. Utilisation de l'API

## 2.1. Endpoint /login (POST)

Permet de récupérer un token JWT.

Commande :

curl -X POST http://localhost:3000/login \
  -H "Content-Type: application/json" \
  -d '{"payload":{"username":"admin","password":"admin123"}}'

Exemple de réponse :

{ "token": "xxxxx.yyyyy.zzzzz" }

------------------------------------------------------------------------

## 2.2. Endpoint /predict (POST)

Requiert un token JWT valide.

Commande :

curl -X POST http://localhost:3000/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN_JWT>" \
  -d '{"payload":{"GRE Score":320,"TOEFL Score":110,"University Rating":4,"SOP":4.5,"LOR":4.0,"CGPA":9.2,"Research":1}}'

Exemple de réponse :

{ "user": "user123", "prediction": 0.76 }

------------------------------------------------------------------------

# 3. Exécution des tests unitaires

L'API doit être lancée via Docker AVANT d'exécuter les tests.

Commande :

pytest tests/test_api.py -v

Résultat attendu :

passed
