import React, { useState, useEffect } from "react";
import { policyAPI } from "../api";
import { BookOpen, Search, Filter, ShieldCheck, Check } from "lucide-react";

export const CatalogView = () => {
  const [policies, setPolicies] = useState([]);
  const [search, setSearch] = useState("");
  const [companyFilter, setCompanyFilter] = useState("ALL");
  const [loading, setLoading] = useState(true);

  const fetchPolicies = async () => {
    setLoading(true);
    try {
      const data = await policyAPI.getPolicies();
      setPolicies(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error("Failed to load catalog:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, []);

  const companies = ["ALL", ...new Set(policies.map((p) => p.insurer_name))];

  const filteredPolicies = policies.filter((p) => {
    const matchesSearch =
      p.policy_name.toLowerCase().includes(search.toLowerCase()) ||
      p.insurer_name.toLowerCase().includes(search.toLowerCase());
    const matchesCompany =
      companyFilter === "ALL" || p.insurer_name === companyFilter;
    return matchesSearch && matchesCompany;
  });

  const displayValue = (
    value,
    fallback = "Not available in the provided policy data.",
  ) => {
    if (value === null || value === undefined || value === "") return fallback;
    return value;
  };

  const parseHighlights = (value) => {
    if (!value) return [];
    if (Array.isArray(value)) return value.filter(Boolean).map(String);
    if (typeof value === "string") {
      try {
        const parsed = JSON.parse(value);
        if (Array.isArray(parsed)) {
          return parsed.filter(Boolean).map(String);
        }
      } catch (e) {
        return value
          .split(/\n|;|\|/)
          .map((item) => item.trim())
          .filter(Boolean);
      }
    }
    return [];
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
          <BookOpen size={24} style={{ color: "var(--cyan)" }} />
          Policy Catalogue
        </h2>
        <p
          style={{
            color: "var(--text-muted)",
            fontSize: "0.9rem",
            marginTop: "4px",
          }}
        >
          Browse verified health insurance policies ingested into our metadata
          RAG vector store.
        </p>
      </div>

      {/* Filter controls */}
      <div
        className="glass-card"
        style={{ padding: "16px 20px", marginBottom: "24px" }}
      >
        <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
          <div style={{ flex: 1, minWidth: "240px", position: "relative" }}>
            <Search
              size={18}
              style={{
                position: "absolute",
                left: "14px",
                top: "14px",
                color: "var(--text-muted)",
              }}
            />
            <input
              type="text"
              className="form-input"
              style={{ paddingLeft: "42px" }}
              placeholder="Search policy name or insurer..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div style={{ minWidth: "200px" }}>
            <select
              className="form-select"
              value={companyFilter}
              onChange={(e) => setCompanyFilter(e.target.value)}
            >
              {companies.map((c, i) => (
                <option key={i} value={c}>
                  {c === "ALL" ? "All Insurance Companies" : c}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div
          className="glass-card"
          style={{ textAlign: "center", padding: "40px" }}
        >
          <p style={{ color: "var(--text-muted)" }}>
            Loading policy database...
          </p>
        </div>
      ) : (
        <>
          {filteredPolicies.length === 0 ? (
            <div
              className="glass-card"
              style={{ textAlign: "center", padding: "40px" }}
            >
              <p style={{ color: "var(--text-muted)" }}>
                No policies match your search or budget filter right now.
              </p>
            </div>
          ) : (
        <div className="grid-2">
          {filteredPolicies.map((p) => (
            <div key={p.policy_id || p.id} className="glass-card">
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  marginBottom: "12px",
                }}
              >
                <div>
                  <div
                    style={{
                      fontSize: "0.78rem",
                      fontWeight: 700,
                      color: "var(--cyan)",
                      textTransform: "uppercase",
                    }}
                  >
                    {p.insurer_name}
                  </div>
                  <h3 style={{ fontSize: "1.15rem", fontWeight: 800 }}>

                <div
                  style={{
                    background: "rgba(15, 23, 42, 0.45)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: "var(--radius-md)",
                    padding: "12px",
                    marginBottom: "12px",
                  }}
                >
                  <div style={{ fontSize: "0.72rem", color: "var(--cyan)", fontWeight: 700, marginBottom: "6px" }}>
                    Detailed Description
                  </div>
                  <p style={{ margin: 0, color: "var(--text-main)", fontSize: "0.88rem", lineHeight: 1.55 }}>
                    {displayValue(
                      p.description,
                      `${p.policy_name} provides health coverage with ${displayValue(
                        p.room_rent_limit,
                      )}, PED waiting of ${displayValue(
                        p.ped_waiting_period_months,
                        "?",
                      )} months, and a premium estimate of ${
                        p.base_annual_premium_estimate !== null &&
                        p.base_annual_premium_estimate !== undefined
                          ? `₹${Number(p.base_annual_premium_estimate).toLocaleString()}`
                          : "Not available in the provided policy data"
                      }.`,
                    )}
                  </p>
                </div>

                <div style={{ marginBottom: "12px" }}>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginBottom: "6px" }}>
                    Key Highlights
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                    {parseHighlights(p.key_highlights).length > 0 ? (
                      parseHighlights(p.key_highlights).slice(0, 4).map((item, idx) => (
                        <span
                          key={idx}
                          style={{
                            padding: "6px 10px",
                            borderRadius: "999px",
                            background: "rgba(56,189,248,0.14)",
                            border: "1px solid rgba(56,189,248,0.25)",
                            color: "#e2e8f0",
                            fontSize: "0.76rem",
                          }}
                        >
                          {item}
                        </span>
                      ))
                    ) : (
                      <span style={{ color: "var(--text-muted)", fontSize: "0.82rem" }}>
                        No extra highlights available in the provided policy data.
                      </span>
                    )}
                  </div>
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "10px",
                    fontSize: "0.82rem",
                    color: "var(--text-muted)",
                  }}
                >
                  <div>
                    Claim Settlement: <strong style={{ color: "var(--text-main)" }}>{p.claim_settlement_ratio !== null && p.claim_settlement_ratio !== undefined ? `${p.claim_settlement_ratio}%` : "Not available"}</strong>
                  </div>
                  <div>
                    Restoration: <strong style={{ color: "var(--text-main)" }}>{displayValue(p.restoration_benefit)}</strong>
                  </div>
                </div>
                    {p.policy_name}
                  </h3>
                </div>
            )}
          </>
                <span
                  style={{
                    padding: "4px 10px",
                    borderRadius: "var(--radius-full)",
                    background: "rgba(16, 185, 129, 0.15)",
                    border: "1px solid rgba(16, 185, 129, 0.3)",
                    color: "#34d399",
                    fontSize: "0.75rem",
                    fontWeight: 700,
                  }}
                >
                  {p.plan_type || "Health Plan"}
                </span>
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "12px",
                  background: "rgba(15, 23, 42, 0.5)",
                  padding: "12px",
                  borderRadius: "var(--radius-md)",
                  margin: "12px 0",
                }}
              >
                <div>
                  <div
                    style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}
                  >
                    Sum Insured
                  </div>
                  <div style={{ fontWeight: 700, fontSize: "0.95rem" }}>
                    {p.base_sum_insured_min !== null &&
                    p.base_sum_insured_min !== undefined &&
                    p.base_sum_insured_max !== null &&
                    p.base_sum_insured_max !== undefined
                      ? `₹${Number(p.base_sum_insured_min).toLocaleString()} - ₹${Number(p.base_sum_insured_max).toLocaleString()}`
                      : "Not available in the provided policy data."}
                  </div>
                </div>
                <div>
                  <div
                    style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}
                  >
                    PED Waiting Period
                  </div>
                  <div style={{ fontWeight: 700, fontSize: "0.95rem" }}>
                    {p.ped_waiting_period_months !== null &&
                    p.ped_waiting_period_months !== undefined
                      ? `${p.ped_waiting_period_months} Months`
                      : "Not available in the provided policy data."}
                  </div>
                </div>
              </div>

              <div
                style={{
                  fontSize: "0.82rem",
                  color: "var(--text-muted)",
                  marginBottom: "12px",
                }}
              >
                Room Rent Cap:{" "}
                <strong style={{ color: "var(--text-main)" }}>
                  {displayValue(p.room_rent_limit)}
                </strong>{" "}
                | Copay:{" "}
                <strong style={{ color: "var(--text-main)" }}>
                  {p.co_pay_percentage !== null &&
                  p.co_pay_percentage !== undefined
                    ? `${p.co_pay_percentage}%`
                    : "Not available in the provided policy data."}
                </strong>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
