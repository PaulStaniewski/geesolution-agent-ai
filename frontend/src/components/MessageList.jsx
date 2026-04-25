import React, { useEffect, useRef } from "react";
import StreamedMarkdown from "./StreamedMarkdown";
import SourcesList from "./SourcesList";
import "./MessageList.css";

/* =========================================================
   Text transforms before markdown render
   ========================================================= */

const colorizeCheckmarks = (text = "") =>
  text
    .replace(/✔/g, '<span class="correct">✔</span>')
    .replace(/(?:✗|❌)/g, '<span class="incorrect">✗</span>');

const fixLeadingDotToOrderedList = (text = "") =>
  text.replace(/^\.\s+/gm, "1. ");

const transformForStream = (text = "") =>
  fixLeadingDotToOrderedList(text);

const transformForFinal = (text = "") =>
  colorizeCheckmarks(fixLeadingDotToOrderedList(text));

const MessageItem = React.memo(({ msg }) => {
  const isUser = msg.from === "user";

  return (
    <div className={`message-row ${isUser ? "message-row--user" : "message-row--bot"}`}>
      <div
        className={`message-bubble markdown-container ${isUser ? "message-user" : "message-bot"
          }`}
      >
        <StreamedMarkdown
          text={msg.text || ""}
          isStreaming={false}
          highlight
          transformText={transformForFinal}
        />

        {!isUser && msg?.trace?.hits?.length ? (
          <div className="message-sources">
            <SourcesList hits={msg.trace.hits} />
          </div>
        ) : null}
      </div>
    </div>
  );
});

MessageItem.displayName = "MessageItem";

const FinalMessages = React.memo(({ messages }) => {
  return (
    <>
      {messages.map((msg, idx) => (
        <MessageItem key={msg.id ?? idx} msg={msg} />
      ))}
    </>
  );
});

FinalMessages.displayName = "FinalMessages";

const MessageList = React.memo(
  ({ messages, messagesEndRef, streamedBotMessage, loading }) => {
    const hasMountedRef = useRef(false);
    const prevMessagesLenRef = useRef(messages.length);

    useEffect(() => {
      if (!messagesEndRef?.current) return;

      if (!hasMountedRef.current) {
        hasMountedRef.current = true;
        prevMessagesLenRef.current = messages.length;
        return;
      }

      const didAddMessage = messages.length > prevMessagesLenRef.current;
      prevMessagesLenRef.current = messages.length;

      if (!didAddMessage) return;

      messagesEndRef.current.scrollIntoView({
        behavior: "smooth",
        block: "end",
      });
    }, [messages.length, messagesEndRef]);

    return (
      <div className="message-list">
        <FinalMessages messages={messages} />

        {streamedBotMessage && (
          <div className="message-row message-row--bot">
            <div className="message-bubble message-bot markdown-container streaming">
              <StreamedMarkdown
                text={streamedBotMessage}
                isStreaming
                highlight
                transformText={transformForStream}
              />
            </div>
          </div>
        )}

        {loading && !streamedBotMessage && (
          <div className="message-row message-row--bot">
            <div className="typing">
              <div className="chat-dot"></div>
              <div className="chat-dot"></div>
              <div className="chat-dot"></div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    );
  }
);

MessageList.displayName = "MessageList";

export default MessageList;