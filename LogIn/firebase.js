// firebase-init.js

import { initializeApp } from "https://www.gstatic.com/firebasejs/9.6.10/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/9.6.10/firebase-auth.js";
import { getFirestore, doc, setDoc, getDoc } from "https://www.gstatic.com/firebasejs/9.6.10/firebase-firestore.js";

// Import Firebase config securely
import { firebaseConfig } from "./config.js";

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

// Export authentication and Firestore
export { auth, db, createUserWithEmailAndPassword, signInWithEmailAndPassword, doc, setDoc, getDoc };
