import { useCallback, useEffect, useRef, useState } from "react";
import {
    createConversation,
    sendMessageWithStream,
    loadConversations,
} from "../../../services/api";

const STREAM_MODE = "word";
const NL_TOKEN = "[[NL]]";
const MIN_CHUNK = 24;

export default function useChatStream({
    conversationId,
    setConversationId,
    setMessages,
    setLoading,
    setConversations,
}) {
    const [streamedBotMessage, setStreamedBotMessage] = useState("");

    const esRef = useRef(null);
    const shownRef = useRef("");
    const queueRef = useRef("");
    const doneRef = useRef(false);
    const lastRenderedRef = useRef("");
    const rafIdRef = useRef(0);

    const stopRaf = useCallback(() => {
        if (!rafIdRef.current) return;
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = 0;
    }, []);

    const resetStreamState = useCallback(() => {
        setStreamedBotMessage("");
        shownRef.current = "";
        queueRef.current = "";
        doneRef.current = false;
        lastRenderedRef.current = "";
        stopRaf();
    }, [stopRaf]);

    const finalizeStream = useCallback(() => {
        const finalText = shownRef.current;

        setLoading(false);
        setMessages((prev) => [...prev, { text: finalText, from: "bot" }]);

        setStreamedBotMessage("");
        shownRef.current = "";
        queueRef.current = "";
        doneRef.current = false;
        lastRenderedRef.current = "";

        loadConversations(setConversations);
    }, [setConversations, setLoading, setMessages]);

    const pumpOneUnit = useCallback(() => {
        if (!queueRef.current) return false;

        if (queueRef.current.startsWith(NL_TOKEN)) {
            queueRef.current = queueRef.current.slice(NL_TOKEN.length);
            shownRef.current += "\n";
            return true;
        }

        if (STREAM_MODE === "letter") {
            const ch = queueRef.current[0];
            queueRef.current = queueRef.current.slice(1);
            shownRef.current += ch;
            return true;
        }

        const nlIdx = queueRef.current.indexOf(NL_TOKEN);
        const spIdx = queueRef.current.indexOf(" ");
        const punctMatch = queueRef.current.match(/[.,:;!?)]/);
        const punctIdx = punctMatch ? punctMatch.index : -1;

        const candidates = [
            nlIdx,
            spIdx !== -1 ? spIdx + 1 : -1,
            punctIdx !== -1 ? punctIdx + 1 : -1,
        ]
            .filter((x) => x !== -1)
            .sort((a, b) => a - b);

        const cut = candidates.length ? candidates[0] : -1;

        if (cut === -1) {
            const emitLen = Math.min(MIN_CHUNK, queueRef.current.length);
            const piece = queueRef.current.slice(0, emitLen);
            queueRef.current = queueRef.current.slice(emitLen);
            shownRef.current += piece;
            return true;
        }

        const piece = queueRef.current.slice(0, cut);
        queueRef.current = queueRef.current.slice(cut);
        shownRef.current += piece;
        return true;
    }, []);

    const getUnitsPerFrame = useCallback(() => {
        const qlen = queueRef.current.length;

        if (qlen > 3000) return 8;
        if (qlen > 1500) return 6;
        if (qlen > 700) return 5;
        if (qlen > 250) return 4;
        if (qlen > 80) return 3;

        return 2;
    }, []);

    const ensureRaf = useCallback(() => {
        if (rafIdRef.current) return;

        const frame = () => {
            let pumped = false;
            const units = getUnitsPerFrame();
            const start = performance.now();

            for (let i = 0; i < units; i++) {
                if (!queueRef.current) break;

                pumped = pumpOneUnit() || pumped;

                if (performance.now() - start > 10) break;
            }

            if (pumped && shownRef.current !== lastRenderedRef.current) {
                lastRenderedRef.current = shownRef.current;
                setStreamedBotMessage(shownRef.current);
            }

            if (!queueRef.current && doneRef.current) {
                stopRaf();
                finalizeStream();
                return;
            }

            if (queueRef.current || !doneRef.current) {
                rafIdRef.current = requestAnimationFrame(frame);
            } else {
                stopRaf();
            }
        };

        rafIdRef.current = requestAnimationFrame(frame);
    }, [finalizeStream, getUnitsPerFrame, pumpOneUnit, stopRaf]);

    const ensureConversation = useCallback(
        async (userPrompt) => {
            if (conversationId) return conversationId;

            const resp = await createConversation(
                userPrompt.slice(0, 50) || "New Conversation"
            );

            if (!resp?.id) {
                throw new Error("Conversation creation failed.");
            }

            setConversationId(resp.id);
            await loadConversations(setConversations);

            return resp.id;
        },
        [conversationId, setConversationId, setConversations]
    );

    const handleStreamChunk = useCallback(
        (chunk) => {
            if (chunk == null) return;
            queueRef.current += String(chunk);
            ensureRaf();
        },
        [ensureRaf]
    );

    const handleStreamComplete = useCallback(() => {
        doneRef.current = true;
        esRef.current?.close?.();
        ensureRaf();
    }, [ensureRaf]);

    const handleStreamError = useCallback(
        (err) => {
            console.error(err);
            setLoading(false);
            resetStreamState();
            alert("Error streaming response.");
        },
        [resetStreamState, setLoading]
    );

    const startStream = useCallback(
        async (userPrompt) => {
            if (!userPrompt?.trim()) return;

            esRef.current?.close?.();
            resetStreamState();

            setMessages((prev) => [...prev, { text: userPrompt, from: "user" }]);
            setLoading(true);

            try {
                const currentConversationId = await ensureConversation(userPrompt);

                const es = sendMessageWithStream(
                    userPrompt,
                    currentConversationId,
                    handleStreamChunk,
                    handleStreamComplete,
                    handleStreamError
                );

                esRef.current = es;
            } catch (err) {
                console.error(err);
                setLoading(false);
                resetStreamState();
                alert("Error sending message.");
            }
        },
        [
            ensureConversation,
            handleStreamChunk,
            handleStreamComplete,
            handleStreamError,
            resetStreamState,
            setLoading,
            setMessages,
        ]
    );

    const stopStream = useCallback(() => {
        esRef.current?.close?.();
        resetStreamState();
        setLoading(false);
    }, [resetStreamState, setLoading]);

    useEffect(() => {
        return () => {
            esRef.current?.close?.();
            stopRaf();
        };
    }, [stopRaf]);

    return {
        streamedBotMessage,
        startStream,
        stopStream,
        resetStreamState,
    };
}