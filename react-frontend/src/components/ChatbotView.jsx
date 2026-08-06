import React, { useState, useEffect, useRef } from 'react';
import { chatAPI } from '../api';
import { 
  Send, 
  Bot, 
  User, 
  Sparkles, 
  History, 
  BookOpen, 
  Calculator, 
  Stethoscope, 
  Scale, 
  ExternalLink,
  MessageSquarePlus
} from 'lucide-react';

const QUICK_PROMPTS = [
  { text: "🧮 Calculate premium for 35yo in Tier 1 city", query: "Can you calculate my annual estimated premium for age 35, Tier 1 city with Family Floater?" },
  { text: "🩺 Check claim eligibility for knee surgery", query: "Am I eligible to claim ₹2,00,000 for knee surgery hospital stay after 2 years of policy?" },
  { text: "💡 Recommend best policy for diabetes", query: "Which health policy is best for someone with pre-existing diabetes and 2 family members?" },
  { text: "⚖️ Compare Star Comprehensive vs HDFC Optima", query: "Compare Star Health Comprehensive vs HDFC ERGO Optima Secure side by side." },
  { text: "📜 What is pre-existing disease waiting period?", query: "What is the standard pre-existing disease (PED) waiting period across policies?" },
];

export const ChatbotView = ({ onNavigate }) => {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      agent_name: 'Clario AI Assistant',
      content: 'Hello! I am your AI Health Insurance Advisor. Powered by multi-agent RAG (Coverage Explainer, Sales Recommendation, Actuarial Premium & Claims Evaluator), how can I help you today?',
      sources: [],
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchSessions = async () => {
    try {
      const data = await chatAPI.getSessions();
      setSessions(data || []);
    } catch (e) {
      console.warn('Could not load chat sessions:', e);
    }
  };

  const handleSend = async (queryText = null) => {
    const textToSend = queryText || inputQuery;
    if (!textToSend.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
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
        id: Date.now() + 1,
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
          id: Date.now() + 1,
          sender: 'assistant',
          agent_name: 'Error',
          content: 'Sorry, I encountered an issue communicating with the AI multi-agent service. Please ensure the backend server on port 8001 is online.',
        }
      ]);
    } finally {
      setLoading(false);
    }
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
    setShowHistory(false);
  };

  const startNewChat = () => {
    setSessionId(null);
    setMessages([
      {
        id: 'welcome',
        sender: 'assistant',
        agent_name: 'Clario AI Assistant',
        content: 'New session started! What insurance question or calculation would you like to perform?',
        sources: [],
      }
    ]);
    setShowHistory(false);
  };

  const getAgentBadgeClass = (agentName) => {
    if (!agentName) return 'badge-coverage';
    const lower = agentName.toLowerCase();
    if (lower.includes('sales')) return 'badge-sales';
    if (lower.includes('compare')) return 'badge-comparison';
    if (lower.includes('claim')) return 'badge-claims';
    return 'badge-coverage';
  };

  return (
    <div className="chat-container">
      {/* Header Banner */}
      <div className="chat-header-banner">
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Bot size={22} style={{ color: 'var(--cyan)' }} /> 
            Multi-Agent AI Advisor
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Ask anything about insurance policies, calculate estimates, check claims, or request smart recommendations.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem' }} onClick={startNewChat}>
            <MessageSquarePlus size={16} /> New Chat
          </button>
          <button 
            className="btn-secondary" 
            style={{ padding: '6px 12px', fontSize: '0.8rem', background: showHistory ? 'rgba(16, 185, 129, 0.15)' : '' }} 
            onClick={() => setShowHistory(!showHistory)}
          >
            <History size={16} /> History ({sessions.length})
          </button>
        </div>
      </div>

      {/* History Drawer Overlay */}
      {showHistory && (
        <div className="glass-card" style={{ padding: '16px', border: '1px solid var(--border-highlight)' }}>
          <h4 style={{ fontSize: '0.9rem', marginBottom: '12px', color: 'var(--text-muted)' }}>Past Chat Sessions</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '180px', overflowY: 'auto' }}>
            {sessions.length === 0 ? (
              <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)' }}>No prior chat sessions found.</span>
            ) : (
              sessions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => loadSession(s)}
                  className="sidebar-nav-item"
                  style={{
                    padding: '8px 12px',
                    fontSize: '0.82rem',
                    background: s.id === sessionId ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255,255,255,0.03)',
                  }}
                >
                  <Bot size={14} />
                  <span style={{ flex: 1, textAlign: 'left', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                    {s.session_title || `Chat Session #${s.id}`}
                  </span>
                </button>
              ))
            )}
          </div>
        </div>
      )}

      {/* Messages Timeline */}
      <div className="chat-messages-scroll">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          return (
            <div key={msg.id} className={`chat-bubble ${isUser ? 'user' : 'assistant'}`}>
              {!isUser && (
                <div className={`agent-badge ${getAgentBadgeClass(msg.agent_name)}`}>
                  <Sparkles size={12} /> {msg.agent_name || 'AI Assistant'}
                </div>
              )}

              <div style={{ whiteSpace: 'pre-line' }}>{msg.content}</div>

              {/* RAG Sources rendering */}
              {msg.sources && msg.sources.length > 0 && (
                <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '6px' }}>
                    📖 Policy Citations & Excerpts:
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {msg.sources.map((src, sIdx) => (
                      <div
                        key={sIdx}
                        style={{
                          background: 'rgba(0,0,0,0.25)',
                          padding: '8px 12px',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '0.78rem',
                          borderLeft: '3px solid var(--cyan)',
                        }}
                      >
                        <div style={{ fontWeight: 700, color: '#38bdf8' }}>
                          {src.insurer_name} - {src.policy_name} ({src.clause_type})
                        </div>
                        <div style={{ color: 'var(--text-muted)', marginTop: '2px', fontStyle: 'italic' }}>
                          "{src.text || src.content || 'Clause excerpt details.'}"
                        </div>
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
              <Sparkles size={12} className="pulse-dot" /> Multi-Agent Workflow Executing...
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Analyzing metadata, ChromaDB RAG vector store & actuarial models...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Action Prompt Chips ("What do you want to do?") */}
      <div style={{ marginTop: 'auto' }}>
        <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Sparkles size={14} style={{ color: 'var(--cyan)' }} /> Quick AI Prompt Chips ("What do you want to do?"):
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
            placeholder="Ask insurance question, claim eligibility, premium estimation..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={loading}
          />
          <button type="submit" className="btn-primary" disabled={loading || !inputQuery.trim()}>
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};
