import React from 'react';
import { 
  Bot, 
  Sparkles, 
  BookOpen, 
  Scale, 
  Stethoscope, 
  Calculator, 
  UserCheck, 
  HelpCircle 
} from 'lucide-react';

export const NAV_ITEMS = [
  { id: 'chat', label: 'AI Chatbot Hub', icon: Bot },
  { id: 'recommendations', label: 'Smart Recommendations', icon: Sparkles },
  { id: 'catalog', label: 'Policy Catalogue', icon: BookOpen },
  { id: 'compare', label: 'Compare Policies', icon: Scale },
  { id: 'claims', label: 'Claim Checker', icon: Stethoscope },
  { id: 'calculator', label: 'Premium Calculator', icon: Calculator },
  { id: 'profile', label: 'User Profile', icon: UserCheck },
  { id: 'faqs', label: 'Glossary & FAQs', icon: HelpCircle },
];

export const Sidebar = ({ activeTab, setActiveTab }) => {
  return (
    <aside className="sidebar">
      <div style={{ padding: '0 8px 12px', color: 'var(--text-dim)', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Navigation
      </div>
      {NAV_ITEMS.map((item) => {
        const Icon = item.icon;
        const isActive = activeTab === item.id;
        return (
          <button
            key={item.id}
            className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
            onClick={() => setActiveTab(item.id)}
          >
            <Icon size={18} className="sidebar-nav-icon" style={{ color: isActive ? '#34d399' : 'inherit' }} />
            <span>{item.label}</span>
          </button>
        );
      })}
    </aside>
  );
};
