import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { profileAPI } from "../api";
import { UserCheck, Save, CheckCircle2 } from "lucide-react";

export const ProfileView = ({ onComplete }) => {
  const { userProfile, refreshProfile } = useAuth();
  const [formData, setFormData] = useState({
    age: 30,
    gender: "Male",
    city: "Mumbai",
    city_tier: "Tier 1",
    pre_existing_diseases: ["Diabetes"],
    coverage_type: "Family Floater",
    family_members_count: 2,
    sum_insured_preference: 1000000,
    budget_annual_max: 25000,
    tobacco_user: false,
  });

  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (userProfile) {
      setFormData({
        age: userProfile.age || 30,
        gender: userProfile.gender || "Male",
        city: userProfile.city || "Mumbai",
        city_tier: userProfile.city_tier || "Tier 1",
        pre_existing_diseases: Array.isArray(userProfile.pre_existing_diseases)
          ? userProfile.pre_existing_diseases
          : ["Diabetes"],
        coverage_type: userProfile.coverage_type || "Family Floater",
        family_members_count: userProfile.family_members_count || 2,
        sum_insured_preference: userProfile.sum_insured_preference || 1000000,
        budget_annual_max: userProfile.budget_annual_max || 25000,
        tobacco_user: !!userProfile.tobacco_user,
      });
    }
  }, [userProfile]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);

    try {
      await profileAPI.updateProfile({
        ...formData,
        age: Number(formData.age),
        family_members_count: Number(formData.family_members_count),
        sum_insured_preference: Number(formData.sum_insured_preference),
        budget_annual_max: Number(formData.budget_annual_max),
      });
      await refreshProfile();
      setSuccess(true);
      if (onComplete) {
        onComplete();
      }
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error("Failed to update profile:", err);
    } finally {
      setSaving(false);
    }
  };

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
          <UserCheck size={24} style={{ color: "var(--cyan)" }} />
          User Profile & Health Parameters
        </h2>
        <p
          style={{
            color: "var(--text-muted)",
            fontSize: "0.9rem",
            marginTop: "4px",
          }}
        >
          Configure your personal health parameters used by the LangGraph
          Multi-Agent Assistant to tailor RAG answers and policy
          recommendations.
        </p>
      </div>

      <div className="glass-card" style={{ maxWidth: "720px" }}>
        {success && (
          <div
            style={{
              padding: "12px 16px",
              background: "rgba(16, 185, 129, 0.15)",
              border: "1px solid rgba(16, 185, 129, 0.4)",
              borderRadius: "var(--radius-md)",
              color: "#34d399",
              marginBottom: "20px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <CheckCircle2 size={18} />
            <span>
              Health Profile updated successfully! Smart recommendations will
              now reflect these preferences.
            </span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "16px",
            }}
          >
            <div className="form-group">
              <label className="form-label">Age</label>
              <input
                type="number"
                className="form-input"
                value={formData.age}
                onChange={(e) =>
                  setFormData({ ...formData, age: e.target.value })
                }
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Gender</label>
              <select
                className="form-select"
                value={formData.gender}
                onChange={(e) =>
                  setFormData({ ...formData, gender: e.target.value })
                }
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "16px",
            }}
          >
            <div className="form-group">
              <label className="form-label">City</label>
              <input
                type="text"
                className="form-input"
                value={formData.city}
                onChange={(e) =>
                  setFormData({ ...formData, city: e.target.value })
                }
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">City Tier</label>
              <select
                className="form-select"
                value={formData.city_tier}
                onChange={(e) =>
                  setFormData({ ...formData, city_tier: e.target.value })
                }
              >
                <option value="Tier 1">Tier 1 (Metro)</option>
                <option value="Tier 2">Tier 2</option>
                <option value="Tier 3">Tier 3</option>
              </select>
            </div>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "16px",
            }}
          >
            <div className="form-group">
              <label className="form-label">Coverage Type</label>
              <select
                className="form-select"
                value={formData.coverage_type}
                onChange={(e) =>
                  setFormData({ ...formData, coverage_type: e.target.value })
                }
              >
                <option value="Individual">Individual</option>
                <option value="Family Floater">Family Floater</option>
                <option value="Senior Citizen">Senior Citizen</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Family Members Count</label>
              <input
                type="number"
                className="form-input"
                value={formData.family_members_count}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    family_members_count: e.target.value,
                  })
                }
                required
              />
            </div>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "16px",
            }}
          >
            <div className="form-group">
              <label className="form-label">Sum Insured Preference (₹)</label>
              <input
                type="number"
                className="form-input"
                value={formData.sum_insured_preference}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    sum_insured_preference: e.target.value,
                  })
                }
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Max Annual Budget (₹)</label>
              <input
                type="number"
                className="form-input"
                value={formData.budget_annual_max}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    budget_annual_max: e.target.value,
                  })
                }
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">
              Pre-Existing Diseases (Comma Separated)
            </label>
            <input
              type="text"
              className="form-input"
              value={formData.pre_existing_diseases.join(", ")}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  pre_existing_diseases: e.target.value
                    .split(",")
                    .map((s) => s.trim())
                    .filter(Boolean),
                })
              }
              placeholder="e.g. Diabetes, Hypertension, Asthma"
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            style={{ marginTop: "12px" }}
            disabled={saving}
          >
            <Save size={18} />
            {saving
              ? "Saving Profile..."
              : onComplete
                ? "Save and Continue"
                : "Save Health Profile"}
          </button>
        </form>
      </div>
    </div>
  );
};
