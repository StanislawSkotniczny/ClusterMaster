import { defineStore } from "pinia"
import { signInWithEmailAndPassword, signOut, onAuthStateChanged } from "firebase/auth"
import { auth } from "@/firebase"
import { useAwsStore } from "./aws"

export const useAuthStore = defineStore("auth", {
    state: () => ({
        user: null as null | { uid: string; email: string },
        authReady: false,
    }),
    getters: {
        isLoggedIn: (state) => !!state.user,
    },
    actions: {
        async login(email: string, pass: string) {
            const cred = await signInWithEmailAndPassword(auth, email, pass)
            this.user = { uid: cred.user.uid, email: cred.user.email! }
        },
        async logout() {
            await signOut(auth)
            this.user = null
            
            // Clear AWS credentials on logout
            const awsStore = useAwsStore()
            awsStore.clearCredentials()
        },
        init() {
            return new Promise((resolve) => {
                onAuthStateChanged(auth, (user) => {
                    if (user) {
                        this.user = { uid: user.uid, email: user.email! }
                    } else {
                        this.user = null
                    }
                    this.authReady = true
                    resolve(true)
                })
            })
        }
    }
})
