import "./AuthCardLayout.css";

const AuthCardLayout = ({ children }) => {
    return (
        <div className="auth-card-layout">
            <div className="auth-card-layout__glow auth-card-layout__glow--blue" />
            <div className="auth-card-layout__glow auth-card-layout__glow--purple" />

            <div className="auth-card-layout__container">
                <div className="auth-card-layout__frame-glow" />

                <div className="auth-card-layout__card">
                    {children}
                </div>
            </div>
        </div>
    );
};

export default AuthCardLayout;