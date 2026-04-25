import { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import "./RegisterForm.css";

const RegisterForm = ({ onSwitchToLogin }) => {
    const { register, error, isRegistering } = useAuth();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [localError, setLocalError] = useState("");

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLocalError("");

        const normalizedEmail = email.trim().toLowerCase();

        if (password !== confirmPassword) {
            setLocalError("Passwords do not match.");
            return;
        }

        await register({
            email: normalizedEmail,
            password,
        });
    };

    const handleSwitchToLogin = () => {
        setLocalError("");
        onSwitchToLogin();
    };

    return (
        <>
            <div className="register-form__header">
                <div className="register-form__eyebrow">Agent AI</div>
                <h1 className="register-form__title">Create account</h1>
                <p className="register-form__subtitle">
                    Register to access your AI workspace.
                </p>
            </div>

            <form onSubmit={handleSubmit} className="register-form__form">
                <div className="register-form__field">
                    <label
                        htmlFor="register-email"
                        className="register-form__label"
                    >
                        Email
                    </label>

                    <input
                        id="register-email"
                        type="email"
                        autoComplete="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        placeholder="Enter your email"
                        className="register-form__input"
                    />
                </div>

                <div className="register-form__field">
                    <label
                        htmlFor="register-password"
                        className="register-form__label"
                    >
                        Password
                    </label>

                    <div className="register-form__password-wrapper">
                        <input
                            id="register-password"
                            type={showPassword ? "text" : "password"}
                            autoComplete="new-password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            placeholder="Create password"
                            className="register-form__input register-form__input--password"
                        />

                        <button
                            type="button"
                            onClick={() => setShowPassword((prev) => !prev)}
                            className="register-form__toggle-password"
                        >
                            {showPassword ? "Hide" : "Show"}
                        </button>
                    </div>
                </div>

                <div className="register-form__field">
                    <label
                        htmlFor="register-confirm-password"
                        className="register-form__label"
                    >
                        Confirm password
                    </label>

                    <input
                        id="register-confirm-password"
                        type={showPassword ? "text" : "password"}
                        autoComplete="new-password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                        placeholder="Confirm password"
                        className="register-form__input"
                    />
                </div>

                {(localError || error) && (
                    <div className="register-form__error">
                        {localError || error}
                    </div>
                )}

                <button
                    type="submit"
                    disabled={isRegistering}
                    className="register-form__submit"
                >
                    {isRegistering ? "Creating account..." : "Create account"}
                </button>


            </form>
        </>
    );
};

export default RegisterForm;