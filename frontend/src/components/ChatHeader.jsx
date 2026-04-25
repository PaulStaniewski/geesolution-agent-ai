import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import Modal from "./Modal";
import "./ChatHeader.css";

const ChatHeader = ({ setSidebarsOpen, setMobileMenuOpen }) => {
    const { logout } = useAuth();
    const [showLogoutModal, setShowLogoutModal] = useState(false);

    const handleConfirmLogout = () => {
        logout();
    };

    const handleSettingsClick = () => {
        if (setMobileMenuOpen) {
            setMobileMenuOpen((prev) => !prev);
            return;
        }

        if (setSidebarsOpen) {
            setSidebarsOpen((prev) => !prev);
        }
    };

    return (
        <>
            <div className="chat-header">
                <div className="flex items-center gap-2">
                    <h1 className="chat-header__title">Haystack Agent</h1>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        type="button"
                        onClick={handleSettingsClick}
                        title="Settings"
                        className="chat-header__button"
                    >
                        Settings
                    </button>

                    <button
                        type="button"
                        onClick={() => setShowLogoutModal(true)}
                        title="Log out"
                        className="chat-header__button chat-header__button--logout"
                    >
                        Log out
                    </button>
                </div>
            </div>

            <Modal
                title="Log out"
                show={showLogoutModal}
                onClose={() => setShowLogoutModal(false)}
                onConfirm={handleConfirmLogout}
                confirmText="Log out"
                cancelText="Cancel"
            >
                <p className="text-sm text-slate-300">
                    Are you sure you want to log out?
                </p>
            </Modal>
        </>
    );
};

export default ChatHeader;