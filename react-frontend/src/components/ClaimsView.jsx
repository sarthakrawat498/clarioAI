import React, { useState } from 'react';
import { claimAPI } from '../api';
import { Stethoscope, CheckCircle2, XCircle, AlertCircle, FileText } from 'lucide-react';

export const ClaimsView = () => {
  const [formData, setFormData] = useState({
    policy_name: 'Star Comprehensive Insurance',
    treatment_name: 'Knee Replacement Surgery',
    hospital_type: 'Network',
    room_category_chosen: 'Single Private Room',
    claimed_amount: 250000,
    policy_holding_duration_months: 24,
    is_pre_existing_condition: false,
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const resp = await claimAPI.checkEligibility({
        ...formData,
        claimed_amount: Number(formData.claimed_amount),
        policy_holding_duration_months: Number(formData.policy_holding_duration_months),
      });
      setResult(resp);
    } catch (err) {
      console.error('Claim check error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Stethoscope size={24} style={{ color: 'var(--amber)' }} />
          Claim Eligibility Evaluator
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '4px' }}>
          Check policy clause rules, waiting periods, copay deductions, and estimated payout before filing.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <div className="glass-card">
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '16px' }}>Claim Details Form</h3>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Active Health Policy</label>
              <select
                className="form-select"
                value={formData.policy_name}
                onChange={(e) => setFormData({ ...formData, policy_name: e.target.value })}
              >
                <option value="Star Comprehensive Insurance">Star Comprehensive Insurance</option>
                <option value="HDFC ERGO Optima Secure">HDFC ERGO Optima Secure</option>
                <option value="Niva Bupa ReAssure 2.0">Niva Bupa ReAssure 2.0</option>
                <option value="Care Health Advantage">Care Health Advantage</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Medical Procedure / Diagnosis</label>
              <input
                type="text"
                className="form-input"
                value={formData.treatment_name}
                onChange={(e) => setFormData({ ...formData, treatment_name: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Claimed Hospitalization Bill (₹)</label>
              <input
                type="number"
                className="form-input"
                value={formData.claimed_amount}
                onChange={(e) => setFormData({ ...formData, claimed_amount: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Policy Tenure Completed (Months)</label>
              <input
                type="number"
                className="form-input"
                value={formData.policy_holding_duration_months}
                onChange={(e) => setFormData({ ...formData, policy_holding_duration_months: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Is this a Pre-Existing Disease (PED)?</label>
              <select
                className="form-select"
                value={formData.is_pre_existing_condition ? 'yes' : 'no'}
                onChange={(e) => setFormData({ ...formData, is_pre_existing_condition: e.target.value === 'yes' })}
              >
                <option value="no">No - Acute / New Medical Condition</option>
                <option value="yes">Yes - Pre-Existing Illness</option>
              </select>
            </div>

            <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: '12px' }} disabled={loading}>
              {loading ? 'Evaluating Policy Rules...' : 'Evaluate Claim Eligibility'}
            </button>
          </form>
        </div>

        {/* Results Card */}
        <div className="glass-card" style={{ border: result ? '1px solid var(--border-highlight)' : '1px solid var(--border-color)' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '16px' }}>Eligibility Decision Breakdown</h3>

          {!result ? (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
              <FileText size={40} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
              <p>Fill in claim bill details and submit form to view rule evaluation.</p>
            </div>
          ) : (
            <div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '14px',
                  borderRadius: 'var(--radius-md)',
                  background: result.is_eligible ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                  border: `1px solid ${result.is_eligible ? 'rgba(16, 185, 129, 0.4)' : 'rgba(244, 63, 94, 0.4)'}`,
                  marginBottom: '20px',
                }}
              >
                {result.is_eligible ? (
                  <CheckCircle2 size={28} style={{ color: '#34d399' }} />
                ) : (
                  <XCircle size={28} style={{ color: '#fb7185' }} />
                )}
                <div>
                  <div style={{ fontSize: '1.05rem', fontWeight: 800, color: result.is_eligible ? '#34d399' : '#fb7185' }}>
                    {result.status || (result.is_eligible ? 'CLAIM APPROVED' : 'CLAIM REJECTED / SUBJECT TO WAITING PERIOD')}
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                    Estimated Payable Amount: <strong style={{ color: 'var(--text-main)' }}>₹{(result.estimated_approved_amount || 0).toLocaleString()}</strong>
                  </div>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Evaluated Rule Reason</label>
                <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '12px', borderRadius: 'var(--radius-md)', fontSize: '0.88rem' }}>
                  {result.explanation || result.eligibility_notes || 'All clause conditions validated successfully.'}
                </div>
              </div>

              {result.deductions !== undefined && typeof result.deductions === 'number' && (
                <div style={{ marginTop: '16px' }}>
                  <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '8px' }}>
                    Total Deductions & Copay:
                  </div>
                  <div style={{ background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: 'var(--radius-md)', fontSize: '0.85rem' }}>
                    <div>Amount to be Deducted: ₹{(result.deductions).toLocaleString()}</div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
