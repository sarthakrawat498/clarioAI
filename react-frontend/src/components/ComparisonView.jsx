import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { policyAPI } from '../api';
import { Scale, ArrowRightLeft, Check, X } from 'lucide-react';

export const ComparisonView = () => {
  const { userProfile } = useAuth();
  const [policies, setPolicies] = useState([]);
  const [p1Id, setP1Id] = useState('');
  const [p2Id, setP2Id] = useState('');
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchPolicies();
  }, [userProfile?.budget_annual_max]);

  const fetchPolicies = async () => {
    try {
      const budget = userProfile?.budget_annual_max;
      const list = await policyAPI.getPolicies(budget);
      const affordablePolicies = Array.isArray(list)
        ? list.filter((policy) => {
            const premium = Number(policy.base_annual_premium_estimate);
            return !budget || (!Number.isNaN(premium) && premium <= Number(budget));
          })
        : [];
      setPolicies(affordablePolicies);
      if (affordablePolicies.length >= 2) {
        setP1Id(affordablePolicies[0].id || affordablePolicies[0].policy_id);
        setP2Id(affordablePolicies[1].id || affordablePolicies[1].policy_id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleCompare = async () => {
    if (!p1Id || !p2Id) return;
    setLoading(true);
    try {
      const data = await policyAPI.comparePolicies(p1Id, p2Id);
      setComparison(data);
    } catch (e) {
      console.error('Comparison error:', e);
    } finally {
      setLoading(false);
    }
  };

  const p1 = policies.find((p) => String(p.id || p.policy_id) === String(p1Id));
  const p2 = policies.find((p) => String(p.id || p.policy_id) === String(p2Id));

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Scale size={24} style={{ color: 'var(--indigo)' }} />
          Compare Health Policies
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '4px' }}>
          Side-by-side feature, waiting period, room capping, and rider breakdown comparison.
        </p>
      </div>

      <div className="glass-card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr auto', gap: '16px', alignItems: 'center' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Select Policy #1</label>
            <select className="form-select" value={p1Id} onChange={(e) => setP1Id(e.target.value)}>
              {policies.map((p) => (
                <option key={p.id || p.policy_id} value={p.id || p.policy_id}>
                  {p.insurer_name} - {p.policy_name}
                </option>
              ))}
            </select>
          </div>

          <div style={{ color: 'var(--cyan)', marginTop: '20px' }}>
            <ArrowRightLeft size={22} />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Select Policy #2</label>
            <select className="form-select" value={p2Id} onChange={(e) => setP2Id(e.target.value)}>
              {policies.map((p) => (
                <option key={p.id || p.policy_id} value={p.id || p.policy_id}>
                  {p.insurer_name} - {p.policy_name}
                </option>
              ))}
            </select>
          </div>

          <button className="btn-primary" onClick={handleCompare} disabled={loading} style={{ marginTop: '20px' }}>
            {loading ? 'Comparing...' : 'Compare Side-by-Side'}
          </button>
        </div>
      </div>

      {(p1 && p2) && (
        <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th style={{ width: '30%' }}>Comparison Metric</th>
                  <th style={{ width: '35%', color: 'var(--cyan)' }}>{p1.insurer_name} - {p1.policy_name}</th>
                  <th style={{ width: '35%', color: 'var(--primary)' }}>{p2.insurer_name} - {p2.policy_name}</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Base Premium (Est.)</strong></td>
                  <td>₹{(p1.base_annual_premium || 12000).toLocaleString()} / yr</td>
                  <td>₹{(p2.base_annual_premium || 14000).toLocaleString()} / yr</td>
                </tr>
                <tr>
                  <td><strong>Pre-Existing Disease (PED) Waiting</strong></td>
                  <td>{p1.ped_waiting_period_months || 36} Months</td>
                  <td>{p2.ped_waiting_period_months || 24} Months</td>
                </tr>
                <tr>
                  <td><strong>Room Rent Capping</strong></td>
                  <td>{p1.room_rent_capping || 'Single Private Room'}</td>
                  <td>{p2.room_rent_capping || 'No Capping'}</td>
                </tr>
                <tr>
                  <td><strong>Co-Payment Percentage</strong></td>
                  <td>{p1.copay_percentage || 0}%</td>
                  <td>{p2.copay_percentage || 0}%</td>
                </tr>
                <tr>
                  <td><strong>Restoration Benefit</strong></td>
                  <td>{p1.restoration_benefit ? '100% Automatic Unlimited' : 'Standard'}</td>
                  <td>{p2.restoration_benefit ? '100% Automatic Unlimited' : 'Standard'}</td>
                </tr>
                <tr>
                  <td><strong>Day Care Treatments</strong></td>
                  <td>All Day Care Covered</td>
                  <td>All Day Care Covered</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
