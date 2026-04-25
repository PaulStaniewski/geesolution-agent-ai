// src/services/api.js
import api from "../apiClient";
import { getAccessToken } from "./authStorage";

export const STREAM_URL =
    import.meta.env.VITE_STREAM_URL || "/chat-stream/";

export const BASE_FASTAPI =
    import.meta.env?.VITE_FASTAPI_URL?.replace(/\/$/, "") || "http://localhost:8001";

export const API_BASE = BASE_FASTAPI; // convenience alias

/**
 * Streaming messages (SSE)
 * Query params: message, conversation_id, token
 * - token goes in the URL because native EventSource doesn't support headers
 * - This function manages auto-reconnect on token refresh (via a custom event)
 */
export const sendMessageWithStream = (
    message,
    conversationId,
    onStream,   // (chunk: string) => void
    onComplete, // () => void
    onError,    // (err: any) => void
    onTrace     // (payload: { type: "trace", hits: [] }) => void
) => {
    const access = getAccessToken() || "";

    if (!conversationId) {
        onError?.(new Error("Brak conversationId"));
        return { close() { } };
    }

    const qs = new URLSearchParams({
        message,
        conversation_id: String(conversationId),
    });

    if (access) {
        qs.append("token", access);
    }

    let es = null;
    let closed = false;

    const safeClose = () => {
        if (closed) return;
        closed = true;

        try {
            es?.close();
        } catch { }

        window.removeEventListener("token:refreshed", onTokenRefreshed);
    };

    const handleMessage = (event) => {
        if (event.data === "[DONE]") {
            try {
                onComplete?.();
            } finally {
                safeClose();
            }
            return;
        }

        if (event.data == null) return;

        const raw = String(event.data);

        // 1) Try pure JSON first (trace / delta / etc.)
        try {
            const parsed = JSON.parse(raw);

            if (parsed && parsed.type === "trace") {
                if (Array.isArray(parsed.hits)) {
                    onTrace?.(parsed);
                }
                return;
            }

            if (parsed?.type === "delta" && typeof parsed.text === "string") {
                onStream?.(parsed.text.replace(/\[\[NL\]\]/g, "\n"));
                return;
            }

            if (typeof parsed === "string") {
                onStream?.(parsed.replace(/\[\[NL\]\]/g, "\n"));
                return;
            }
        } catch {
            // not JSON, continue
        }

        // 2) Mixed payload: "text ... {json}"
        const braceIdx = raw.lastIndexOf("{");

        if (braceIdx > -1) {
            const prefix = raw.slice(0, braceIdx);
            const maybeJson = raw.slice(braceIdx).trim();

            try {
                const parsedTail = JSON.parse(maybeJson);

                if (parsedTail && parsedTail.type === "trace") {
                    if (prefix.trim()) {
                        onStream?.(prefix.replace(/\[\[NL\]\]/g, "\n"));
                    }

                    if (Array.isArray(parsedTail.hits)) {
                        onTrace?.(parsedTail);
                    }

                    return;
                }
            } catch {
                // tail was not valid JSON, continue as plain text
            }
        }

        // 3) Fallback: plain text
        onStream?.(raw.replace(/\[\[NL\]\]/g, "\n"));
    };

    const handleError = (err) => {
        try {
            onError?.(err);
        } finally {
            safeClose();
        }
    };

    const start = () => {
        es = new EventSource(`${STREAM_URL}?${qs.toString()}`);
        es.onmessage = handleMessage;
        es.onerror = handleError;
    };

    // Auto-restart SSE after access token refresh (emitted in apiClient.js)
    const onTokenRefreshed = (e) => {
        if (closed) return;

        try {
            es?.close();
        } catch { }

        const newAccess = e?.detail || getAccessToken() || "";

        if (newAccess) {
            qs.set("token", newAccess);
        }

        start();
    };

    window.addEventListener("token:refreshed", onTokenRefreshed);

    start();

    return { close: safeClose };
};

