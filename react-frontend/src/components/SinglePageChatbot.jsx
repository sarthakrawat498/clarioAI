import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { chatAPI, profileAPI, policyAPI, faqAPI } from '../api';
import { 
  Bot, 
  Send, 
  Sparkles, 
  History, 
  UserCheck, 
  BookOpen, 
  HelpCircle, 
  LogOut, 
  Plus, 
  X, 
  CheckCircle2, 
  Award, 
  Search, 
  Save, 
  Book, 
  ChevronDown, 
  ChevronUp,
  Shield,
  Trash2
} from 'lucide-react';


const QUICK_PROMPTS = [
  { text: "💡 Recommend best policy", query: "Can you recommend the top health insurance policy based on my health profile and budget?" },
  { text: "🧮 Calculate annual premium", query: "Can you estimate my annual health insurance premium?" },
  { text: "🩺 Am I eligible for knee claim?", query: "Am I eligible to claim ₹2,00,000 for knee surgery hospital stay after 2 years of policy?" },
  { text: "⚖️ Compare Star vs HDFC", query: "Compare Star Health Comprehensive vs HDFC ERGO Optima Secure side by side." },
  { text: "📜 What is PED waiting period?", query: "What is the standard pre-existing disease (PED) waiting period across policies?" },
  { text: "📊 Show policy catalogue", query: "What health insurance policies are available in the catalogue?" },
];

