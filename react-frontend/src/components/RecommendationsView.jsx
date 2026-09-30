import React, { useState, useEffect } from "react";
import { policyAPI } from "../api";
import { Sparkles, ShieldCheck, CheckCircle2, Award, Zap } from "lucide-react";

export const RecommendationsView = () => {
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const fetchRecommendations = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await policyAPI.getRecommendations();
      setRecommendations(data);
    } catch (err) {
      console.error("Failed to load recommendations:", err);
      setError(
        "Could not fetch recommendations. Please check your backend connection.",
      );
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div
        className="glass-card"
        style={{ textAlign: "center", padding: "40px" }}
      >
        <Sparkles
          size={32}
          className="pulse-dot"
          style={{ margin: "0 auto 16px", color: "var(--primary)" }}
        />
        <h3>Generating Smart Recommendations...</h3>
        <p style={{ color: "var(--text-muted)", marginTop: "8px" }}>
          Evaluating user profile, pre-existing conditions, city tier & budget
          thresholds...
        </p>
      </div>
    );
  }

  const topRecs = recommendations?.top_recommendations || [];

  if (!topRecs.length) {
    return (
      <div>
        <div style={{ marginBottom: "24px" }}>
          <h2
            style={{
              fontSize: "1.4rem",
              fontWeight: 800,
              display: "flex",
              alignItems: "center",
              gap: "10px",
            }}
          >
            <Sparkles size={24} style={{ color: "var(--amber)" }} />
            Smart Policy Recommendations
          </h2>
          <p
            style={{
              color: "var(--text-muted)",
              fontSize: "0.9rem",
              marginTop: "4px",
            }}
          >
            {recommendations?.general_advice ||
              "Personalized health policy matches tuned to your health profile and budget preferences."}
          </p>
        </div>

        <div
          className="glass-card"
          style={{ textAlign: "center", padding: "36px 24px" }}
        >
          <ShieldCheck
            size={30}
            style={{ color: "var(--cyan)", margin: "0 auto 12px" }}
          />
          <h3
            style={{
              fontSize: "1.05rem",
              fontWeight: 800,
              marginBottom: "8px",
            }}
          >
            No affordable policies found
          </h3>
          <p
            style={{
              color: "var(--text-muted)",
              maxWidth: "560px",
              margin: "0 auto",
            }}
          >
            Your current budget filter excludes all available policies. Update
            your budget to see matching plans.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: "24px" }}>
        <h2
          style={{
            fontSize: "1.4rem",
            fontWeight: 800,
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <Sparkles size={24} style={{ color: "var(--amber)" }} />
          Smart Policy Recommendations
        </h2>
        <p
          style={{
            color: "var(--text-muted)",
            fontSize: "0.9rem",
            marginTop: "4px",
          }}
        >
          {recommendations?.general_advice ||
            "Personalized health policy matches tuned to your health profile and budget preferences."}
        </p>
      </div>

      {error && (
        <div
          style={{
            padding: "14px",
            background: "rgba(244, 63, 94, 0.15)",
            border: "1px solid rgba(244, 63, 94, 0.4)",
            borderRadius: "var(--radius-md)",
            color: "#fb7185",
            marginBottom: "20px",
          }}
        >
          {error}
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        {topRecs.map((card, idx) => (
          <div
            key={idx}
            className="glass-card"
            style={{
              borderLeft: `4px solid ${idx === 0 ? "var(--primary)" : "var(--cyan)"}`,
              position: "relative",
              overflow: "hidden",
            }}
          >
            {idx === 0 && (
              <div
                style={{
                  position: "absolute",
                  top: "14px",
                  right: "-32px",
                  background: "var(--primary)",
                  color: "#0f172a",
                  fontWeight: 800,
                  fontSize: "0.7rem",
                  padding: "4px 36px",
                  transform: "rotate(45deg)",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
                }}
              >
                BEST MATCH
              </div>
            )}

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                flexWrap: "wrap",
                gap: "12px",
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: "0.8rem",
                    fontWeight: 700,
                    color: "var(--cyan)",
                    textTransform: "uppercase",
                  }}
                >
                  #{idx + 1} {card.insurer_name}
                </div>
                <h3
                  style={{
                    fontSize: "1.25rem",
                    fontWeight: 800,
                    marginTop: "2px",
                  }}
                >
                  {card.policy_name}
                </h3>
              </div>

              <div style={{ textAlign: "right" }}>
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                    padding: "6px 14px",
                    borderRadius: "var(--radius-full)",
                    background: "rgba(16, 185, 129, 0.18)",
                    border: "1px solid rgba(16, 185, 129, 0.4)",
                    color: "#34d399",
                    fontWeight: 800,
                    fontSize: "0.9rem",
                  }}
                >
                  <Award size={16} /> {card.match_score}% MATCH
                </span>
                <div
                  style={{
                    fontSize: "1.1rem",
                    fontWeight: 800,
                    color: "var(--text-main)",
                    marginTop: "8px",
                  }}
                >
                  ₹{(card.estimated_annual_premium || 0).toLocaleString()}{" "}
                  <span
                    style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}
                  >
                    / year
                  </span>
                </div>
              </div>
            </div>

            <div
              style={{
                marginTop: "16px",
                padding: "12px 16px",
                background: "rgba(15, 23, 42, 0.6)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-color)",
              }}
            >
              <div
                style={{
                  fontSize: "0.82rem",
                  fontWeight: 700,
                  color: "var(--text-muted)",
                  marginBottom: "4px",
                }}
              >
                💡 Recommendation Rationale:
              </div>
              <p style={{ fontSize: "0.9rem", color: "var(--text-main)" }}>
                {card.why_recommended}
              </p>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                gap: "16px",
                marginTop: "16px",
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: "0.8rem",
                    fontWeight: 700,
                    color: "var(--text-muted)",
                    marginBottom: "8px",
                  }}
                >
                  ✨ Key Policy Features:
                </div>
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "6px",
                  }}
                >
                  {(card.key_features || []).map((feat, fIdx) => (
                    <div
                      key={fIdx}
                      style={{
                        fontSize: "0.85rem",
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        color: "var(--text-main)",
                      }}
                    >
                      <CheckCircle2
                        size={16}
                        style={{ color: "var(--primary)", flexShrink: 0 }}
                      />
                      <span>{feat}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <div
                  style={{
                    fontSize: "0.8rem",
                    fontWeight: 700,
                    color: "var(--text-muted)",
                    marginBottom: "8px",
                  }}
                >
                  🛡️ Recommended Riders:
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                  {(card.recommended_riders || []).map((rider, rIdx) => (
                    <span
                      key={rIdx}
                      style={{
                        padding: "4px 10px",
                        borderRadius: "var(--radius-full)",
                        background: "rgba(99, 102, 241, 0.15)",
                        border: "1px solid rgba(99, 102, 241, 0.3)",
                        color: "#818cf8",
                        fontSize: "0.78rem",
                        fontWeight: 600,
                      }}
                    >
                      + {rider}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
