import React, { useState, useEffect } from 'react';
import { faqAPI } from '../api';
import { HelpCircle, ChevronDown, ChevronUp, Book } from 'lucide-react';

const DEFAULT_FAQS = [
  {
    question: "What is a Pre-Existing Disease (PED) waiting period?",
    answer: "A PED waiting period is the duration (typically 24 to 48 months) during which an insurance company will not cover expenses related to illnesses you already had before purchasing the policy."
  },
  {
    question: "What is the difference between Cashless and Reimbursement claims?",
    answer: "Cashless claims allow you to get treated at a network hospital without paying out-of-pocket (the insurer settles bills directly). Reimbursement claims occur at non-network hospitals where you pay first and submit bills later for refund."
  },
  {
    question: "What is a Co-Payment (Copay) clause?",
    answer: "Co-payment is a fixed percentage (e.g., 10% or 20%) of the total medical bill that you agree to pay from your own pocket during every claim settlement, while the insurer covers the rest."
  },
  {
    question: "What is Restoration / Reassurance benefit?",
    answer: "Restoration reinstates your total Sum Insured by up to 100% automatically if your sum insured is exhausted due to previous claims in the same policy year."
  },
  {
    question: "Why does City Tier affect health insurance premiums?",
    answer: "Tier 1 metro cities have higher healthcare treatment costs and room rates compared to Tier 2/3 cities, so insurers apply zone/tier multipliers to reflect local hospital pricing."
  }
];

export const FaqsView = () => {
  const [faqs, setFaqs] = useState(DEFAULT_FAQS);
  const [openIndex, setOpenIndex] = useState(0);

  useEffect(() => {
    fetchFaqs();
  }, []);

  const fetchFaqs = async () => {
    try {
      const data = await faqAPI.getFaqs();
      if (data && data.length > 0) setFaqs(data);
    } catch (e) {
      console.warn('Using default FAQs');
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '10px' }}>
          <HelpCircle size={24} style={{ color: 'var(--primary)' }} />
          Glossary & Frequently Asked Questions
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '4px' }}>
          Essential terminology and answers to common health insurance policy questions.
        </p>
      </div>

      <div className="glass-card" style={{ maxWidth: '800px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {faqs.map((faq, idx) => {
            const isOpen = openIndex === idx;
            return (
              <div
                key={idx}
                style={{
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  background: isOpen ? 'rgba(15, 23, 42, 0.8)' : 'rgba(255, 255, 255, 0.02)',
                  overflow: 'hidden',
                  transition: 'var(--transition-fast)',
                }}
              >
                <button
                  onClick={() => setOpenIndex(isOpen ? -1 : idx)}
                  style={{
                    width: '100%',
                    padding: '16px 20px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-main)',
                    fontWeight: 700,
                    fontSize: '0.95rem',
                    textAlign: 'left',
                    cursor: 'pointer',
                  }}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                    <Book size={18} style={{ color: 'var(--cyan)' }} />
                    {faq.question || faq.term}
                    {faq.category && (
                      <span style={{ fontSize: '0.72rem', padding: '2px 8px', borderRadius: '12px', background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', fontWeight: 600 }}>
                        {faq.category}
                      </span>
                    )}
                  </span>
                  {isOpen ? <ChevronUp size={20} style={{ color: 'var(--primary)' }} /> : <ChevronDown size={20} style={{ color: 'var(--text-muted)' }} />}
                </button>

                {isOpen && (
                  <div style={{ padding: '0 20px 20px 48px', color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: '1.6' }}>
                    {faq.answer || faq.explanation}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
