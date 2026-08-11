import React, { createContext, useState, useEffect, useContext } from "react";
import { authAPI, profileAPI } from "../api";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token") || null);
  const [loading, setLoading] = useState(true);
  const [profileOnboardingRequired, setProfileOnboardingRequired] = useState(
    localStorage.getItem("needs_profile_onboarding") === "true",
  );

  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        try {
          const userData = await authAPI.getMe();
          setUser(userData);
          try {
            const prof = await profileAPI.getProfile();
            setUserProfile(prof);
          } catch (pErr) {
            console.warn("Profile loading warning:", pErr);
          }
        } catch (err) {
          console.error("Token validation failed, logging out:", err);
          logout();
        }
      }
      setLoading(false);
    };

    initAuth();
  }, [token]);

  const login = async (email, password) => {
    const data = await authAPI.login(email, password);
    if (data.access_token) {
      localStorage.setItem("token", data.access_token);
      setToken(data.access_token);
      const userData = await authAPI.getMe();
      setUser(userData);
      try {
        const prof = await profileAPI.getProfile();
        setUserProfile(prof);
      } catch (e) {}
      return userData;
    }
    throw new Error("Authentication failed");
  };

  const register = async (fullName, email, password) => {
    const userReg = await authAPI.register(fullName, email, password);
    // Automatically log in after registration
    localStorage.setItem("needs_profile_onboarding", "true");
    setProfileOnboardingRequired(true);
    return await login(email, password);
  };

  const completeProfileOnboarding = () => {
    localStorage.removeItem("needs_profile_onboarding");
    setProfileOnboardingRequired(false);
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("needs_profile_onboarding");
    setToken(null);
    setUser(null);
    setUserProfile(null);
    setProfileOnboardingRequired(false);
  };

  const refreshProfile = async () => {
    try {
      const prof = await profileAPI.getProfile();
      setUserProfile(prof);
    } catch (e) {
      console.error("Failed to refresh profile:", e);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        userProfile,
        token,
        loading,
        login,
        register,
        logout,
        refreshProfile,
        completeProfileOnboarding,
        profileOnboardingRequired,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
