import { defineStore } from "pinia"
import { signInWithEmailAndPassword, signOut } from "firebase/auth"
import { auth } from "@/firebase"

export const useAuthStore = defineStore("auth", {
    state: () => ({
        user: null as null | { uid: string; email: string },
    }),
    actions: {
        async login(email: string, pass: string) {
            const cred = await signInWithEmailAndPassword(auth, email, pass)
            this.user = { uid: cred.user.uid, email: cred.user.email! }
        },
        async logout() {
            await signOut(auth)
            this.user = null
        }
    }
})
