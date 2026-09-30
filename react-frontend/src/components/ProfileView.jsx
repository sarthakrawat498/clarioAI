import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import { profileAPI } from "../api";
import {
  UserCheck,
  Save,
  CheckCircle2,
  Info,
  ChevronDown,
  X,
} from "lucide-react";

const PED_OPTIONS = [
  "None / No Pre-Existing Conditions",
  "Diabetes Mellitus",
  "Hypertension / High BP",
  "Asthma / Respiratory Conditions",
  "Thyroid Disorder",
  "Heart Disease / Cardiac Condition",
  "Kidney Disease / Renal Disorder",
  "Cancer / History of Tumor",
  "Arthritis / Joint Pain",
  "Gastrointestinal / Liver Condition",
  "Neurological / Epilepsy",
];

const COVERAGE_DESCRIPTIONS = {
  Individual: {
    title: "Individual Health Plan",
    icon: "👤",
    description:
      "Dedicated health insurance exclusively for a single policyholder. 100% of the sum insured is reserved for the primary applicant's medical treatment without sharing with family members.",
  },
  "Family Floater": {
    title: "Family Floater Plan",
    icon: "👨‍👩‍👧‍👦",
    description:
      "A single umbrella policy covering multiple family members (spouse, children, dependent parents). The total sum insured floats across all covered members and can be utilized by any member during the policy year.",
  },
  "Family Plan": {
    title: "Family Floater Plan",
    icon: "👨‍👩‍👧‍👦",
    description:
      "A single umbrella policy covering multiple family members (spouse, children, dependent parents). The total sum insured floats across all covered members and can be utilized by any member during the policy year.",
  },
  "Senior Citizen": {
    title: "Senior Citizen Special Cover",
    icon: "👵👴",
    description:
      "Tailored health coverage designed for older adults (typically age 60+). Focuses on age-specific medical risks, pre-existing condition management, cardiac/joint care, and higher hospital allowance needs.",
  },
};

// Formats digits into Indian locale format e.g. 1000000 -> "10,00,000"
const formatINRInput = (value) => {
  if (value === "" || value === null || value === undefined) return "";
  const cleanStr = String(value).replace(/[^0-9]/g, "");
  if (!cleanStr) return "";
  const num = Number(cleanStr);
  return num.toLocaleString("en-IN");
};

// Extracts raw number digits string e.g. "10,00,000" -> "1000000"
const parseINRInput = (formattedStr) => {
  if (!formattedStr) return "";
  return String(formattedStr).replace(/[^0-9]/g, "");
};

// Helper text for Lakhs / Crores / Thousands e.g. "₹10,00,000 (10 Lakhs)"
const getINRHelperText = (value) => {
  const cleanStr = String(value).replace(/[^0-9]/g, "");
  if (!cleanStr) return "";
  const num = Number(cleanStr);
  if (isNaN(num) || num === 0) return "";

  if (num >= 10000000) {
    const cr = num / 10000000;
    return `₹${num.toLocaleString("en-IN")} (${cr % 1 === 0 ? cr : cr.toFixed(2)} Crore${cr > 1 ? "s" : ""})`;
  } else if (num >= 100000) {
    const lakh = num / 100000;
    return `₹${num.toLocaleString("en-IN")} (${lakh % 1 === 0 ? lakh : lakh.toFixed(2)} Lakh${lakh > 1 ? "s" : ""})`;
  } else if (num >= 1000) {
    const k = num / 1000;
    return `₹${num.toLocaleString("en-IN")} (${k % 1 === 0 ? k : k.toFixed(2)} Thousand)`;
  }
  return `₹${num.toLocaleString("en-IN")}`;
};

