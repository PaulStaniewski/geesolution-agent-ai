import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { confirmPasswordReset } from "../../services/api";
import AuthCardLayout from "./AuthCardLayout";
import "./ResetPasswordForm.css";

const ResetPasswordForm = () => {
    const { uid, token } = useParams();
    const navigate = useNavigate();

    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setMessage("");

        if (password !== confirmPassword) {
            setError("Passwords do not match.");
            return;
        }

        setIsSubmitting(true);

        try {
            const res = await confirmPasswordReset({ uid, token, password });
            setMessage(res.message || "Password has been reset successfully.");

            setTimeout(() => {
                navigate("/login");
            }, 1500);
        } catch (err) {
            const backendError =
                err.response?.data?.error ||
                err.response?.data?.password?.[0] ||
                "Invalid or expired reset link.";

            setError(Array.isArray(backendError) ? backendError[0] : backendError);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <AuthCardLayout>
            <div className="reset-password__header">
                <div className="reset-password__eyebrow">Agent AI</div>
                <h1 className="reset-password__title">Set new password</h1>
                <p className="reset-password__subtitle">
                    Enter your new password below.
                </p>
            </div>

            <form onSubmit={handleSubmit} className="reset-password__form">
                <div className="reset-password__field">
                    <label
                        htmlFor="password"
                        className="reset-password__label"
                    >
                        New password
                    </label>

                    <input
                        id="password"
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        className="reset-password__input"
                    />
                </div>

                <div className="reset-password__field">
                    <label
                        htmlFor="confirmPassword"
                        className="reset-password__label"
                    >
                        Confirm new password
                    </label>

                    <input
                        id="confirmPassword"
                        type={showPassword ? "text" : "password"}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                        className="reset-password__input"
                    />
                </div>

                <label className="reset-password__checkbox-row">
                    <input
                        type="checkbox"
                        checked={showPassword}
                        onChange={() => setShowPassword((prev) => !prev)}
                        className="reset-password__checkbox"
                    />
                    <span>Show passwords</span>
                </label>

                {message && (
                    <div className="reset-password__success">
                        {message}
                    </div>
                )}

                {error && (
                    <div className="reset-password__error">
                        {error}
                    </div>
                )}

                <button
                    type="submit"
                    disabled={isSubmitting}
                    className="reset-password__submit"
                >
                    {isSubmitting ? "Saving..." : "Reset password"}
                </button>

                <div className="reset-password__footer">
                    <Link
                        to="/login"
                        className="reset-password__back-link"
                    >
                        Back to sign in
                    </Link>
                </div>
            </form>
        </AuthCardLayout>
    );
};

export default ResetPasswordForm;