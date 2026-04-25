import { useCallback, useEffect, useRef, useState } from "react";
import "./ChatBot.css";

import SidebarConversations from "../../components/SidebarConversations";
import SidebarDocuments from "../../components/SidebarDocuments";
import MessageList from "../../components/MessageList";
import ChatInput from "../../components/ChatInput";
import ChatHeader from "../../components/ChatHeader";
import ChatFooter from "../../components/ChatFooter";
import MobileSidebarControls from "../../components/MobileSidebarControls";

import useChatStream from "./hooks/useChatStream";

const ChatBot = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // Desktop only
  const [sidebarsOpen, setSidebarsOpen] = useState(false);

  // Mobile only
  const [mobilePanel, setMobilePanel] = useState("chat");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 1024);

  const [conversationId, setConversationId] = useState(null);
  const [conversations, setConversations] = useState([]);

  const chatBodyRef = useRef(null);
  const hasMountedScrollRef = useRef(false);
  const prevMessagesLenRef = useRef(0);
  const streamRafRef = useRef(null);
  const messagesEndRef = useRef(null);

  const { streamedBotMessage, startStream } = useChatStream({
    conversationId,
    setConversationId,
    setMessages,
    setLoading,
    setConversations,
  });

  const handleSendStream = useCallback(
    async (messageOverride) => {
      const userPrompt = (messageOverride ?? input).trim();
      if (!userPrompt) return;

      setInput("");
      await startStream(userPrompt);
    },
    [input, startStream]
  );

  const handleMainClick = () => {
    if (!isMobile && sidebarsOpen) {
      setSidebarsOpen(false);
    }

    if (isMobile && mobileMenuOpen) {
      setMobileMenuOpen(false);
    }
  };

  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 1024;
      setIsMobile(mobile);

      if (!mobile) {
        setMobilePanel("chat");
        setMobileMenuOpen(false);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    const chatBody = chatBodyRef.current;
    if (!chatBody) return;

    if (!hasMountedScrollRef.current) {
      hasMountedScrollRef.current = true;
      prevMessagesLenRef.current = messages.length;
      return;
    }

    const didAddMessage = messages.length > prevMessagesLenRef.current;
    prevMessagesLenRef.current = messages.length;

    if (didAddMessage) {
      chatBody.scrollTo({
        top: chatBody.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages]);

  useEffect(() => {
    const chatBody = chatBodyRef.current;
    if (!chatBody || !streamedBotMessage) return;

    if (streamRafRef.current) {
      cancelAnimationFrame(streamRafRef.current);
    }

    streamRafRef.current = requestAnimationFrame(() => {
      chatBody.scrollTop = chatBody.scrollHeight;
    });

    return () => {
      if (streamRafRef.current) {
        cancelAnimationFrame(streamRafRef.current);
      }
    };
  }, [streamedBotMessage]);

  const desktopChatView = (
    <main className="chat-main" onClick={handleMainClick}>
      <div className="chatbot-card">
        <ChatHeader
          setSidebarsOpen={setSidebarsOpen}
          setMobileMenuOpen={undefined}
        />

        <div className="chat-body" ref={chatBodyRef}>
          <MessageList
            messages={messages}
            streamedBotMessage={streamedBotMessage}
            messagesEndRef={messagesEndRef}
            loading={loading}
          />
        </div>

        <ChatInput
          input={input}
          setInput={setInput}
          handleSendStream={handleSendStream}
        />
      </div>
    </main>
  );

  const mobileChatPanel = (
    <>
      <div className="chat-body" ref={chatBodyRef}>
        <MessageList
          messages={messages}
          streamedBotMessage={streamedBotMessage}
          messagesEndRef={messagesEndRef}
          loading={loading}
        />
      </div>

      <ChatInput
        input={input}
        setInput={setInput}
        handleSendStream={handleSendStream}
      />
    </>
  );

  const mobileConversationsPanel = (
    <div className="chatbot-mobile-panel chatbot-mobile-panel--conversations">
      <SidebarConversations
        sidebarsOpen={true}
        embedded={true}
        setMessages={setMessages}
        onConversationSelect={(id) => {
          setConversationId(id);
          setMobilePanel("chat");
          setMobileMenuOpen(false);
        }}
        setConversations={setConversations}
        conversations={conversations}
      />
    </div>
  );

  const mobileDocumentsPanel = (
    <div className="chatbot-mobile-panel chatbot-mobile-panel--documents">
      <SidebarDocuments
        sidebarsOpen={true}
        embedded={true}
      />
    </div>
  );

  const mobileView = (
    <main className="chat-main" onClick={handleMainClick}>
      <div className="chatbot-card chatbot-card--mobile">
        <ChatHeader
          setSidebarsOpen={undefined}
          setMobileMenuOpen={setMobileMenuOpen}
        />

        {mobilePanel === "conversations" && mobileConversationsPanel}
        {mobilePanel === "chat" && mobileChatPanel}
        {mobilePanel === "documents" && mobileDocumentsPanel}
      </div>
    </main>
  );

  return (
    <div className="chatbot-wrapper">
      {isMobile && mobileMenuOpen && (
        <MobileSidebarControls
          mobilePanel={mobilePanel}
          setMobilePanel={setMobilePanel}
          onClose={() => setMobileMenuOpen(false)}
        />
      )}

      <div className="chatbot-layout">
        {!isMobile ? (
          <>
            <aside className="chatbot-sidebar chatbot-sidebar--desktop">
              <SidebarConversations
                sidebarsOpen={sidebarsOpen}
                setMessages={setMessages}
                onConversationSelect={setConversationId}
                setConversations={setConversations}
                conversations={conversations}
              />
            </aside>

            {desktopChatView}

            <aside className="chatbot-sidebar chatbot-sidebar--desktop">
              <SidebarDocuments sidebarsOpen={sidebarsOpen} />
            </aside>
          </>
        ) : (
          mobileView
        )}
      </div>

      <ChatFooter />
    </div>
  );
};

export default ChatBot;