import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import { initializeApp } from "firebase/app";
import { getDatabase } from "firebase/database";
import NotesList from "./NotesList";
import NoteDetail from "./NoteDetail";
import "./App.css";

// Firebase configuration
const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY,
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
  databaseURL: process.env.REACT_APP_FIREBASE_DATABASE_URL,
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.REACT_APP_FIREBASE_APP_ID,
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const database = getDatabase(app);

// Default sorting constants
export const DEFAULT_SORT_FIELD = "updated_date";
export const DEFAULT_SORT_ORDER = "desc";

function App() {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <h1>
            <Link to="/">Notes Dashboard</Link>
          </h1>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<NotesList />} />
            <Route path="/notes/:noteId" element={<NoteDetail />} />
          </Routes>
        </main>
        <footer className="app-footer">
          <p>Apple Notes Sync Dashboard</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
