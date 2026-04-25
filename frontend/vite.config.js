import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const inDocker = process.env.IN_DOCKER === "1";
const FASTAPI_TARGET = inDocker ? "http://fastapi:8001" : "http://localhost:8001";
const DJANGO_TARGET = inDocker ? "http://django:8000" : "http://localhost:8000";

export default defineConfig({
    plugins: [
        react(),
        tailwindcss(),
    ],
    server: {
        host: true,
        port: 3000,
        strictPort: true,
        open: !inDocker,
        proxy: {
            "/chat-stream/": {
                target: FASTAPI_TARGET,
                changeOrigin: true,
                ws: false,
                secure: false,
            },
            "/api": {
                target: DJANGO_TARGET,
                changeOrigin: true,
                secure: false,
            },
        },
    },
});