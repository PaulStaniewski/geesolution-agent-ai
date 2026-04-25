import "./AppLoading.css";

const Loading = () => {
    return (
        <div className="app-loading">
            <div className="app-loading-glow app-loading-glow-left" />
            <div className="app-loading-glow app-loading-glow-right" />

            <div className="app-loading-card">
                <div className="app-loading-spinner" />
                <div className="app-loading-text">Loading workspace...</div>
            </div>
        </div>
    );
};

export default Loading;