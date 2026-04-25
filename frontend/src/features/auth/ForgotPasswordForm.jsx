import { useState } from "react";
import { Link } from "react-router-dom";
import { requestPasswordReset } from "../../services/api";
import AuthCardLayout from "./AuthCardLayout";
import "./ForgotPasswordForm.css";

const ForgotPasswordForm = () => {
    const [email, setEmail] = useState("");
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setMessage("");
        setIsSubmitting(true);

        try {
            const normalizedEmail = email.trim().toLowerCase();
            const res = await requestPasswordReset(normalizedEmail);

            setMessage(
                res.message ||
                "If an account with that email exists, a reset link has been sent."
            );
        } catch (err) {
            if (!err.response) {
                setError("Unable to connect to the server.");
            } else {
                setError("Could not process password reset request.");
            }
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <AuthCardLayout>
            <div className="forgot-password__header">
                <div className="forgot-password__eyebrow">Agent AI</div>
                <h1 className="forgot-password__title">Forgot password</h1>
                <p className="forgot-password__subtitle">
                    Enter your email and we’ll send you a reset link.
                </p>
            </div>

            <form onSubmit={handleSubmit} className="forgot-password__form">
                <div className="forgot-password__field">
                    <label
                        htmlFor="email"
                        className="forgot-password__label"
                    >
                        Email
                    </label>

                    <input
                        id="email"
                        type="email"
                        autoComplete="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        className="forgot-password__input"
                    />
                </div>

                {message && (
                    <div className="forgot-password__success">
                        {message}
                    </div>
                )}

                {error && (
                    <div className="forgot-password__error">
                        {error}
                    </div>
                )}

                <button
                    type="submit"
                    disabled={isSubmitting}
                    className="forgot-password__submit"
                >
                    {isSubmitting ? "Sending..." : "Send reset link"}
                </button>

                <div className="forgot-password__footer">
                    <Link
                        to="/login"
                        className="forgot-password__back-link"
                    >
                        Back to sign in
                    </Link>
                </div>
            </form>
        </AuthCardLayout>
    );
};

export default ForgotPasswordForm;