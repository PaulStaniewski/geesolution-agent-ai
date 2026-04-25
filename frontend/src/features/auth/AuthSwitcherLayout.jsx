import "./AuthSwitcherLayout.css";

const AuthSwitcherLayout = ({
    mode = "login",
    onSwitchToLogin,
    onSwitchToRegister,
    loginContent,
    registerContent,
}) => {
    const isRegister = mode === "register";

    return (
        <div className="auth-switcher">
            <div className="auth-switcher__glow auth-switcher__glow--blue" />
            <div className="auth-switcher__glow auth-switcher__glow--purple" />

            <div className="auth-switcher__container">
                <div className="auth-switcher__frame-glow" />

                <div className="auth-switcher__card">
                    <div className="auth-switcher__stage">
                        {/* LOGIN FORM */}
                        <div
                            className={`auth-switcher__panel auth-switcher__panel--login ${isRegister
                                ? "auth-switcher__panel--hidden-left"
                                : "auth-switcher__panel--visible"
                                }`}
                        >
                            <div className="auth-switcher__panel-inner">
                                {loginContent}
                            </div>
                        </div>

                        {/* REGISTER FORM */}
                        <div
                            className={`auth-switcher__panel auth-switcher__panel--register ${isRegister
                                ? "auth-switcher__panel--visible"
                                : "auth-switcher__panel--hidden-right"
                                }`}
                        >
                            <div className="auth-switcher__panel-inner">
                                {registerContent}
                            </div>
                        </div>

                        {/* OVERLAY PANEL */}
                        <div
                            className={`auth-switcher__overlay ${isRegister
                                ? "auth-switcher__overlay--register"
                                : "auth-switcher__overlay--login"
                                }`}
                        >
                            <div className="auth-switcher__overlay-glow auth-switcher__overlay-glow--top" />
                            <div className="auth-switcher__overlay-glow auth-switcher__overlay-glow--bottom" />

                            <div className="auth-switcher__overlay-content">
                                <div className="auth-switcher__overlay-eyebrow">
                                    Agent AI
                                </div>

                                {isRegister ? (
                                    <>
                                        <h2 className="auth-switcher__overlay-title">
                                            Create account
                                        </h2>

                                        <p className="auth-switcher__overlay-text">
                                            Access your AI workspace, documents
                                            and conversations.
                                        </p>

                                        <button
                                            type="button"
                                            onClick={onSwitchToLogin}
                                            className="auth-switcher__overlay-button"
                                        >
                                            Sign in
                                        </button>
                                    </>
                                ) : (
                                    <>
                                        <h2 className="auth-switcher__overlay-title">
                                            Welcome Back!
                                        </h2>

                                        <p className="auth-switcher__overlay-text">
                                            Sign in to continue working with your
                                            AI Agent workspace.
                                        </p>

                                        <button
                                            type="button"
                                            onClick={onSwitchToRegister}
                                            className="auth-switcher__overlay-button"
                                        >
                                            Create account
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
};

export default AuthSwitcherLayout;