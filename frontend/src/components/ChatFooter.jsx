import "./ChatFooter.css";

const ChatFooter = () => {
    return (
        <footer className="chatbot-footer">
            © {new Date().getFullYear()} GeeBOT by Gee. All rights reserved.
        </footer>
    );
};

export default ChatFooter;