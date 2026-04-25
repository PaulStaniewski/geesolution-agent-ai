import { useEffect, useRef, useState } from "react";
import Modal from "../components/Modal";
import {
  uploadDocument,
  fetchDocuments,
  deleteDocuments,
} from "../services/api";
import "./SidebarDocuments.css";

const SidebarDocuments = ({ sidebarsOpen, embedded = false }) => {
  const fileInputRef = useRef(null);
  const didLoadRef = useRef(false);

  const [documents, setDocuments] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [activeDocumentTab, setActiveDocumentTab] = useState("user");

  const [showDeleteAllModal, setShowDeleteAllModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  const refreshDocuments = async () => {
    try {
      const docs = await fetchDocuments();
      setDocuments(Array.isArray(docs) ? docs : []);
    } catch (error) {
      console.error("Error fetching documents:", error);
    }
  };

  useEffect(() => {
    if (didLoadRef.current) return;

    didLoadRef.current = true;
    refreshDocuments();
  }, []);

  const haystackDocuments = documents.filter(
    (doc) => doc.corpus === "haystack"
  );

  const userDocuments = documents.filter(
    (doc) => doc.corpus === "user"
  );

  const deletableDocuments = documents.filter(
    (doc) => doc.is_deletable === true
  );

  const visibleDocuments =
    activeDocumentTab === "user" ? userDocuments : haystackDocuments;

  const visibleTitle =
    activeDocumentTab === "user" ? "My documents" : "Haystack corpus";

  const visibleEmptyText =
    activeDocumentTab === "user"
      ? "No uploaded documents"
      : "No Haystack documents";

  const handleFileChange = (event) => {
    setSelectedFiles(Array.from(event.target.files || []));
  };

  const handleUpload = async () => {
    if (!selectedFiles.length) return;

    try {
      await uploadDocument(selectedFiles);
      await refreshDocuments();

      setSelectedFiles([]);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error) {
      alert("Error uploading documents.");
    }
  };

  const openDeleteModal = (doc) => {
    if (!doc?.is_deletable) return;

    setDeleteId(doc.id);
    setShowDeleteModal(true);
  };

  const confirmDelete = async () => {
    try {
      await deleteDocuments(deleteId);
      await refreshDocuments();

      setShowDeleteModal(false);
      setDeleteId(null);
    } catch (error) {
      alert("Error deleting document.");
    }
  };

  const handleDeleteAllDocumentsWithModal = () => {
    setShowDeleteAllModal(true);
  };

  const confirmDeleteAllDocuments = async () => {
    try {
      await deleteDocuments();
      await refreshDocuments();
      setShowDeleteAllModal(false);
    } catch (error) {
      alert("Error deleting all documents.");
    }
  };

  const getDocumentName = (doc) => {
    return doc.file_name || doc.title || "Untitled document";
  };

  const renderDocumentsSection = (title, docs, emptyText) => (
    <section className="documents-section">
      <div className="documents-section__header">
        <h6 className="documents-section__title">{title}</h6>

        <span className="documents-section__count">
          {docs.length}
        </span>
      </div>

      <ul className="documents-list">
        {docs.length === 0 ? (
          <li className="documents-list__empty">{emptyText}</li>
        ) : (
          docs.map((doc) => {
            const name = getDocumentName(doc);

            return (
              <li
                key={doc.id}
                className="documents-list__item"
                data-readonly={doc.corpus === "haystack"}
              >
                <div className="documents-list__content">
                  <span
                    className="documents-list__name"
                    title={name}
                  >
                    {name}
                  </span>

                  <span className="documents-list__meta">
                    {doc.corpus === "haystack"
                      ? "Global documentation"
                      : "Uploaded document"}
                  </span>
                </div>

                {doc.is_deletable && (
                  <button
                    className="documents-list__delete"
                    onClick={() => openDeleteModal(doc)}
                    type="button"
                    title="Delete document"
                    aria-label={`Delete document ${name}`}
                  >
                    ✕
                  </button>
                )}
              </li>
            );
          })
        )}
      </ul>
    </section>
  );

  return (
    <>
      <div
        className={`sidebar-drawer-right ${sidebarsOpen ? "open" : ""} ${embedded ? "sidebar-drawer-right--embedded" : ""
          }`}
      >
        <div className="sidebar-drawer-right__inner">
          <div className="sidebar-drawer-right__header">
            <h5 className="sidebar-drawer-right__title">Upload Documents</h5>
          </div>

          <div className="sidebar-drawer-right__content">
            <div className="documents-upload-card">
              <label className="documents-upload-card__dropzone">
                <div className="documents-upload-card__title">
                  {selectedFiles.length > 0 ? "Files selected" : "Browse files"}
                </div>

                <div className="documents-upload-card__subtitle">
                  {selectedFiles.length > 0
                    ? `${selectedFiles.length} file${selectedFiles.length > 1 ? "s" : ""
                    } selected`
                    : "Select one or more documents"}
                </div>

                <input
                  type="file"
                  className="documents-upload-card__input"
                  multiple
                  ref={fileInputRef}
                  onChange={handleFileChange}
                />
              </label>

              <button
                className="documents-upload-card__button"
                onClick={handleUpload}
                disabled={!selectedFiles.length}
                type="button"
              >
                Upload {selectedFiles.length > 0 ? `(${selectedFiles.length})` : ""}
              </button>
            </div>

            {selectedFiles.length > 0 && (
              <p className="documents-selected-info">
                Selected files: {selectedFiles.length}
              </p>
            )}

            <div className="documents-header">
              <h6 className="documents-header__title">Documents</h6>

              <span className="documents-header__count">
                {documents.length}
              </span>
            </div>

            <div className="documents-tabs">
              <button
                type="button"
                className={`documents-tabs__button ${activeDocumentTab === "user"
                    ? "documents-tabs__button--active"
                    : ""
                  }`}
                onClick={() => setActiveDocumentTab("user")}
              >
                My documents
                <span>{userDocuments.length}</span>
              </button>

              <button
                type="button"
                className={`documents-tabs__button ${activeDocumentTab === "haystack"
                    ? "documents-tabs__button--active"
                    : ""
                  }`}
                onClick={() => setActiveDocumentTab("haystack")}
              >
                Haystack corpus
                <span>{haystackDocuments.length}</span>
              </button>
            </div>

            {renderDocumentsSection(
              visibleTitle,
              visibleDocuments,
              visibleEmptyText
            )}

            <button
              className="documents-delete-all-button"
              onClick={handleDeleteAllDocumentsWithModal}
              disabled={deletableDocuments.length === 0}
              type="button"
            >
              Delete My Documents
            </button>
          </div>
        </div>
      </div>

      <Modal
        title="Delete My Documents"
        show={showDeleteAllModal}
        onClose={() => setShowDeleteAllModal(false)}
        onConfirm={confirmDeleteAllDocuments}
        confirmText="Delete"
        cancelText="Cancel"
      >
        <p className="documents-modal-text">
          Are you sure you want to delete all your uploaded documents? Global Haystack documentation will not be deleted.
        </p>
      </Modal>

      <Modal
        title="Delete Document"
        show={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={confirmDelete}
        confirmText="Delete"
        cancelText="Cancel"
      >
        <p className="documents-modal-text">
          Are you sure you want to delete this document? This action cannot be undone.
        </p>
      </Modal>
    </>
  );
};

export default SidebarDocuments;