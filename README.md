# Examen BentoML

Ce repertoire contient l'architecture basique afin de rendre l'évaluation pour l'examen BentoML.

Vous êtes libres d'ajouter d'autres dossiers ou fichiers si vous jugez utile de le faire.

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

Afin de pouvoir commencer le projet vous devez suivre les étapes suivantes:

- Forker le projet sur votre compte github

- Cloner le projet sur votre machine

- Récuperer le jeu de données à partir du lien suivant: [Lien de téléchargement]( https://datascientest.s3-eu-west-1.amazonaws.com/examen_bentoml/admissions.csv)


Bon travail!



# Examen BentoML — Admissions Prediction

# Prérequis
- Docker installé 
- (Optionnel) Python 3.12 + venv si vous voulez lancer les tests hors Docker

# Lancer ces commandes dans l'ordre
```bash
docker load -i valery_analivia_admissions_service.tar
docker images | grep analivia_admissions_service
docker run --rm -p 3000:3000 analivia_admissions_service:latest