export const ProfileView = ({ onComplete }) => {
  const { userProfile, refreshProfile } = useAuth();
  const [formData, setFormData] = useState({
    age: "",
    gender: "",
    city: "",
    pre_existing_diseases: [],
    coverage_type: "",
    family_members_count: "",
    sum_insured_preference: "",
    budget_annual_max: "",
    tobacco_user: false,
  });

  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [pedDropdownOpen, setPedDropdownOpen] = useState(false);
  const pedRef = useRef(null);

  useEffect(() => {
    if (userProfile) {
      setFormData({
        age:
          userProfile.age !== null && userProfile.age !== undefined
            ? userProfile.age
            : "",
        gender: userProfile.gender || "",
        city: userProfile.city || "",
        pre_existing_diseases: Array.isArray(userProfile.pre_existing_diseases)
          ? userProfile.pre_existing_diseases
          : [],
        coverage_type: userProfile.coverage_type || "",
        family_members_count:
          userProfile.family_members_count !== null &&
          userProfile.family_members_count !== undefined
            ? userProfile.family_members_count
            : "",
        sum_insured_preference:
          userProfile.sum_insured_preference !== null &&
          userProfile.sum_insured_preference !== undefined
            ? userProfile.sum_insured_preference
            : "",
        budget_annual_max:
          userProfile.budget_annual_max !== null &&
          userProfile.budget_annual_max !== undefined
            ? userProfile.budget_annual_max
            : "",
        tobacco_user: !!userProfile.tobacco_user,
      });
    }
  }, [userProfile]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (pedRef.current && !pedRef.current.contains(event.target)) {
        setPedDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handlePedToggle = (opt) => {
    if (opt.startsWith("None")) {
      setFormData((prev) => ({ ...prev, pre_existing_diseases: [] }));
      return;
    }
    setFormData((prev) => {
      const current = prev.pre_existing_diseases || [];
      const filtered = current.filter((item) => !item.startsWith("None"));
      if (filtered.includes(opt)) {
        return {
          ...prev,
          pre_existing_diseases: filtered.filter((d) => d !== opt),
        };
      } else {
        return { ...prev, pre_existing_diseases: [...filtered, opt] };
      }
    });
  };

  const removePedTag = (tag, e) => {
    e.stopPropagation();
    setFormData((prev) => ({
      ...prev,
      pre_existing_diseases: (prev.pre_existing_diseases || []).filter(
        (t) => t !== tag,
      ),
    }));
  };

  const isFamilyCoverage =
    formData.coverage_type === "Family Floater" ||
    formData.coverage_type === "Family Plan";

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);

    try {
      const payload = {
        ...formData,
        age: formData.age !== "" ? Number(formData.age) : undefined,
        family_members_count: isFamilyCoverage
          ? formData.family_members_count !== ""
            ? Number(formData.family_members_count)
            : 2
          : 1,
        sum_insured_preference:
          formData.sum_insured_preference !== ""
            ? Number(formData.sum_insured_preference)
            : undefined,
        budget_annual_max:
          formData.budget_annual_max !== ""
            ? Number(formData.budget_annual_max)
            : undefined,
      };

      await profileAPI.updateProfile(payload);
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
          Profile Details & Health Parameters
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
                placeholder="e.g. 30"
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
                required
              >
                <option value="">Select Gender</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: isFamilyCoverage ? "1fr 1fr 1fr" : "1fr 1fr",
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
                placeholder="e.g. Mumbai, Delhi"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Coverage Type</label>
              <select
                className="form-select"
                value={formData.coverage_type}
                onChange={(e) =>
                  setFormData({ ...formData, coverage_type: e.target.value })
                }
                required
              >
                <option value="">Select Coverage Type</option>
                <option value="Individual">Individual</option>
                <option value="Family Floater">Family Floater</option>
                <option value="Senior Citizen">Senior Citizen</option>
              </select>
            </div>

            {/* Only show Family Members Count when Family Floater / Family Plan is selected */}
            {isFamilyCoverage && (
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
                  placeholder="e.g. 2, 4"
                  min="1"
                  required
                />
              </div>
            )}
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
                type="text"
                className="form-input"
                value={formatINRInput(formData.sum_insured_preference)}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    sum_insured_preference: parseINRInput(e.target.value),
                  })
                }
                placeholder="e.g. 10,00,000 (10 Lakhs)"
                required
              />
              {formData.sum_insured_preference && (
                <div
                  style={{
                    fontSize: "0.78rem",
                    color: "#38bdf8",
                    marginTop: "4px",
                    fontWeight: 600,
                  }}
                >
                  💡 {getINRHelperText(formData.sum_insured_preference)}
                </div>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">
                Max Annual Premium Budget (₹)
              </label>
              <input
                type="text"
                className="form-input"
                value={formatINRInput(formData.budget_annual_max)}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    budget_annual_max: parseINRInput(e.target.value),
                  })
                }
                placeholder="e.g. 25,000 (25 Thousand)"
                required
              />
              {formData.budget_annual_max && (
                <div
                  style={{
                    fontSize: "0.78rem",
                    color: "#38bdf8",
                    marginTop: "4px",
                    fontWeight: 600,
                  }}
                >
                  💡 {getINRHelperText(formData.budget_annual_max)}
                </div>
              )}
            </div>
          </div>

          {/* Pre-Existing Diseases: Multi-Select Dropdown */}
          <div
            className="form-group"
            style={{ position: "relative" }}
            ref={pedRef}
          >
            <label className="form-label">
              Pre-Existing Diseases (Multi-Select)
            </label>
            <div
              className="form-input"
              style={{
                minHeight: "44px",
                height: "auto",
                display: "flex",
                flexWrap: "wrap",
                alignItems: "center",
                gap: "6px",
                cursor: "pointer",
                padding: "8px 12px",
                justifyContent: "space-between",
              }}
              onClick={() => setPedDropdownOpen(!pedDropdownOpen)}
            >
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "6px",
                  flex: 1,
                }}
              >
                {!formData.pre_existing_diseases ||
                formData.pre_existing_diseases.length === 0 ? (
                  <span
                    style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}
                  >
                    Select pre-existing health conditions (Insurance Approved
                    Options)...
                  </span>
                ) : (
                  formData.pre_existing_diseases.map((item) => (
                    <span
                      key={item}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "4px",
                        background: "rgba(6, 182, 212, 0.2)",
                        border: "1px solid rgba(6, 182, 212, 0.4)",
                        color: "#38bdf8",
                        padding: "3px 8px",
                        borderRadius: "var(--radius-sm)",
                        fontSize: "0.78rem",
                        fontWeight: 600,
                      }}
                    >
                      {item}
                      <X
                        size={14}
                        style={{ cursor: "pointer" }}
                        onClick={(e) => removePedTag(item, e)}
                      />
                    </span>
                  ))
                )}
              </div>
              <ChevronDown size={16} style={{ color: "var(--text-muted)" }} />
            </div>

            {pedDropdownOpen && (
              <div
                style={{
                  position: "absolute",
                  top: "100%",
                  left: 0,
                  right: 0,
                  marginTop: "4px",
                  background: "#0f172a",
                  border: "1px solid var(--border-highlight)",
                  borderRadius: "var(--radius-md)",
                  zIndex: 1000,
                  maxHeight: "220px",
                  overflowY: "auto",
                  padding: "6px",
                  boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
                }}
              >
                {PED_OPTIONS.map((opt) => {
                  const isChecked = opt.startsWith("None")
                    ? !formData.pre_existing_diseases ||
                      formData.pre_existing_diseases.length === 0
                    : (formData.pre_existing_diseases || []).includes(opt);
                  return (
                    <div
                      key={opt}
                      onClick={() => handlePedToggle(opt)}
                      style={{
                        padding: "8px 12px",
                        display: "flex",
                        alignItems: "center",
                        gap: "10px",
                        cursor: "pointer",
                        borderRadius: "var(--radius-sm)",
                        fontSize: "0.83rem",
                        background: isChecked
                          ? "rgba(16, 185, 129, 0.15)"
                          : "transparent",
                        color: isChecked ? "#34d399" : "var(--text-main)",
                        marginBottom: "2px",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        readOnly
                        style={{ cursor: "pointer" }}
                      />
                      <span>{opt}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Coverage Type Disclaimer Section at end of the page */}
          <div
            style={{
              marginTop: "24px",
              marginBottom: "20px",
              padding: "16px 20px",
              background: "rgba(15, 23, 42, 0.7)",
              border: "1px solid var(--border-highlight)",
              borderRadius: "var(--radius-md)",
            }}
          >
            <div
              style={{
                fontSize: "0.82rem",
                fontWeight: 700,
                color: "var(--cyan)",
                textTransform: "uppercase",
                marginBottom: "8px",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              <Info size={16} /> Coverage Type Summary & Disclaimer
            </div>
            {formData.coverage_type &&
            COVERAGE_DESCRIPTIONS[formData.coverage_type] ? (
              <div>
                <div
                  style={{
                    fontWeight: 800,
                    fontSize: "0.95rem",
                    color: "#fff",
                    marginBottom: "4px",
                  }}
                >
                  {COVERAGE_DESCRIPTIONS[formData.coverage_type].icon}{" "}
                  {COVERAGE_DESCRIPTIONS[formData.coverage_type].title}
                </div>
                <p
                  style={{
                    fontSize: "0.85rem",
                    color: "var(--text-muted)",
                    lineHeight: "1.5",
                    margin: 0,
                  }}
                >
                  {COVERAGE_DESCRIPTIONS[formData.coverage_type].description}
                </p>
              </div>
            ) : (
              <p
                style={{
                  fontSize: "0.85rem",
                  color: "var(--text-muted)",
                  margin: 0,
                  fontStyle: "italic",
                }}
              >
                Select a Coverage Type above to view detailed coverage
                information and policy guidelines.
              </p>
            )}
          </div>

          <button
            type="submit"
            className="btn-primary"
            style={{ marginTop: "12px", width: "100%" }}
            disabled={saving}
          >
            <Save size={18} />
            {saving
              ? "Saving Profile..."
              : onComplete
                ? "Save and Continue"
                : "Save Profile Details"}
          </button>
        </form>
      </div>
    </div>
  );
};
