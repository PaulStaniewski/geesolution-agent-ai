import { useEffect, useId, useRef } from "react";
import ReactDOM from "react-dom";
import "./Modal.css";

const FOCUSABLE_SELECTOR =
  'button, [href], input, textarea, select, [tabindex]:not([tabindex="-1"])';

const CloseIcon = ({ size = 18 }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <path d="M18 6 6 18" />
    <path d="m6 6 12 12" />
  </svg>
);

const Modal = ({
  title,
  show,
  onClose,
  onConfirm,
  confirmText = "Save",
  cancelText = "Cancel",
  children,
}) => {
  const modalRef = useRef(null);
  const onCloseRef = useRef(onClose);
  const titleId = useId();

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!show) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        onCloseRef.current?.();
        return;
      }

      if (e.key !== "Tab" || !modalRef.current) return;

      const focusableElements = modalRef.current.querySelectorAll(FOCUSABLE_SELECTOR);
      if (!focusableElements.length) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (e.shiftKey) {
        if (
          document.activeElement === firstElement ||
          document.activeElement === modalRef.current
        ) {
          e.preventDefault();
          lastElement.focus();
        }
      } else if (document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    const focusableElements = modalRef.current?.querySelectorAll(FOCUSABLE_SELECTOR);

    if (focusableElements?.length) {
      focusableElements[0].focus();
    } else {
      modalRef.current?.focus();
    }

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [show]);

  if (!show || typeof document === "undefined") return null;

  return ReactDOM.createPortal(
    <div className="app-modal-backdrop" onClick={() => onCloseRef.current?.()}>
      <div
        ref={modalRef}
        className="app-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="app-modal-header">
          <h2 id={titleId} className="app-modal-title">
            {title}
          </h2>

          <button
            type="button"
            className="app-modal-close"
            onClick={() => onCloseRef.current?.()}
            aria-label="Close"
          >
            <CloseIcon size={18} />
          </button>
        </div>

        <div className="app-modal-body">{children}</div>

        <div className="app-modal-footer">
          <button
            type="button"
            className="app-btn app-btn-secondary"
            onClick={() => onCloseRef.current?.()}
          >
            {cancelText}
          </button>

          <button
            type="button"
            className="app-btn app-btn-primary"
            onClick={() => onConfirm?.()}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
};

export default Modal;