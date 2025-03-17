# TFE---Party-Screen
A Repository for Documentation, Code and any usefull Information for my TFE

### Préparer le Nginx 
#### Dégager le Fichier par défaut Nginx
```
sudo rm /etc/nginx/sites-enabled/default
sudo cp /home/test/Desktop/Test-Party-Screen/nginx-config/sveltekit /etc/nginx/sites-available
sudo cp /etc/nginx/sites-available/sveltekit /etc/nginx/sites-enabled
sudo nginx -t  # Vérifier que la config est bonne
sudo systemctl restart nginx  # Redémarrer Nginx
```

#### Build le Frontend 
Se placer dans le répertoire Frontend là où il y a `package.json` (il doit y avoir un dossier appelé `build`
```
npm run build
```

#### Run le Frontend Buildé
`node build/index.js`

#### Run le Frontend non Buildé
`npm run dev`

#### Run le Backend
`uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

#### Run Nginx et activer son démarrage au démarrage du SBC
```
sudo systemctl start nginx
sudo systemctl enable nginx
```

#### Run Mosquitto et activer son démarrage au démarrage du SBC
```
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

#### Pour faire une requête Curl depuis le terminal pour appeler le Backend :
	`curl -X POST "http://127.0.0.1:8000/send_message/" -H "Content-Type: application/json" -d '{"message": "Caca prout"}`

#### Pour souscrire à un topic MQTT et voir/recevoir les messages :
	`mosquitto_sub -h 127.0.0.1 -t "topic/esp8266"`

#### Pour publier un message sur un topic MQTT :
	`mosquitto_pub -h 127.0.0.1 -t "topic/esp8266" -m "Salut la compagnie"`

#### Pour activer environnement Python : 
	`source myenv/bin/activate`

#### Pour desactiver environnement Python :
	`deactivate`

#### Pour envoyer un fichier de mon PC vers SBC Ubuntu/Debian/Armbian/... :
	`scp mqtt.py root@192.168.137.91:/home/test/Desktop/Test-Party-Screen/backend/app/utils`
