import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import {
    getRememberedEmail,
    setRememberedEmail,
    clearRememberedEmail,
} from "../../services/authStorage";
import AuthSwitcherLayout from "./AuthSwitcherLayout";
import RegisterForm from "./RegisterForm";
import "./LoginForm.css";

const LoginPanel = ({ onSwitchToRegister }) => {
    const { login, error, isLoggingIn } = useAuth();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [rememberMe, setRememberMe] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    useEffect(() => {
        const savedEmail = getRememberedEmail();
        if (savedEmail) {
            setEmail(savedEmail);
            setRememberMe(true);
        }
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();

        const normalizedEmail = email.trim().toLowerCase();

        if (rememberMe) {
            setRememberedEmail(normalizedEmail);
        } else {
            clearRememberedEmail();
        }

        await login(normalizedEmail, password);
    };

    const handleRememberChange = (e) => {
        const checked = e.target.checked;
        setRememberMe(checked);

        if (!checked) {
            clearRememberedEmail();
        }
    };

    return (
        <>
            <div className="login-panel__header">
                <div className="login-panel__eyebrow">Agent AI</div>
                <h1 className="login-panel__title">Sign in</h1>
                <p className="login-panel__subtitle">
                    Log in to access your Haystack Agent workspace.
                </p>
            </div>

            <form onSubmit={handleSubmit} className="login-panel__form">
                <div className="login-panel__field">
                    <label htmlFor="email" className="login-panel__label">
                        Email
                    </label>

                    <input
                        id="email"
                        type="email"
                        autoComplete="email"
                        autoFocus
                        placeholder="Enter your email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        className="login-panel__input"
                    />
                </div>

                <div className="login-panel__field">
                    <label htmlFor="password" className="login-panel__label">
                        Password
                    </label>

                    <div className="login-panel__password-wrapper">
                        <input
                            id="password"
                            type={showPassword ? "text" : "password"}
                            autoComplete="current-password"
                            placeholder="Enter your password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            className="login-panel__input login-panel__input--password"
                        />

                        <button
                            type="button"
                            onClick={() => setShowPassword((prev) => !prev)}
                            className="login-panel__toggle-password"
                        >
                            {showPassword ? "Hide" : "Show"}
                        </button>
                    </div>
                </div>

                <div className="login-panel__options">
                    <label className="login-panel__remember">
                        <input
                            type="checkbox"
                            checked={rememberMe}
                            onChange={handleRememberChange}
                            className="login-panel__checkbox"
                        />
                        <span>Remember me</span>
                    </label>

                    <Link
                        to="/forgot-password"
                        className="login-panel__forgot-link"
                    >
                        Forgot password?
                    </Link>
                </div>

                {error && (
                    <div className="login-panel__error">
                        {error}
                    </div>
                )}

                <button
                    type="submit"
                    disabled={isLoggingIn}
                    className="login-panel__submit"
                >
                    {isLoggingIn ? "Signing in..." : "Sign in"}
                </button>
            </form>
        </>
    );
};

const LoginForm = () => {
    const [mode, setMode] = useState("login");
    const { clearError } = useAuth();

    const switchToLogin = () => {
        clearError();
        setMode("login");
    };

    const switchToRegister = () => {
        clearError();
        setMode("register");
    };

    return (
        <AuthSwitcherLayout
            mode={mode}
            onSwitchToLogin={switchToLogin}
            onSwitchToRegister={switchToRegister}
            loginContent={
                <LoginPanel onSwitchToRegister={switchToRegister} />
            }
            registerContent={
                <RegisterForm onSwitchToLogin={switchToLogin} />
            }
        />
    );
};

export default LoginForm;