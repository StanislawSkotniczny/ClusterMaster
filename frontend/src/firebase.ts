// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyDbrgoy_oGPYzeThxH9Ukks5wj1anvxM1Y",
    authDomain: "clustermaster-af054.firebaseapp.com",
    projectId: "clustermaster-af054",
    storageBucket: "clustermaster-af054.firebasestorage.app",
    messagingSenderId: "272995448697",
    appId: "1:272995448697:web:0aa1ddfdd2d2c8589261a8"
};

// Initialize Firebase
const firebaseApp = initializeApp(firebaseConfig);
export const auth = getAuth(firebaseApp);
export const db = getFirestore(firebaseApp);
export default firebaseApp;