import { defineStore } from "pinia"
import { signInWithEmailAndPassword, signOut, onAuthStateChanged } from "firebase/auth"
import { auth } from "@/firebase"

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
