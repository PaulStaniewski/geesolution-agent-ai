import { useCallback, useEffect, useRef, useState } from "react";

const useSpeechRecognition = ({ language = "pl-PL", onTranscript, onFinalTranscript }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [speechSupported, setSpeechSupported] = useState(true);

    const recognitionRef = useRef(null);
    const finalBufferRef = useRef("");
    const isProcessingFinalRef = useRef(false);

    const stopRecording = useCallback(() => {
        if (recognitionRef.current) {
            recognitionRef.current.stop();
        }
        setIsRecording(false);
    }, []);

    const startRecording = useCallback(() => {
        if (!recognitionRef.current || isProcessingFinalRef.current) return;

        finalBufferRef.current = "";
        recognitionRef.current.start();
        setIsRecording(true);
    }, []);

    useEffect(() => {
        const SpeechRecognition =
            window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            console.warn("This browser does not support SpeechRecognition.");
            setSpeechSupported(false);
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = language;
        recognition.continuous = true;
        recognition.interimResults = true;

        recognition.onresult = async (event) => {
            let interimText = "";
            let finalText = "";

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const result = event.results[i];
                const transcript = result[0]?.transcript ?? "";

                if (result.isFinal) {
                    finalText += `${transcript} `;
                } else {
                    interimText += `${transcript} `;
                }
            }

            const mergedText = `${finalBufferRef.current}${finalText}${interimText}`.trim();

            if (onTranscript) {
                onTranscript(mergedText);
            }

            if (finalText && onFinalTranscript && !isProcessingFinalRef.current) {
                const finalMessage = `${finalBufferRef.current}${finalText}`.trim();

                finalBufferRef.current = finalMessage;
                isProcessingFinalRef.current = true;

                try {
                    await onFinalTranscript(finalMessage);
                    finalBufferRef.current = "";
                    stopRecording();
                } catch (error) {
                    console.error("Speech final transcript handling failed:", error);
                } finally {
                    isProcessingFinalRef.current = false;
                }
            }
        };

        recognition.onerror = (event) => {
            console.error("Speech recognition error:", event);
            setIsRecording(false);
            isProcessingFinalRef.current = false;
        };

        recognition.onend = () => {
            setIsRecording(false);
        };

        recognitionRef.current = recognition;

        return () => {
            recognition.onresult = null;
            recognition.onerror = null;
            recognition.onend = null;
            recognition.stop();
            recognitionRef.current = null;
        };
    }, [language, onTranscript, onFinalTranscript, stopRecording]);

    return {
        isRecording,
        speechSupported,
        startRecording,
        stopRecording,
    };
};

export default useSpeechRecognition;