// Saving messages
export const saveMessageToDatabase = async (
    message,
    conversationId,
    botReply = null
) => {
    try {
        await api.post("/chat/", {
            message,
            conversation_id: conversationId,
            bot_reply: botReply !== null ? botReply : undefined,
        });
    } catch (err) {
        console.error("Error saving message:", err.response?.data || err.message);
        throw err;
    }
};

// Uploading documents
export const uploadDocument = async (files, title) => {
    const list = Array.from(files || []);

    if (!list.length) {
        throw new Error("No files selected");
    }

    const fd = new FormData();
    list.forEach((file) => fd.append("files", file));

    if (title) {
        fd.append("title", title);
    }

    // POST (do not set Content-Type manually)
    const postRes = await api.post("/upload/", fd);

    if (postRes?.data?.errors?.length) {
        console.warn("Upload errors:", postRes.data.errors);
    }

    // GET documents list; normalize to array regardless of payload shape
    const getRes = await api.get("/documents/");
    const data = getRes.data;

    const docs = Array.isArray(data)
        ? data
        : Array.isArray(data?.results)
            ? data.results
            : Array.isArray(data?.documents)
                ? data.documents
                : [];

    return docs;
};

// Creating a new conversation
export const createConversation = async (name = "") => {
    try {
        const res = await api.post("/conversations/", {
            name,
            updated_at: new Date().toISOString(),
        });

        if (res.data && res.data.id) {
            return res.data;
        }

        console.error("Conversation creation failed: No ID in response.");
        return null;
    } catch (err) {
        console.error("Error creating conversation:", err.response?.data || err.message);
        return null;
    }
};

// Fetching messages for a conversation
export const fetchMessagesForConversation = async (id) => {
    try {
        const res = await api.get(`/messages/?conversation_id=${id}`);

        return res.data.flatMap((msg) => {
            const items = [];

            if (msg.user_message) {
                items.push({ text: msg.user_message, from: "user" });
            }

            if (msg.bot_reply) {
                items.push({ text: msg.bot_reply, from: "bot" });
            }

            return items;
        });
    } catch (err) {
        console.error("Error fetching messages:", err);
        return [];
    }
};

// Load conversations and update state setter
export const loadConversations = async (setConversations) => {
    try {
        const conversations = await fetchConversations();
        setConversations(conversations);
    } catch (err) {
        console.error("Error loading conversations:", err);
    }
};

// Fetching list of conversations
export const fetchConversations = async () => {
    try {
        const res = await api.get("/conversations/");
        return res.data.sort(
            (a, b) =>
                new Date(b.updated_at || b.started_at) -
                new Date(a.updated_at || a.started_at)
        );
    } catch (err) {
        console.error("Error fetching conversations:", err);
        return [];
    }
};

// Updating conversation name
export const updateConversationName = async (id, newName) => {
    try {
        await api.patch(`/conversations/${id}/`, { name: newName });
    } catch (err) {
        console.error("Error updating conversation name:", err);
        throw err;
    }
};

// Fetching documents
export const fetchDocuments = async () => {
    try {
        const res = await api.get("/documents/");
        return res.data;
    } catch (err) {
        console.error("Error fetching documents:", err);
        return [];
    }
};

// Deleting documents (single or all)
export const deleteDocuments = async (docId = null) => {
    try {
        if (docId) {
            await api.delete(`/documents/${docId}/`);
        } else {
            await api.delete("/documents/delete-all/");
        }
    } catch (err) {
        console.error("Error deleting document(s):", err);
        throw err;
    }
};

// Deleting a conversation
export const deleteConversation = async (convId) => {
    try {
        await api.delete(`/conversations/${convId}/`);
    } catch (err) {
        console.error("Error deleting conversation:", err);
    }
};

export const requestPasswordReset = async (email) => {
    const res = await api.post("/password-reset/", { email });
    return res.data;
};

export const confirmPasswordReset = async ({ uid, token, password }) => {
    const res = await api.post("/password-reset-confirm/", {
        uid,
        token,
        password,
    });

    return res.data;
};