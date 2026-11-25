import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Bot, MessageCircle, Plus, Send, Trash2, Loader2, ExternalLink, FileText } from 'lucide-react';
import api from '../lib/api';
import MarkdownContent from '../components/assistant/MarkdownContent';

const SUGGESTIONS = [
  'What schemes am I eligible for?',
  'What documents are missing?',
  'Explain PMAY',
  'What should I do next?',
];

const SchemeCard = ({ scheme }) => (
  <article className="mt-3 rounded-xl border border-border bg-background/70 p-4">
    <div className="flex items-start justify-between gap-3">
      <div>
        <h3 className="font-semibold text-foreground">{scheme.name}</h3>
        {scheme.status && <p className="mt-1 text-xs text-muted-foreground">{scheme.status}{scheme.match_percentage != null ? ' · ' + Math.round(scheme.match_percentage) + '% match' : ''}</p>}
      </div>
      {scheme.deadline && <span className="shrink-0 rounded-md bg-secondary px-2 py-1 text-xs text-muted-foreground">Deadline {scheme.deadline}</span>}
    </div>
    {scheme.benefits_summary && <p className="mt-3 text-sm text-muted-foreground">{scheme.benefits_summary}</p>}
    {scheme.eligibility_summary && <p className="mt-2 text-sm text-muted-foreground">{scheme.eligibility_summary}</p>}
    {scheme.application_url && <a className="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline" href={scheme.application_url} target="_blank" rel="noreferrer">Official application <ExternalLink className="h-3.5 w-3.5" /></a>}
  </article>
);

const Action = ({ action }) => action.external
  ? <a href={action.href} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-xs font-medium text-foreground hover:bg-secondary">{action.label}<ExternalLink className="h-3 w-3" /></a>
  : <Link to={action.href} className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-xs font-medium text-foreground hover:bg-secondary">{action.label}</Link>;