const FormattedMessage = ({ content }) => {
  if (!content) return null;

  const parseBlocks = (text) => {
    // Strip trailing citation placeholder text if already formatted in sources
    let cleanText = text.replace(/📖 Policy Excerpt Citations:[\s\S]*$/gi, '').trim();

    const lines = cleanText.split('\n');
    const blocks = [];
    let tableRows = [];
    let inTable = false;
    let listItems = [];
    let inList = false;

    const renderBold = (str) => {
      const parts = str.split(/(\*\*.*?\*\*|\*.*?\*|__.*?__|`.*?`)/g);
      return parts.map((part, i) => {
        if ((part.startsWith('**') && part.endsWith('**')) || (part.startsWith('__') && part.endsWith('__'))) {
          return <strong key={i} style={{ color: '#f8fafc', fontWeight: 700 }}>{part.slice(2, -2)}</strong>;
        }
        if (part.startsWith('*') && part.endsWith('*')) {
          return <em key={i} style={{ color: '#e2e8f0' }}>{part.slice(1, -1)}</em>;
        }
        if (part.startsWith('`') && part.endsWith('`')) {
          return <code key={i} style={{ background: 'rgba(56,189,248,0.15)', color: '#38bdf8', padding: '2px 6px', borderRadius: '4px', fontSize: '0.82em', fontFamily: 'monospace' }}>{part.slice(1, -1)}</code>;
        }
        return part;
      });
    };

    const flushList = () => {
      if (listItems.length > 0) {
        blocks.push(
          <ul key={`ul-${blocks.length}`} style={{ margin: '8px 0 12px 18px', paddingLeft: '8px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {listItems.map((item, idx) => (
              <li key={idx} style={{ color: '#cbd5e1', fontSize: '0.92rem', lineHeight: '1.5' }}>
                {renderBold(item)}
              </li>
            ))}
          </ul>
        );
        listItems = [];
        inList = false;
      }
    };

    const flushTable = () => {
      if (tableRows.length > 0) {
        const headerRow = tableRows[0];
        const bodyRows = tableRows.slice(1).filter(r => !r.every(cell => cell.trim().startsWith('---') || cell.trim() === ''));

        blocks.push(
          <div key={`table-${blocks.length}`} style={{ overflowX: 'auto', margin: '14px 0', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.12)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left', background: 'rgba(15,23,42,0.6)' }}>
              <thead>
                <tr style={{ background: 'rgba(30,41,59,0.9)', borderBottom: '1px solid rgba(255,255,255,0.15)' }}>
                  {headerRow.map((cell, cIdx) => (
                    <th key={cIdx} style={{ padding: '10px 14px', color: '#38bdf8', fontWeight: 700 }}>
                      {renderBold(cell.trim())}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {bodyRows.map((r, rIdx) => (
                  <tr key={rIdx} style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', background: rIdx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)' }}>
                    {r.map((cell, cIdx) => (
                      <td key={cIdx} style={{ padding: '9px 14px', color: '#cbd5e1' }}>
                        {renderBold(cell.trim())}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        tableRows = [];
        inTable = false;
      }
    };

    for (let i = 0; i < lines.length; i++) {
      let line = lines[i].trim();
      if (!line) {
        flushList();
        flushTable();
        continue;
      }

      // Check for Table Row
      if (line.startsWith('|') && line.endsWith('|')) {
        flushList();
        inTable = true;
        const cells = line.split('|').slice(1, -1);
        tableRows.push(cells);
        continue;
      } else if (inTable) {
        flushTable();
      }

      // Check for List Item
      if (line.startsWith('- ') || line.startsWith('* ') || line.startsWith('• ') || /^\d+\.\s/.test(line)) {
        inList = true;
        const itemContent = line.replace(/^(-|\*|•|\d+\.)\s*/, '');
        listItems.push(itemContent);
        continue;
      } else if (inList) {
        flushList();
      }

      // Check for Headers (#, ##, ###)
      if (line.startsWith('#')) {
        const headerText = line.replace(/^#+\s*/, '');
        const level = line.match(/^#+/)[0].length;

        if (level === 1) {
          blocks.push(<h2 key={`h1-${blocks.length}`} style={{ fontSize: '1.2rem', fontWeight: 800, color: '#f8fafc', margin: '14px 0 8px 0', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '6px' }}>{renderBold(headerText)}</h2>);
        } else if (level === 2) {
          blocks.push(<h3 key={`h2-${blocks.length}`} style={{ fontSize: '1.08rem', fontWeight: 700, color: '#38bdf8', margin: '12px 0 6px 0' }}>{renderBold(headerText)}</h3>);
        } else {
          blocks.push(<h4 key={`h3-${blocks.length}`} style={{ fontSize: '0.96rem', fontWeight: 700, color: '#34d399', margin: '10px 0 4px 0' }}>{renderBold(headerText)}</h4>);
        }
        continue;
      }

      // Normal Paragraph
      blocks.push(
        <p key={`p-${blocks.length}`} style={{ margin: '6px 0 10px 0', lineHeight: '1.6', color: '#cbd5e1', fontSize: '0.92rem' }}>
          {renderBold(line)}
        </p>
      );
    }

    flushList();
    flushTable();

    return blocks;
  };

  return <div className="formatted-msg-container">{parseBlocks(content)}</div>;
};

export const SinglePageChatbot = () => {
  const { user, userProfile, logout, refreshProfile } = useAuth();

  // Chat State
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      agent_name: 'Clario AI Assistant',
      content: `Hello ${user?.full_name || ''}! 👋 I am your AI Health Insurance Advisor. Powered by multi-agent RAG (Coverage Explainer, Sales Recommendation, Actuarial Premium & Claims Evaluator), how can I assist you today?`,
      sources: [],
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);

  // Active Drawer State ('none' | 'profile' | 'catalog' | 'faqs' | 'history')
  const [activeDrawer, setActiveDrawer] = useState('none');

  // Profile Form State
  const [profileForm, setProfileForm] = useState({
    age: 30,
    gender: 'Male',
    city: 'Mumbai',
    city_tier: 'Tier 1',
    pre_existing_diseases: ['Diabetes'],
    coverage_type: 'Family Floater',
    family_members_count: 2,
    sum_insured_preference: 1000000,
    budget_annual_max: 25000,
  });
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileSuccess, setProfileSuccess] = useState(false);

  // Catalog State
  const [policies, setPolicies] = useState([]);
  const [catalogSearch, setCatalogSearch] = useState('');

  // FAQs State
  const [faqs, setFaqs] = useState([]);
  const [openFaqIndex, setOpenFaqIndex] = useState(0);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchSessions();
    fetchPolicies();
    fetchFaqs();
  }, []);

  useEffect(() => {
    if (userProfile) {
      setProfileForm({
        age: userProfile.age || 30,
        gender: userProfile.gender || 'Male',
        city: userProfile.city || 'Mumbai',
        city_tier: userProfile.city_tier || 'Tier 1',
        pre_existing_diseases: Array.isArray(userProfile.pre_existing_diseases) ? userProfile.pre_existing_diseases : ['Diabetes'],
        coverage_type: userProfile.coverage_type || 'Family Floater',
        family_members_count: userProfile.family_members_count || 2,
        sum_insured_preference: userProfile.sum_insured_preference || 1000000,
        budget_annual_max: userProfile.budget_annual_max || 25000,
      });
    }
  }, [userProfile]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const fetchSessions = async () => {
    try {
      const data = await chatAPI.getSessions();
      setSessions(data || []);
    } catch (e) {
      console.warn('Could not load chat sessions:', e);
    }
  };

  const handleDeleteSession = async (e, idToDelete) => {
    e.stopPropagation();
    try {
      await chatAPI.deleteSession(idToDelete);
      setSessions((prev) => prev.filter((s) => s.id !== idToDelete));
      if (sessionId === idToDelete) {
        startNewChat();
      }
    } catch (err) {
      console.error('Delete session error:', err);
    }
  };

  const handleClearAllSessions = async () => {
    if (!window.confirm('Are you sure you want to delete all past chat history?')) return;
    try {
      await chatAPI.clearAllSessions();
      setSessions([]);
      startNewChat();
    } catch (err) {
      console.error('Clear all sessions error:', err);
    }
  };


  const fetchPolicies = async () => {
    try {
      const data = await policyAPI.getPolicies();
      setPolicies(data || []);
    } catch (e) {
      console.warn('Could not load policies:', e);
    }
  };

  const fetchFaqs = async () => {
    try {
      const data = await faqAPI.getFaqs();
      setFaqs(data || []);
    } catch (e) {
      console.warn('Could not load faqs:', e);
    }
  };

  const handleSend = async (queryText = null) => {
    const textToSend = queryText || inputQuery;
    if (!textToSend.trim() || loading) return;

    const userMessage = {
      id: 'usr-' + Date.now(),
      sender: 'user',
      content: textToSend,
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!queryText) setInputQuery('');
    setLoading(true);

    try {
      const res = await chatAPI.sendQuery(textToSend, sessionId);
      if (res.session_id) setSessionId(res.session_id);

      const assistantMessage = {
        id: 'ast-' + Date.now(),
        sender: 'assistant',
        agent_name: res.agent_used || 'Multi-Agent Assistant',
        intent: res.intent,
        content: res.message,
        sources: res.sources || [],
        recommended_policies: res.recommended_policies,
        comparison_table: res.comparison_table,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      fetchSessions();
    } catch (err) {
      console.error('Chat error:', err);
      setMessages((prev) => [
        ...prev,
        {
          id: 'err-' + Date.now(),
          sender: 'assistant',
          agent_name: 'Error',
          content: 'Unable to reach backend server. Please verify FastAPI service is running.',
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const startNewChat = () => {
    setSessionId(null);
    setMessages([
      {
        id: 'welcome-' + Date.now(),
        sender: 'assistant',
        agent_name: 'Clario AI Assistant',
        content: 'New chat session started! What insurance coverage or claim query can I resolve for you?',
        sources: [],
      }
    ]);
  };

  const loadSession = (s) => {
    setSessionId(s.id);
    const converted = s.messages.map((m) => ({
      id: m.id,
      sender: m.sender,
      agent_name: m.agent_name || (m.sender === 'user' ? 'User' : 'Assistant'),
      content: m.content,
      sources: m.sources || [],
    }));
    setMessages(converted);
    setActiveDrawer('none');
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setSavingProfile(true);
    setProfileSuccess(false);
    try {
      await profileAPI.updateProfile({
        ...profileForm,
        age: Number(profileForm.age),
        family_members_count: Number(profileForm.family_members_count),
        sum_insured_preference: Number(profileForm.sum_insured_preference),
        budget_annual_max: Number(profileForm.budget_annual_max),
      });
      await refreshProfile();
      setProfileSuccess(true);
      setTimeout(() => setProfileSuccess(false), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setSavingProfile(false);
    }
  };

  const getAgentBadgeClass = (agentName) => {
    if (!agentName) return 'badge-coverage';
    const lower = agentName.toLowerCase();
    if (lower.includes('sales')) return 'badge-sales';
    if (lower.includes('compare')) return 'badge-comparison';
    if (lower.includes('claim')) return 'badge-claims';
    return 'badge-coverage';
  };

  const filteredPolicies = policies.filter((p) =>
    p.policy_name.toLowerCase().includes(catalogSearch.toLowerCase()) ||
    p.insurer_name.toLowerCase().includes(catalogSearch.toLowerCase())
  );

  return (
    <div className="app-layout">
      {/* Top Header */}
      <header className="navbar">
        <div className="navbar-brand">
          <div className="brand-icon">🛡️</div>
          <div>
            <div className="brand-title">Clario AI</div>
            <div className="brand-subtitle">Single-Page AI Health Assistant</div>
          </div>
        </div>

        <div className="nav-actions">
          <div className="system-badge">
            <span className="pulse-dot"></span>
            <span>Multi-Agent RAG Online</span>
          </div>

          <button 
            className="btn-secondary" 
            style={{ padding: '6px 14px', fontSize: '0.82rem', background: activeDrawer === 'profile' ? 'rgba(16,185,129,0.2)' : '' }}
            onClick={() => setActiveDrawer(activeDrawer === 'profile' ? 'none' : 'profile')}
          >
            <UserCheck size={16} /> Profile Onboarding
          </button>

          <button 
            className="btn-secondary" 
            style={{ padding: '6px 14px', fontSize: '0.82rem', background: activeDrawer === 'catalog' ? 'rgba(16,185,129,0.2)' : '' }}
            onClick={() => setActiveDrawer(activeDrawer === 'catalog' ? 'none' : 'catalog')}
          >
            <BookOpen size={16} /> Products
          </button>

          <button 
            className="btn-secondary" 
            style={{ padding: '6px 14px', fontSize: '0.82rem', background: activeDrawer === 'faqs' ? 'rgba(16,185,129,0.2)' : '' }}
            onClick={() => setActiveDrawer(activeDrawer === 'faqs' ? 'none' : 'faqs')}
          >
            <HelpCircle size={16} /> FAQs
          </button>

          {user && (
            <div className="user-pill">
              <div className="user-avatar">{user.full_name ? user.full_name[0].toUpperCase() : 'U'}</div>
              <span>{user.full_name || user.email}</span>
            </div>
          )}

          <button className="logout-btn" onClick={logout} title="Sign Out">
            <LogOut size={16} /> Exit
          </button>
        </div>
      </header>

      {/* Main Single-Page Chatbot Body */}
      <div className="main-body" style={{ position: 'relative' }}>
        {/* Left History Sidebar */}
        <aside className="sidebar" style={{ width: '280px', flexShrink: 0 }}>
          <button className="btn-primary" style={{ width: '100%', marginBottom: '16px' }} onClick={startNewChat}>
            <Plus size={18} /> New Chat Session
          </button>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', padding: '0 4px' }}>
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <History size={13} style={{ color: 'var(--cyan)' }} /> Past Conversations ({sessions.length})
            </div>
            {sessions.length > 0 && (
              <button
                onClick={handleClearAllSessions}
                style={{ background: 'transparent', border: 'none', color: '#fb7185', fontSize: '0.72rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '3px' }}
                title="Clear all chat history"
              >
                <Trash2 size={12} /> Clear All
              </button>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', overflowY: 'auto', flex: 1 }}>
            {sessions.map((s) => (
              <div
                key={s.id}
                className={`history-item ${sessionId === s.id ? 'active' : ''}`}
                onClick={() => loadSession(s)}
              >
                <Bot size={15} style={{ flexShrink: 0, color: 'var(--cyan)' }} />
                <span className="history-item-title">{s.session_title}</span>
                <button
                  className="delete-session-btn"
                  onClick={(e) => handleDeleteSession(e, s.id)}
                  title="Delete chat session"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
          </div>


          <div style={{ paddingTop: '16px', borderTop: '1px solid var(--border-color)', marginTop: 'auto' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center' }}>
              LangGraph RAG Engine v1.0
            </div>
          </div>
        </aside>

        {/* Central Chat Feed */}
        <main className="content-area" style={{ flex: 1, height: 'calc(100vh - 68px)', padding: '20px 28px', display: 'flex', flexDirection: 'column' }}>
          <div className="chat-messages-scroll" style={{ flex: 1 }}>
            {messages.map((msg) => {
              const isUser = msg.sender === 'user';
              return (
                <div key={msg.id} className={`chat-bubble ${isUser ? 'user' : 'assistant'}`}>
                  {!isUser && (
                    <div className={`agent-badge ${getAgentBadgeClass(msg.agent_name)}`}>
                      <Sparkles size={12} /> {msg.agent_name || 'AI Assistant'}
                    </div>
                  )}

                  <FormattedMessage content={msg.content} />

                  {/* Sources citation list */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '6px' }}>
                        📖 Policy Excerpt Citations:
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {msg.sources.map((src, sIdx) => (
                          <div key={sIdx} style={{ background: 'rgba(0,0,0,0.25)', padding: '8px 12px', borderRadius: 'var(--radius-sm)', fontSize: '0.78rem', borderLeft: '3px solid var(--cyan)' }}>
                            <div style={{ fontWeight: 700, color: '#38bdf8' }}>{src.insurer_name} - {src.policy_name}</div>
                            <div style={{ color: 'var(--text-muted)', marginTop: '2px', fontStyle: 'italic' }}>"{src.text || src.content}"</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {loading && (
              <div className="chat-bubble assistant" style={{ width: 'fit-content' }}>
                <div className="agent-badge badge-coverage">
                  <Sparkles size={12} className="pulse-dot" /> Multi-Agent Execution...
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Processing query through Coverage RAG, Sales & Actuarial Graph...
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Action Prompt Chips */}
          <div style={{ marginTop: '12px' }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Sparkles size={14} style={{ color: 'var(--cyan)' }} /> Quick Actions ("What do you want to do?"):
            </div>
            <div className="quick-chips-container">
              {QUICK_PROMPTS.map((chip, idx) => (
                <button key={idx} className="chip-btn" onClick={() => handleSend(chip.query)}>
                  {chip.text}
                </button>
              ))}
            </div>

            {/* Input Bar */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              style={{ display: 'flex', gap: '12px', marginTop: '10px' }}
            >
              <input
                type="text"
                className="form-input"
                placeholder="Ask any policy question, coverage terms, claim rules, or premium..."
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                disabled={loading}
              />
              <button type="submit" className="btn-primary" disabled={loading || !inputQuery.trim()}>
                <Send size={18} />
              </button>
            </form>
          </div>
        </main>

        {/* Slide-Over Drawer: Profile Onboarding */}
        {activeDrawer === 'profile' && (
          <div style={{ position: 'absolute', top: 0, right: 0, width: '420px', height: '100%', background: 'rgba(17, 24, 39, 0.96)', backdropFilter: 'blur(20px)', borderLeft: '1px solid var(--border-highlight)', zIndex: 100, padding: '24px', display: 'flex', flexDirection: 'column', boxShadow: '-10px 0 30px rgba(0,0,0,0.5)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <UserCheck size={20} style={{ color: 'var(--cyan)' }} /> Profile Onboarding
              </h3>
              <button className="btn-secondary" style={{ padding: '4px 8px' }} onClick={() => setActiveDrawer('none')}>
                <X size={18} />
              </button>
            </div>

            <div style={{ flex: 1, overflowY: 'auto' }}>
              {profileSuccess && (
                <div style={{ padding: '10px', background: 'rgba(16,185,129,0.2)', border: '1px solid rgba(16,185,129,0.4)', color: '#34d399', borderRadius: 'var(--radius-md)', fontSize: '0.82rem', marginBottom: '16px' }}>
                  <CheckCircle2 size={16} inline /> Profile updated! Chat agent is now personalized.
                </div>
              )}

              <form onSubmit={handleSaveProfile}>
                <div className="form-group">
                  <label className="form-label">Age</label>
                  <input type="number" className="form-input" value={profileForm.age} onChange={(e) => setProfileForm({ ...profileForm, age: e.target.value })} required />
                </div>

                <div className="form-group">
                  <label className="form-label">City Tier</label>
                  <select className="form-select" value={profileForm.city_tier} onChange={(e) => setProfileForm({ ...profileForm, city_tier: e.target.value })}>
                    <option value="Tier 1">Tier 1 (Metro)</option>
                    <option value="Tier 2">Tier 2</option>
                    <option value="Tier 3">Tier 3</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Coverage Type</label>
                  <select className="form-select" value={profileForm.coverage_type} onChange={(e) => setProfileForm({ ...profileForm, coverage_type: e.target.value })}>
                    <option value="Individual">Individual</option>
                    <option value="Family Floater">Family Floater</option>
                    <option value="Senior Citizen">Senior Citizen</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Family Members Count</label>
                  <input type="number" className="form-input" value={profileForm.family_members_count} onChange={(e) => setProfileForm({ ...profileForm, family_members_count: e.target.value })} required />
                </div>

                <div className="form-group">
                  <label className="form-label">Max Annual Budget (₹)</label>
                  <input type="number" className="form-input" value={profileForm.budget_annual_max} onChange={(e) => setProfileForm({ ...profileForm, budget_annual_max: e.target.value })} required />
                </div>

                <div className="form-group">
                  <label className="form-label">Pre-Existing Diseases (Comma Separated)</label>
                  <input type="text" className="form-input" value={profileForm.pre_existing_diseases.join(', ')} onChange={(e) => setProfileForm({ ...profileForm, pre_existing_diseases: e.target.value.split(',').map(s => s.trim()).filter(Boolean) })} />
                </div>

                <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: '12px' }} disabled={savingProfile}>
                  <Save size={16} /> {savingProfile ? 'Saving...' : 'Save Profile Context'}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* Slide-Over Drawer: Product Catalogue */}
        {activeDrawer === 'catalog' && (
          <div style={{ position: 'absolute', top: 0, right: 0, width: '480px', height: '100%', background: 'rgba(17, 24, 39, 0.96)', backdropFilter: 'blur(20px)', borderLeft: '1px solid var(--border-highlight)', zIndex: 100, padding: '24px', display: 'flex', flexDirection: 'column', boxShadow: '-10px 0 30px rgba(0,0,0,0.5)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <BookOpen size={20} style={{ color: 'var(--cyan)' }} /> Product Catalogue
              </h3>
              <button className="btn-secondary" style={{ padding: '4px 8px' }} onClick={() => setActiveDrawer('none')}>
                <X size={18} />
              </button>
            </div>

            <div style={{ position: 'relative', marginBottom: '16px' }}>
              <Search size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
              <input type="text" className="form-input" style={{ paddingLeft: '38px', fontSize: '0.85rem' }} placeholder="Search policy name..." value={catalogSearch} onChange={(e) => setCatalogSearch(e.target.value)} />
            </div>

            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {filteredPolicies.map((p) => (
                <div key={p.policy_id || p.id} className="glass-card" style={{ padding: '14px' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--cyan)' }}>{p.insurer_name}</div>
                  <div style={{ fontWeight: 800, fontSize: '0.95rem' }}>{p.policy_name}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    PED Waiting: {p.ped_waiting_period_months || 36}m | Room Rent: {p.room_rent_capping || 'No Capping'}
                  </div>
                  <button className="btn-secondary" style={{ width: '100%', marginTop: '10px', fontSize: '0.78rem', padding: '6px' }} onClick={() => { setActiveDrawer('none'); handleSend(`Explain details and benefits of ${p.policy_name} by ${p.insurer_name}`); }}>
                    Ask AI Assistant About This Policy
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Slide-Over Drawer: FAQs */}
        {activeDrawer === 'faqs' && (
          <div style={{ position: 'absolute', top: 0, right: 0, width: '440px', height: '100%', background: 'rgba(17, 24, 39, 0.96)', backdropFilter: 'blur(20px)', borderLeft: '1px solid var(--border-highlight)', zIndex: 100, padding: '24px', display: 'flex', flexDirection: 'column', boxShadow: '-10px 0 30px rgba(0,0,0,0.5)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <HelpCircle size={20} style={{ color: 'var(--primary)' }} /> Glossary & FAQs
              </h3>
              <button className="btn-secondary" style={{ padding: '4px 8px' }} onClick={() => setActiveDrawer('none')}>
                <X size={18} />
              </button>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {faqs.map((faq, idx) => {
                const isOpen = openFaqIndex === idx;
                return (
                  <div key={idx} style={{ border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', background: isOpen ? 'rgba(15,23,42,0.8)' : 'transparent', overflow: 'hidden' }}>
                    <button onClick={() => setOpenFaqIndex(isOpen ? -1 : idx)} style={{ width: '100%', padding: '12px 14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'transparent', border: 'none', color: 'var(--text-main)', fontWeight: 700, fontSize: '0.85rem', textAlign: 'left', cursor: 'pointer' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                        {faq.question || faq.term}
                        {faq.category && (
                          <span style={{ fontSize: '0.68rem', padding: '1px 6px', borderRadius: '10px', background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', fontWeight: 600 }}>
                            {faq.category}
                          </span>
                        )}
                      </span>
                      {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                    {isOpen && (
                      <div style={{ padding: '0 14px 14px', color: 'var(--text-muted)', fontSize: '0.82rem', lineHeight: '1.5' }}>
                        {faq.answer || faq.explanation}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
