import { useEffect, useRef, useState } from "react";
import Modal from "../components/Modal";
import {
  createConversation,
  fetchMessagesForConversation,
  fetchConversations,
  deleteConversation,
  updateConversationName,
} from "../services/api";
import "./SidebarConversations.css";

/* =========================================================
   Helpers
   ========================================================= */

const getActivityDate = (conv) => conv.updated_at || conv.started_at || null;

const formatDate = (dateString) => {
  if (!dateString) return "—";

  const date = new Date(dateString);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString("pl-PL");
};

const getConversationLabel = (conv) => {
  const name = conv?.name || "";
  return name.trim() || "Untitled conversation";
};

const groupConversationsByDate = (conversations) => {
  const groups = {
    today: [],
    yesterday: [],
    last7Days: [],
    older: [],
  };

  const localNow = new Date();
  localNow.setHours(0, 0, 0, 0);

  [...conversations]
    .sort(
      (a, b) =>
        new Date(getActivityDate(b) || 0) - new Date(getActivityDate(a) || 0)
    )
    .forEach((conv) => {
      const updated = new Date(getActivityDate(conv));
      if (Number.isNaN(updated.getTime())) return;

      const localDate = new Date(updated);
      localDate.setHours(0, 0, 0, 0);

      const diffDays = Math.floor(
        (localNow - localDate) / (1000 * 60 * 60 * 24)
      );

      if (diffDays === 0) groups.today.push(conv);
      else if (diffDays === 1) groups.yesterday.push(conv);
      else if (diffDays < 7) groups.last7Days.push(conv);
      else groups.older.push(conv);
    });

  return groups;
};

