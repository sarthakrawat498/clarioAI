import React, { useState, useEffect } from 'react';
import { policyAPI } from '../api';
import { BookOpen, Search, Filter, ShieldCheck, Check } from 'lucide-react';

export const CatalogView = () => {
  const [policies, setPolicies] = useState([]);
  const [search, setSearch] = useState('');
  const [companyFilter, setCompanyFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPolicies();
  }, []);

  const fetchPolicies = async () => {
    setLoading(true);
    try {
      const data = await policyAPI.getPolicies();
      setPolicies(data || []);
    } catch (e) {
      console.error('Failed to load catalog:', e);
    } finally {
      setLoading(false);
    }
  };

  const companies = ['ALL', ...new Set(policies.map((p) => p.insurer_name))];

  const filteredPolicies = policies.filter((p) => {
    const matchesSearch =
      p.policy_name.toLowerCase().includes(search.toLowerCase()) ||
      p.insurer_name.toLowerCase().includes(search.toLowerCase());
    const matchesCompany = companyFilter === 'ALL' || p.insurer_name === companyFilter;
    return matchesSearch && matchesCompany;
  });

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '10px' }}>
          <BookOpen size={24} style={{ color: 'var(--cyan)' }} />
          Policy Catalogue
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '4px' }}>
          Browse verified health insurance policies ingested into our metadata RAG vector store.
        </p>
      </div>

      {/* Filter controls */}
      <div className="glass-card" style={{ padding: '16px 20px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '240px', position: 'relative' }}>
            <Search size={18} style={{ position: 'absolute', left: '14px', top: '14px', color: 'var(--text-muted)' }} />
            <input
              type="text"
              className="form-input"
              style={{ paddingLeft: '42px' }}
              placeholder="Search policy name or insurer..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div style={{ minWidth: '200px' }}>
            <select
              className="form-select"
              value={companyFilter}
              onChange={(e) => setCompanyFilter(e.target.value)}
            >
              {companies.map((c, i) => (
                <option key={i} value={c}>
                  {c === 'ALL' ? 'All Insurance Companies' : c}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="glass-card" style={{ textAlign: 'center', padding: '40px' }}>
          <p style={{ color: 'var(--text-muted)' }}>Loading policy database...</p>
        </div>
      ) : (
        <div className="grid-2">
          {filteredPolicies.map((p) => (
            <div key={p.policy_id || p.id} className="glass-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                <div>
                  <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--cyan)', textTransform: 'uppercase' }}>
                    {p.insurer_name}
                  </div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 800 }}>{p.policy_name}</h3>
                </div>
                <span
                  style={{
                    padding: '4px 10px',
                    borderRadius: 'var(--radius-full)',
                    background: 'rgba(16, 185, 129, 0.15)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    color: '#34d399',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                  }}
                >
                  {p.plan_type || 'Health Plan'}
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', background: 'rgba(15, 23, 42, 0.5)', padding: '12px', borderRadius: 'var(--radius-md)', margin: '12px 0' }}>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Sum Insured</div>
                  <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>₹{(p.min_sum_insured || 500000).toLocaleString()} - ₹{(p.max_sum_insured || 10000000).toLocaleString()}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>PED Waiting Period</div>
                  <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>{p.ped_waiting_period_months || 36} Months</div>
                </div>
              </div>

              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                Room Rent Cap: <strong style={{ color: 'var(--text-main)' }}>{p.room_rent_capping || 'No Capping'}</strong> | Copay: <strong style={{ color: 'var(--text-main)' }}>{p.copay_percentage || 0}%</strong>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
