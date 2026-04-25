import { useCallback, useEffect, useRef } from "react";
import useSpeechRecognition from "../features/chat/hooks/useSpeechRecognition";
import "./ChatInput.css";
import { SendIcon, MicIcon } from "../features/ui/icons";

const ChatInput = ({ input, setInput, handleSendStream, disabled = false }) => {
    const textareaRef = useRef(null);

    const sendMessage = useCallback(
        async (messageOverride) => {
            const textToSend = (messageOverride ?? input).trim();

            if (!textToSend || disabled) return;

            await handleSendStream(textToSend);
            setInput("");
        },
        [disabled, handleSendStream, input, setInput]
    );

    const { isRecording, speechSupported, startRecording, stopRecording } =
        useSpeechRecognition({
            language: "pl-PL",
            onTranscript: (text) => {
                setInput(text);
            },
            onFinalTranscript: async (finalText) => {
                await sendMessage(finalText);
            },
        });

    useEffect(() => {
        const textarea = textareaRef.current;
        if (!textarea) return;

        textarea.style.height = "0px";
        const nextHeight = Math.min(textarea.scrollHeight, 160);
        textarea.style.height = `${nextHeight}px`;
    }, [input]);

    const toggleRecording = () => {
        if (disabled || !speechSupported) return;

        if (isRecording) {
            stopRecording();
            return;
        }

        setInput("");
        startRecording();
    };

    const handleKeyDown = (event) => {
        if (event.key !== "Enter" || event.shiftKey) return;

        event.preventDefault();
        sendMessage();
    };

    const micTooltip = speechSupported
        ? isRecording
            ? "Recording..."
            : "Record message"
        : "Voice input is not supported in this browser (Firefox)";

    return (
        <div className="chat-input">
            <div className="chat-input__inner">
                <textarea
                    ref={textareaRef}
                    className="chat-input__field"
                    placeholder="Type a message..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={disabled}
                    rows={1}
                />

                {/* MICROPHONE — always visible */}
                <button
                    className={`chat-input__button chat-input__mic-button ${isRecording
                        ? "chat-input__mic-button--recording"
                        : ""
                        }`}
                    onClick={toggleRecording}
                    title={micTooltip}
                    type="button"
                    disabled={disabled || !speechSupported}
                >
                    <MicIcon size={19} />
                </button>

                <button
                    className="chat-input__button chat-input__send-button"
                    onClick={() => sendMessage()}
                    disabled={disabled || !input.trim()}
                    type="button"
                    title="Send message"
                >
                    <SendIcon size={19} />
                </button>
            </div>
        </div>
    );
};

export default ChatInput;