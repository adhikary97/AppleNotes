# Apple Notes UI Viewer

This Project is meant to help organize your Apple Notes.

## Firebase setup
1. Go to `https://console.firebase.google.com/`
2. Create Project and give project name
3. Click on Web Project and register project
4. Go to `Project Settings` -> `General`, copy firebase config
5. Create two `.env` files, one in `frontend` folder and one in `sync-scripts` folder

### .envs
```
# React Frontend Environment Variables
REACT_APP_FIREBASE_API_KEY=
REACT_APP_FIREBASE_AUTH_DOMAIN=
REACT_APP_FIREBASE_DATABASE_URL=
REACT_APP_FIREBASE_PROJECT_ID=
REACT_APP_FIREBASE_STORAGE_BUCKET=
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=
REACT_APP_FIREBASE_APP_ID=
```

```
# Python Sync Script Environment Variables
FIREBASE_API_KEY=
FIREBASE_AUTH_DOMAIN=
FIREBASE_DATABASE_URL=
FIREBASE_STORAGE_BUCKET=
```

## Note Sync Setup
```
cd sync-script
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python note_sync.py
```

## Frontend Setup
```
npm install
npm start
```