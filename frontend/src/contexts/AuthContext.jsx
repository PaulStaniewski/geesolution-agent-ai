import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
} from "react";
import axios from "axios";

import {
    getAccessToken,
    getRefreshToken,
    setTokens,
    clearTokens,
} from "../services/authStorage";

const AuthContext = createContext();

const DJANGO_API_V1 = "/api/v1";
const USER_ID_KEY = "agentai_user_id";

/**
 * Prevent duplicate bootstrap calls in React StrictMode
 */
let authBootstrapPromise = null;

const fetchCurrentUserRequest = async (token) => {
    const res = await axios.get(`${DJANGO_API_V1}/me/`, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });

    return res.data;
};

const refreshAccessTokenRequest = async () => {
    const refresh = getRefreshToken();

    if (!refresh) {
        throw new Error("No refresh token available");
    }

    const res = await axios.post(`${DJANGO_API_V1}/token/refresh/`, {
        refresh,
    });

    const newAccess = res.data?.access;

    if (!newAccess) {
        throw new Error("No access token in refresh response");
    }

    setTokens({
        access: newAccess,
        refresh,
    });

    return newAccess;
};

/**
 * Bootstrap existing session
 */
const bootstrapAuthSession = async () => {
    const token = getAccessToken();
    const refresh = getRefreshToken();

    if (!token) {
        if (!refresh) {
            return {
                user: null,
                accessToken: null,
                clear: true,
            };
        }

        try {
            const newAccess = await refreshAccessTokenRequest();
            const currentUser = await fetchCurrentUserRequest(newAccess);

            return {
                user: currentUser,
                accessToken: newAccess,
                clear: false,
            };
        } catch {
            return {
                user: null,
                accessToken: null,
                clear: true,
            };
        }
    }

    try {
        const currentUser = await fetchCurrentUserRequest(token);

        return {
            user: currentUser,
            accessToken: token,
            clear: false,
        };
    } catch (err) {
        const status = err?.response?.status;

        if (status !== 401) {
            return {
                user: null,
                accessToken: null,
                clear: true,
            };
        }

        try {
            const newAccess = await refreshAccessTokenRequest();
            const currentUser = await fetchCurrentUserRequest(newAccess);

            return {
                user: currentUser,
                accessToken: newAccess,
                clear: false,
            };
        } catch {
            return {
                user: null,
                accessToken: null,
                clear: true,
            };
        }
    }
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [accessToken, setAccessToken] = useState(() =>
        getAccessToken()
    );
    const [error, setError] = useState("");

    const [isInitializing, setIsInitializing] = useState(true);
    const [isLoggingIn, setIsLoggingIn] = useState(false);
    const [isRegistering, setIsRegistering] = useState(false);

    const isAuthenticated = !!user;

    /**
     * Clear error helper
     */
    const clearError = useCallback(() => {
        setError("");
    }, []);

    /**
     * Clear full auth state
     */
    const clearAuthData = useCallback(() => {
        clearTokens();
        localStorage.removeItem(USER_ID_KEY);

        setAccessToken(null);
        setUser(null);
        setError("");
    }, []);

    const fetchCurrentUser = useCallback(async (token) => {
        return fetchCurrentUserRequest(token);
    }, []);

    /**
     * Initialize session
     */
    useEffect(() => {
        let isMounted = true;

        const initializeAuth = async () => {
            try {
                if (!authBootstrapPromise) {
                    authBootstrapPromise =
                        bootstrapAuthSession().finally(() => {
                            authBootstrapPromise = null;
                        });
                }

                const result = await authBootstrapPromise;

                if (!isMounted) return;

                if (
                    result.clear ||
                    !result.user ||
                    !result.accessToken
                ) {
                    clearAuthData();
                    return;
                }

                setUser(result.user);
                setAccessToken(result.accessToken);

                localStorage.setItem(
                    USER_ID_KEY,
                    String(result.user.id)
                );
            } catch {
                if (!isMounted) return;
                clearAuthData();
            } finally {
                if (isMounted) {
                    setIsInitializing(false);
                }
            }
        };

        initializeAuth();

        return () => {
            isMounted = false;
        };
    }, [clearAuthData]);

    /**
     * Global auth expired handler
     */
    useEffect(() => {
        const handleAuthExpired = () => {
            clearAuthData();
            setIsInitializing(false);
        };

        window.addEventListener(
            "auth:expired",
            handleAuthExpired
        );

        return () => {
            window.removeEventListener(
                "auth:expired",
                handleAuthExpired
            );
        };
    }, [clearAuthData]);

    /**
     * LOGIN
     */
    const login = async (email, password) => {
        setIsLoggingIn(true);
        setError("");

        try {
            const tokenRes = await axios.post(
                `${DJANGO_API_V1}/token/`,
                {
                    email: email.trim().toLowerCase(),
                    password,
                }
            );

            const { access, refresh } = tokenRes.data;

            setTokens({ access, refresh });
            setAccessToken(access);

            const currentUser =
                await fetchCurrentUser(access);

            setUser(currentUser);

            localStorage.setItem(
                USER_ID_KEY,
                String(currentUser.id)
            );
        } catch (err) {
            clearAuthData();

            if (
                err.response?.status === 400 ||
                err.response?.status === 401
            ) {
                setError("Invalid email or password.");
            } else if (!err.response) {
                setError(
                    "Unable to connect to the server."
                );
            } else {
                setError(
                    "Login failed. Please try again."
                );
            }
        } finally {
            setIsLoggingIn(false);
        }
    };

    /**
     * REGISTER
     */
    const register = async ({ email, password }) => {
        setIsRegistering(true);
        setError("");

        try {
            await axios.post(
                `${DJANGO_API_V1}/register/`,
                {
                    email: email.trim().toLowerCase(),
                    password,
                }
            );

            /**
             * Auto-login after registration
             */
            await login(email, password);
        } catch (err) {
            if (!err.response) {
                setError(
                    "Unable to connect to the server."
                );
            } else {
                const backendMessage =
                    err.response?.data?.message ||
                    "Registration failed. Please try again.";

                setError(
                    Array.isArray(backendMessage)
                        ? backendMessage[0]
                        : backendMessage
                );
            }
        } finally {
            setIsRegistering(false);
        }
    };

    /**
     * LOGOUT
     */
    const logout = async () => {
        const refresh = getRefreshToken();

        try {
            if (refresh && accessToken) {
                await axios.post(
                    `${DJANGO_API_V1}/logout/`,
                    { refresh },
                    {
                        headers: {
                            Authorization: `Bearer ${accessToken}`,
                        },
                    }
                );
            }
        } catch (err) {
            console.warn("Logout error:", err);
        } finally {
            clearAuthData();
        }
    };

    const value = useMemo(
        () => ({
            user,
            accessToken,
            error,

            isAuthenticated,
            isInitializing,
            isLoggingIn,
            isRegistering,

            isLoading:
                isInitializing ||
                isLoggingIn ||
                isRegistering,

            login,
            register,
            logout,

            clearAuthData,
            clearError,
        }),
        [
            user,
            accessToken,
            error,
            isAuthenticated,
            isInitializing,
            isLoggingIn,
            isRegistering,
            clearAuthData,
            clearError,
        ]
    );

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);