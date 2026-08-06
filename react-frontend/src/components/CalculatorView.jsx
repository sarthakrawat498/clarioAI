import React, { useState } from 'react';
import { premiumAPI } from '../api';
import { Calculator, DollarSign, ShieldAlert, Sparkles } from 'lucide-react';

export const CalculatorView = () => {
  const [formData, setFormData] = useState({
    age: 32,
    city_tier: 'Tier 1',
    family_members_count: 2,
    coverage_type: 'Family Floater',
    sum_insured: 1000000,
    tobacco_user: false,
    has_pre_existing_diseases: false,
  });

  const [estimate, setEstimate] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await premiumAPI.estimatePremium({
        ...formData,
        age: Number(formData.age),
        family_members_count: Number(formData.family_members_count),
        sum_insured: Number(formData.sum_insured),
      });
      setEstimate(res);
    } catch (err) {
      console.error('Calculator error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Calculator size={24} style={{ color: 'var(--primary)' }} />
          Actuarial Premium Calculator
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '4px' }}>
          Real-time actuarial model estimating annual insurance premium based on age, location tier, coverage type & health risk factors.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <div className="glass-card">
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '16px' }}>Input Profile Parameters</h3>

          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Primary Applicant Age</label>
                <input
                  type="number"
                  className="form-input"
                  value={formData.age}
                  onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                  min="18"
                  max="80"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">City Tier Location</label>
                <select
                  className="form-select"
                  value={formData.city_tier}
                  onChange={(e) => setFormData({ ...formData, city_tier: e.target.value })}
                >
                  <option value="Tier 1">Tier 1 (Metro Cities)</option>
                  <option value="Tier 2">Tier 2 Cities</option>
                  <option value="Tier 3">Tier 3 / Rural</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Coverage Type</label>
                <select
                  className="form-select"
                  value={formData.coverage_type}
                  onChange={(e) => setFormData({ ...formData, coverage_type: e.target.value })}
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
                  onChange={(e) => setFormData({ ...formData, family_members_count: e.target.value })}
                  min="1"
                  max="6"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Desired Sum Insured (₹)</label>
              <select
                className="form-select"
                value={formData.sum_insured}
                onChange={(e) => setFormData({ ...formData, sum_insured: e.target.value })}
              >
                <option value={500000}>₹5,00,000 (5 Lakhs)</option>
                <option value={1000000}>₹10,00,000 (10 Lakhs)</option>
                <option value={1500000}>₹15,00,000 (15 Lakhs)</option>
                <option value={2500000}>₹25,00,000 (25 Lakhs)</option>
                <option value={5000000}>₹50,00,000 (50 Lakhs)</option>
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Tobacco / Smoker Status</label>
                <select
                  className="form-select"
                  value={formData.tobacco_user ? 'yes' : 'no'}
                  onChange={(e) => setFormData({ ...formData, tobacco_user: e.target.value === 'yes' })}
                >
                  <option value="no">Non-Tobacco User</option>
                  <option value="yes">Tobacco User (+15% Surcharge)</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Pre-Existing Conditions</label>
                <select
                  className="form-select"
                  value={formData.has_pre_existing_diseases ? 'yes' : 'no'}
                  onChange={(e) => setFormData({ ...formData, has_pre_existing_diseases: e.target.value === 'yes' })}
                >
                  <option value="no">No Declared PED</option>
                  <option value="yes">Declared PED (+20% Surcharge)</option>
                </select>
              </div>
            </div>

            <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: '12px' }} disabled={loading}>
              {loading ? 'Calculating Actuarial Formula...' : 'Calculate Premium Estimate'}
            </button>
          </form>
        </div>

        {/* Calculation Output */}
        <div className="glass-card" style={{ border: estimate ? '1px solid var(--border-highlight)' : '1px solid var(--border-color)' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '16px' }}>Estimated Annual Premium</h3>

          {!estimate ? (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
              <Sparkles size={40} style={{ margin: '0 auto 12px', opacity: 0.5, color: 'var(--cyan)' }} />
              <p>Adjust variables and submit to calculate estimated premium.</p>
            </div>
          ) : (
            <div>
              <div style={{ background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(6, 182, 212, 0.2))', border: '1px solid var(--border-highlight)', borderRadius: 'var(--radius-lg)', padding: '24px', textAlign: 'center', marginBottom: '20px' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#34d399', textTransform: 'uppercase' }}>
                  Estimated Total Annual Premium
                </div>
                <div style={{ fontSize: '2.4rem', fontWeight: 800, color: '#fff', margin: '8px 0' }}>
                  ₹{(estimate.total_annual_premium || estimate.estimated_annual_premium || 0).toLocaleString()}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  (Approx. ₹{Math.round((estimate.total_annual_premium || estimate.estimated_annual_premium || 0) / 12).toLocaleString()} / month)
                </div>
              </div>

              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '8px' }}>
                📊 Actuarial Breakdown Matrix:
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: 'var(--radius-md)', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Base Premium Rate:</span>
                  <strong>₹{(estimate.breakdown?.base_premium || 10000).toLocaleString()}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Age Risk Multiplier:</span>
                  <strong>{estimate.breakdown?.age_multiplier || '1.25x'}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>City Tier Adjustment:</span>
                  <strong>{estimate.breakdown?.city_tier_multiplier || '1.15x'}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Pre-Existing Disease Surcharge:</span>
                  <strong>{estimate.breakdown?.ped_surcharge || '0%'}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>GST Tax (18%):</span>
                  <strong>₹{(estimate.breakdown?.gst_tax || 0).toLocaleString()}</strong>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
