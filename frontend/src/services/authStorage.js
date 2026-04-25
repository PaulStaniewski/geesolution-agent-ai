const ACCESS_KEY = "agentai_access";
const REFRESH_KEY = "agentai_refresh";
const USER_ID_KEY = "agentai_user_id";
const REMEMBERED_EMAIL_KEY = "agentai_remembered_email";

export const getAccessToken = () =>
    localStorage.getItem(ACCESS_KEY) || null;

export const getRefreshToken = () =>
    localStorage.getItem(REFRESH_KEY) || null;

export const setTokens = ({ access, refresh }) => {
    if (access) {
        localStorage.setItem(ACCESS_KEY, access);
    }

    if (refresh) {
        localStorage.setItem(REFRESH_KEY, refresh);
    }
};

export const clearTokens = () => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_ID_KEY);
};

export const getRememberedEmail = () =>
    localStorage.getItem(REMEMBERED_EMAIL_KEY);

export const setRememberedEmail = (email) => {
    const normalized = email?.trim().toLowerCase();

    if (normalized) {
        localStorage.setItem(
            REMEMBERED_EMAIL_KEY,
            normalized
        );
    }
};

export const clearRememberedEmail = () => {
    localStorage.removeItem(
        REMEMBERED_EMAIL_KEY
    );
};