import "./MobileSidebarControls.css";

const MobileSidebarControls = ({
    mobilePanel,
    setMobilePanel,
    onClose,
}) => {
    const handleSelect = (panel) => {
        setMobilePanel(panel);
        onClose();
    };

    return (
        <>
            <div className="mobile-overlay" onClick={onClose} />

            <div
                className="mobile-sidebar-controls"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="mobile-sidebar-controls__inner">
                    <button
                        type="button"
                        className={`mobile-sidebar-controls__button ${mobilePanel === "conversations"
                                ? "mobile-sidebar-controls__button--active"
                                : ""
                            }`}
                        onClick={() => handleSelect("conversations")}
                    >
                        Conversations
                    </button>

                    <button
                        type="button"
                        className={`mobile-sidebar-controls__button ${mobilePanel === "chat"
                                ? "mobile-sidebar-controls__button--active"
                                : ""
                            }`}
                        onClick={() => handleSelect("chat")}
                    >
                        Chat
                    </button>

                    <button
                        type="button"
                        className={`mobile-sidebar-controls__button ${mobilePanel === "documents"
                                ? "mobile-sidebar-controls__button--active"
                                : ""
                            }`}
                        onClick={() => handleSelect("documents")}
                    >
                        Documents
                    </button>
                </div>
            </div>
        </>
    );
};

export default MobileSidebarControls;