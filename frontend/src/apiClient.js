import axios from "axios";
import {
    getAccessToken,
    getRefreshToken,
    setTokens,
    clearTokens,
} from "./services/authStorage";

const DJANGO_API_V1 =
    import.meta.env.VITE_DJANGO_API_URL || "/api/v1";

console.log("DJANGO_API_V1 =", DJANGO_API_V1);

const api = axios.create({
    baseURL: DJANGO_API_V1,
});

api.interceptors.request.use(
    (config) => {
        const token = getAccessToken();

        if (token) {
            config.headers = config.headers || {};
            config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
    },
    (error) => Promise.reject(error)
);

let refreshPromise = null;

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        if (!error.response) {
            return Promise.reject(error);
        }

        const originalRequest = error.config;
        const status = error.response?.status;
        const data = error.response?.data;

        const isRefreshEndpoint =
            originalRequest?.url?.endsWith("/token/refresh/");

        const refreshToken = getRefreshToken();

        if (!refreshToken) {
            clearTokens();
            window.dispatchEvent(new CustomEvent("auth:expired"));
            return Promise.reject(error);
        }

        const detail = data?.detail?.toString().toLowerCase() || "";

        const looksLikeExpired =
            status === 401 &&
            !originalRequest?._retry &&
            !isRefreshEndpoint &&
            !!refreshToken &&
            (
                data?.code === "token_not_valid" ||
                detail.includes("not valid") ||
                detail.includes("token is invalid") ||
                detail.includes("token is expired") ||
                detail.includes("given token")
            );

        if (!looksLikeExpired) {
            return Promise.reject(error);
        }

        originalRequest._retry = true;

        if (!refreshPromise) {
            refreshPromise = axios
                .post(`${DJANGO_API_V1}/token/refresh/`, {
                    refresh: refreshToken,
                })
                .then((res) => {
                    const newAccess = res.data?.access;

                    if (!newAccess) {
                        throw new Error("No access token in refresh response");
                    }

                    setTokens({
                        access: newAccess,
                        refresh: refreshToken,
                    });

                    window.dispatchEvent(
                        new CustomEvent("token:refreshed", { detail: newAccess })
                    );

                    return newAccess;
                })
                .catch((e) => {
                    clearTokens();
                    window.dispatchEvent(new CustomEvent("auth:expired"));
                    throw e;
                })
                .finally(() => {
                    refreshPromise = null;
                });
        }

        try {
            const newAccess = await refreshPromise;

            originalRequest.headers = originalRequest.headers || {};
            originalRequest.headers.Authorization = `Bearer ${newAccess}`;

            return api(originalRequest);
        } catch (e) {
            return Promise.reject(e);
        }
    }
);

export default api;