import React from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Auth } from "./components/Auth";
import { SinglePageChatbot } from "./components/SinglePageChatbot";
import { ProfileView } from "./components/ProfileView";

const MainApp = () => {
  const {
    isAuthenticated,
    loading,
    profileOnboardingRequired,
    completeProfileOnboarding,
  } = useAuth();

  if (loading) {
    return (
      <div className="auth-wrapper">
        <div className="auth-card" style={{ textAlign: "center" }}>
          <div
            className="brand-icon"
            style={{ margin: "0 auto 16px", width: "56px", height: "56px" }}
          >
            🛡️
          </div>
          <h3 style={{ fontSize: "1.2rem", fontWeight: 800 }}>
            Initializing AI Health Assistant...
          </h3>
          <p
            style={{
              color: "var(--text-muted)",
              marginTop: "8px",
              fontSize: "0.85rem",
            }}
          >
            Authenticating user session & vector database context
          </p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Auth />;
  }

  if (profileOnboardingRequired) {
    return (
      <div
        style={{
          minHeight: "100vh",
          background:
            "linear-gradient(135deg, #08111f 0%, #0f172a 50%, #111827 100%)",
          padding: "32px 20px",
        }}
      >
        <div style={{ maxWidth: "980px", margin: "0 auto" }}>
          <div
            style={{
              marginBottom: "18px",
              color: "var(--text-muted)",
              fontSize: "0.9rem",
            }}
          >
            Complete your profile onboarding first to personalize
            recommendations and unlock the assistant.
          </div>
          <ProfileView onComplete={completeProfileOnboarding} />
        </div>
      </div>
    );
  }

  return <SinglePageChatbot />;
};

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}