const AssistantPage = () => {
  const [conversations, setConversations] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [error, setError] = useState('');
  const bottomRef = useRef(null);
  const activeConversation = useMemo(() => conversations.find((item) => item.id === conversationId), [conversations, conversationId]);

  const loadHistory = async () => {
    try {
      const { data } = await api.get('/assistant/conversations');
      setConversations(data.conversations || []);
    } catch {
      setError('Conversation history could not be loaded. Check your connection and try again.');
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => { loadHistory(); }, []);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);

  const openConversation = async (id) => {
    setConversationId(id);
    setError('');
    setLoading(true);
    try {
      const { data } = await api.get('/assistant/conversations/' + id);
      setMessages(data.messages || []);
    } catch {
      setError('This conversation could not be opened.');
    } finally {
      setLoading(false);
    }
  };

  const startNewConversation = () => {
    setConversationId(null);
    setMessages([]);
    setInput('');
    setError('');
  };

  const sendMessage = async (value = input) => {
    const content = value.trim();
    if (!content || loading) return;
    setInput('');
    setError('');
    setLoading(true);
    try {
      let id = conversationId;
      if (!id) {
        const created = await api.post('/assistant/conversations', {});
        id = created.data.conversation_id;
        setConversationId(id);
      }
      const { data } = await api.post('/assistant/conversations/' + id + '/messages', { content });
      setMessages((current) => [...current, data.user_message, data.assistant_message]);
      await loadHistory();
    } catch (requestError) {
      setInput(content);
      setError(requestError?.response?.data?.detail || 'The assistant could not respond. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const deleteConversation = async (event, id) => {
    event.stopPropagation();
    try {
      await api.delete('/assistant/conversations/' + id);
      setConversations((items) => items.filter((item) => item.id !== id));
      if (conversationId === id) startNewConversation();
    } catch {
      setError('Conversation history could not be deleted.');
    }
  };

  return (
    <section className="flex min-h-[calc(100vh-9rem)] flex-col overflow-hidden rounded-2xl border border-border bg-card md:min-h-[calc(100vh-10rem)] md:flex-row">
      <aside className="flex w-full shrink-0 flex-col border-b border-border bg-background/40 md:w-64 md:border-b-0 md:border-r">
        <div className="flex items-center justify-between px-4 py-4">
          <div>
            <h1 className="text-sm font-semibold text-foreground">AI Assistant</h1>
            <p className="mt-1 text-xs text-muted-foreground">Your AidFlow activity, in context</p>
          </div>
          <button type="button" onClick={startNewConversation} aria-label="New conversation" className="rounded-lg border border-border p-2 text-muted-foreground hover:bg-secondary hover:text-foreground"><Plus className="h-4 w-4" /></button>
        </div>
        <div className="max-h-28 min-h-0 overflow-y-auto px-2 pb-3 md:max-h-none md:flex-1">
          {historyLoading ? <div className="px-3 py-4 text-xs text-muted-foreground">Loading history…</div> : conversations.length === 0 ? <div className="px-3 py-4 text-xs text-muted-foreground">Your conversations will appear here.</div> : conversations.map((item) => (
            <div key={item.id} className={'group mb-1 flex w-full items-center gap-1 rounded-lg pr-1 text-sm transition ' + (conversationId === item.id ? 'bg-secondary text-foreground' : 'text-muted-foreground hover:bg-secondary/60 hover:text-foreground')}>
              <button type="button" onClick={() => openConversation(item.id)} className="min-w-0 flex-1 truncate px-3 py-2.5 text-left">{item.title}</button>
              <button type="button" aria-label="Delete conversation" onClick={(event) => deleteConversation(event, item.id)} className="rounded p-1 opacity-70 hover:text-red-400 md:opacity-0 md:group-hover:opacity-100"><Trash2 className="h-3.5 w-3.5" /></button>
            </div>
          ))}
        </div>
        <div className="hidden items-center gap-2 border-t border-border px-4 py-3 text-xs text-muted-foreground md:flex">
          <FileText className="h-4 w-4" /> Responses use saved AidFlow data
        </div>
      </aside>

      <div className="flex min-h-[570px] min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-border px-5 py-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary text-foreground"><Bot className="h-5 w-5" /></div>
          <div className="min-w-0">
            <p className="font-semibold text-foreground">{activeConversation?.title || 'AidFlow Assistant'}</p>
            <p className="text-xs text-muted-foreground">Answers are grounded in your profile and saved scheme data</p>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-5 sm:px-7">
          {messages.length === 0 ? (
            <div className="mx-auto flex min-h-full max-w-2xl flex-col justify-center">
              <div className="mb-6 text-center">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl border border-border bg-background text-foreground"><MessageCircle className="h-6 w-6" /></div>
                <h2 className="text-xl font-semibold tracking-tight text-foreground">What can I help you with?</h2>
                <p className="mt-2 text-sm text-muted-foreground">Ask about your eligibility, schemes, documents, or application progress.</p>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                {SUGGESTIONS.map((suggestion) => <button key={suggestion} type="button" onClick={() => sendMessage(suggestion)} disabled={loading} className="rounded-xl border border-border bg-background/60 px-4 py-3 text-left text-sm text-muted-foreground transition hover:border-primary/50 hover:text-foreground">{suggestion}</button>)}
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-3xl space-y-6">
              {messages.map((message) => (
                <div key={message.id} className={'flex gap-3 ' + (message.role === 'user' ? 'justify-end' : 'justify-start')}>
                  {message.role === 'assistant' && <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-border bg-background text-foreground"><Bot className="h-4 w-4" /></div>}
                  <div className={'max-w-[88%] min-w-0 ' + (message.role === 'user' ? 'rounded-2xl rounded-br-md bg-secondary px-4 py-3 text-foreground' : 'pt-1')}>
                    {message.role === 'user' ? <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p> : <>
                      <MarkdownContent content={message.content} />
                      {(message.metadata?.scheme_cards || []).map((scheme) => <SchemeCard key={scheme.id} scheme={scheme} />)}
                      {message.metadata?.actions?.length > 0 && <div className="mt-3 flex flex-wrap gap-2">{message.metadata.actions.map((action, index) => <Action key={action.href + '-' + index} action={action} />)}</div>}
                    </>}
                  </div>
                </div>
              ))}
              {loading && <div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" />Checking your saved information…</div>}
              <div ref={bottomRef} />
            </div>
          )}
          {error && <div role="alert" className="mx-auto mt-3 max-w-3xl rounded-lg border border-red-500/30 bg-red-500/5 px-4 py-3 text-sm text-red-300">{error}</div>}
        </div>

        <form onSubmit={(event) => { event.preventDefault(); sendMessage(); }} className="border-t border-border bg-background/40 p-4 sm:px-6">
          <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-xl border border-border bg-card p-2 focus-within:border-primary/60">
            <textarea aria-label="Message the AidFlow assistant" value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendMessage(); } }} rows={1} maxLength={4000} placeholder="Ask about schemes, eligibility, or your next steps…" className="max-h-36 min-h-10 flex-1 resize-y bg-transparent px-2 py-2 text-sm text-foreground outline-none placeholder:text-muted-foreground" />
            <button type="submit" disabled={!input.trim() || loading} aria-label="Send message" className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"><Send className="h-4 w-4" /></button>
          </div>
          <p className="mx-auto mt-2 max-w-3xl text-[11px] text-muted-foreground">Answers reflect information saved in AidFlow and may not replace official scheme guidance.</p>
        </form>
      </div>
    </section>
  );
};

export default AssistantPage;
