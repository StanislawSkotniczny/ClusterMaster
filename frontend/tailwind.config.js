/** @type {import('tailwindcss').Config} */
export default {
    darkMode: 'class', // Enable dark mode with class strategy
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: "#4F46E5",
                secondary: "#6366F1",
                success: "#10B981",
                danger: "#EF4444",
                warning: "#F59E0B",
                info: "#3B82F6",
            }
        },
    },
    plugins: [],
}