// Import Firebase SDK via CDN
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.6.10/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/9.6.10/firebase-auth.js";
import { getFirestore, doc, setDoc, getDoc } from "https://www.gstatic.com/firebasejs/9.6.10/firebase-firestore.js";

// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyDysapBKF3HQv7GG4yjcreh1sXp8aDyNA4",
    authDomain: "esd-team5.firebaseapp.com",
    projectId: "esd-team5",
    storageBucket: "esd-team5.firebasestorage.app",
    messagingSenderId: "623947543588",
    appId: "1:623947543588:web:810bf0100abba3ce7994b1",
    measurementId: "G-END9VCHCZV"
  };

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

// Export authentication and Firestore
export { auth, db, createUserWithEmailAndPassword, signInWithEmailAndPassword, doc, setDoc, getDoc };