const SidebarConversations = ({
  sidebarsOpen,
  embedded = false,
  setMessages,
  onConversationSelect,
  setConversations,
  conversations,
}) => {
  const [conversationId, setConversationId] = useState(null);
  const [activeMenu, setActiveMenu] = useState(null);
  const [menuDirection, setMenuDirection] = useState({});

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newConversationName, setNewConversationName] = useState("");

  const [showRenameModal, setShowRenameModal] = useState(false);
  const [renameValue, setRenameValue] = useState("");
  const [renameConvId, setRenameConvId] = useState(null);

  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteConvId, setDeleteConvId] = useState(null);

  const menuRef = useRef(null);
  const scrollRef = useRef(null);
  const didLoadRef = useRef(false);

  const refreshConversations = async () => {
    const updatedConversations = await fetchConversations();
    setConversations(updatedConversations);
  };

  useEffect(() => {
    if (didLoadRef.current) return;

    didLoadRef.current = true;
    refreshConversations();
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setActiveMenu(null);
      }
    };

    if (activeMenu !== null) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [activeMenu]);

  const { today, yesterday, last7Days, older } =
    groupConversationsByDate(conversations);

  const handleSelectConversation = async (id) => {
    setConversationId(id);

    if (onConversationSelect) {
      onConversationSelect(id);
    }

    const messages = await fetchMessagesForConversation(id);
    setMessages(messages);
  };

  const handleCreateConversation = async () => {
    if (!newConversationName.trim()) return;

    const newConv = await createConversation(newConversationName);

    if (newConv?.id) {
      setConversationId(newConv.id);

      if (onConversationSelect) {
        onConversationSelect(newConv.id);
      }

      setMessages([]);
      await refreshConversations();

      setShowCreateModal(false);
      setNewConversationName("");
    }
  };

  const handleRenameConversation = async () => {
    try {
      await updateConversationName(renameConvId, renameValue);
      await refreshConversations();
      setShowRenameModal(false);
    } catch (error) {
      alert("Error updating conversation name.");
    }
  };

  const handleDeleteConversation = async () => {
    try {
      await deleteConversation(deleteConvId);
      await refreshConversations();
      setShowDeleteModal(false);

      if (conversationId === deleteConvId) {
        setConversationId(null);

        if (onConversationSelect) {
          onConversationSelect(null);
        }

        setMessages([]);
      }
    } catch (error) {
      alert("Error deleting conversation.");
    }
  };

  const handleToggleMenu = (event, convId, isMenuOpen) => {
    event.stopPropagation();

    if (isMenuOpen) {
      setActiveMenu(null);
      return;
    }

    const scrollBox = scrollRef.current;
    const triggerRect = event.currentTarget.getBoundingClientRect();

    if (scrollBox) {
      const scrollRect = scrollBox.getBoundingClientRect();
      const estimatedMenuHeight = 120;

      const spaceBelow = scrollRect.bottom - triggerRect.bottom;
      const shouldOpenUp = spaceBelow < estimatedMenuHeight;

      setMenuDirection((prev) => ({
        ...prev,
        [convId]: shouldOpenUp ? "up" : "down",
      }));
    }

    setActiveMenu(convId);
  };

  const renderConversations = (list) =>
    list.map((conv) => {
      const label = getConversationLabel(conv);
      const isSelected = conv.id === conversationId;
      const isMenuOpen = activeMenu === conv.id;
      const shouldOpenUpwards = menuDirection[conv.id] === "up";

      return (
        <li
          key={conv.id}
          className={`conversation-item ${isSelected ? "conversation-item--selected" : ""
            } ${isMenuOpen ? "conversation-item--menu-open" : ""}`}
          onClick={() => handleSelectConversation(conv.id)}
        >
          <div className="conversation-item__content">
            <div title={label} className="conversation-item__title">
              {label.length > 20 ? `${label.slice(0, 18)}...` : label}
            </div>

            <div className="conversation-item__meta">
              <div className="conversation-item__meta-label">Last activity:</div>
              <div>{formatDate(getActivityDate(conv))}</div>
            </div>
          </div>

          <div
            className="conversation-item__actions"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              className="conversation-item__menu-trigger"
              onClick={(e) => handleToggleMenu(e, conv.id, isMenuOpen)}
              aria-label={`Open actions for ${label}`}
            >
              ⋯
            </button>

            {isMenuOpen && (
              <div
                className={`conversation-menu ${shouldOpenUpwards ? "conversation-menu--up" : ""
                  }`}
                ref={menuRef}
              >
                <button
                  type="button"
                  className="conversation-menu__button"
                  onClick={() => {
                    setRenameConvId(conv.id);
                    setRenameValue(conv.name || "");
                    setShowRenameModal(true);
                    setActiveMenu(null);
                  }}
                >
                  Rename
                </button>

                <div className="conversation-menu__divider"></div>

                <button
                  type="button"
                  className="conversation-menu__button conversation-menu__button--danger"
                  onClick={() => {
                    setDeleteConvId(conv.id);
                    setShowDeleteModal(true);
                    setActiveMenu(null);
                  }}
                >
                  Delete
                </button>
              </div>
            )}
          </div>
        </li>
      );
    });

  const renderSection = (title, list) => {
    if (!list.length) return null;

    return (
      <section className="conversation-section">
        <h6 className="conversation-section__title">{title}</h6>

        <ul className="conversation-section__list">
          {renderConversations(list)}
        </ul>
      </section>
    );
  };

  return (
    <>
      <div
        className={`sidebar-drawer-left ${sidebarsOpen ? "open" : ""} ${embedded ? "sidebar-drawer-left--embedded" : ""
          }`}
      >
        <div className="sidebar-drawer-left__inner">
          <div className="sidebar-drawer-left__header">
            <h5 className="sidebar-drawer-left__title">Conversations</h5>
          </div>

          <div className="sidebar-drawer-left__content">
            <div className="sidebar-drawer-left__toolbar">
              <button
                type="button"
                className="sidebar-drawer-left__create-button"
                onClick={() => setShowCreateModal(true)}
              >
                New Conversation
              </button>
            </div>

            <div className="sidebar-drawer-left__panel">
              <div className="sidebar-drawer-left__scroll" ref={scrollRef}>
                {conversations.length === 0 ? (
                  <div className="sidebar-drawer-left__empty">
                    No conversations
                  </div>
                ) : (
                  <>
                    {renderSection("Today", today)}
                    {renderSection("Yesterday", yesterday)}
                    {renderSection("Last 7 Days", last7Days)}
                    {renderSection("Older", older)}
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <Modal
        title="New Conversation"
        show={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onConfirm={handleCreateConversation}
        confirmText="Create"
      >
        <input
          type="text"
          className="sidebar-modal-input"
          placeholder="Conversation Name"
          value={newConversationName}
          onChange={(e) => setNewConversationName(e.target.value)}
        />
      </Modal>

      <Modal
        title="Rename Conversation"
        show={showRenameModal}
        onClose={() => setShowRenameModal(false)}
        onConfirm={handleRenameConversation}
        confirmText="Save"
        cancelText="Cancel"
      >
        <input
          type="text"
          className="sidebar-modal-input"
          placeholder="New name"
          value={renameValue}
          onChange={(e) => setRenameValue(e.target.value)}
        />
      </Modal>

      <Modal
        title="Delete Conversation"
        show={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={handleDeleteConversation}
        confirmText="Delete"
        cancelText="Cancel"
      >
        <p className="sidebar-modal-text">
          Are you sure you want to delete this conversation?
        </p>
      </Modal>
    </>
  );
};

export default SidebarConversations;