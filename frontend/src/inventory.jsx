import { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import { X } from 'lucide-react';
import './inventory.css';
import { useVoice, languages } from './useVoice';
import { getReorderLevel, getStockStatus } from './stockMath';

const API = import.meta.env.VITE_API_URL || '/api';
async function request(path, body) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch(`${API}${path}`, { signal: controller.signal, ...(body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {}) });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      const error = new Error(typeof data.detail === 'string' ? data.detail : 'Cannot complete this request. Please check the inventory server.');
      error.status = response.status;
      throw error;
    }
    return await response.json();
  } finally { clearTimeout(timer); }
}
const colors = ['#f2c94c', '#ea8a55', '#79a982', '#a89cd9', '#cf756d'];
function saved(key, fallback) { try { return JSON.parse(localStorage.getItem(key)) || fallback; } catch { return fallback; } }

export function useInventory() {
  const [stock, setStock] = useState([]), [recentActivity, setActivity] = useState([]);
  const lowStockIds = useRef(new Set());
  const [activeNav, setActiveNav] = useState('Today'), [dialog, setDialog] = useState(null);
  const [settings, setSettings] = useState(() => saved('boli-settings', { shop: 'Sharma Kirana', location: 'Jaipur · Shop 01', owner: 'Rajesh Sharma' }));
  const [filter, setFilter] = useState('all'), [search, setSearch] = useState(''), [command, setCommand] = useState('');
  const [error, setError] = useState('');
  const voice = useVoice({ request, refresh, open, command, setCommand });
  async function refresh() {
    try {
      const products = await request('/products');
      const nextStock = products.map((p, i) => {
        const reorderAt = getReorderLevel(p.minimum_stock);
        return { ...p, stock: p.current_stock, reorderAt, unit: p.default_unit, localName: p.category, accent: colors[i % colors.length], initials: p.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase(), status: getStockStatus(p.current_stock, reorderAt), change: 0 };
      });
      const nextLowIds = new Set(nextStock.filter(p => p.status === 'low').map(p => p.id));
      const newlyLow = nextStock.filter(p => nextLowIds.has(p.id) && !lowStockIds.current.has(p.id));
      lowStockIds.current = nextLowIds;
      setStock(nextStock);
      if (newlyLow.length) {
        const items = newlyLow.map(p => `${p.name} (${p.stock} ${p.unit})`).join(', ');
        toast.warning(`Running low: ${items}`, { description: 'Restock before the item runs out.' });
      }
      setActivity(await request('/activity'));
      setError('');
    } catch { setError('Cannot reach the inventory server. Start the backend and retry.'); }
  }
  useEffect(() => { refresh(); }, []);
  function open(title, item) { setDialog({ title, item }); }
  function navigate(label) {
    setActiveNav(label);
    if (label === 'Today') { setDialog(null); window.scrollTo({ top: 0, behavior: 'smooth' }); }
    else if (label === 'My stock') { setFilter('all'); setSearch(''); document.getElementById('stock-section')?.scrollIntoView({ behavior: 'smooth' }); }
    else open(label);
  }
  function exportStock() {
    const cell = value => '"' + String(value).replace(/^[=+@-]/, "'$&").replaceAll('"', '""') + '"';
    const csv = [['Item', 'Category', 'Stock', 'Unit', 'Reorder at'], ...stock.map(p => [p.name, p.category, p.stock, p.unit, p.reorderAt])].map(row => row.map(cell).join(',')).join('\r\n');
    const url = URL.createObjectURL(new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a'); link.href = url; link.download = `bolistock-${new Date().toISOString().slice(0, 10)}.csv`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return { stock, recentActivity, activeNav, navigate, dialog, open, close: () => setDialog(null), ...voice, settings, saveSettings: value => { setSettings(value); localStorage.setItem('boli-settings', JSON.stringify(value)); }, filter, setFilter, search, setSearch, command, setCommand, error, refresh, exportStock };
}

export function InventoryDialog({ inventory: inv }) {
  const { dialog, stock } = inv;
  const [pending, setPending] = useState(false), [message, setMessage] = useState(''), [story, setStory] = useState(null), [selected, setSelected] = useState('');
  const ref = useRef(null);
  useEffect(() => {
    setMessage(''); setStory(null); setSelected(dialog?.item?.id || stock[0]?.id || '');
    if (!dialog) return;
    ref.current?.showModal();
    if (dialog.title === 'StockStory') {
      let cancelled = false;
      request(`/products/${encodeURIComponent(dialog.item.id)}/story`).then(data => { if (!cancelled) setStory(data); }).catch(e => { if (!cancelled) setMessage(e.message); });
      return () => { cancelled = true; };
    }
  }, [dialog]);
  if (!dialog) return null;
  const title = dialog.title;
  const item = stock.find(p => p.id === selected);
  async function submit(event) {
    event.preventDefault(); if (pending) return;
    setPending(true); setMessage('');
    const data = Object.fromEntries(new FormData(event.currentTarget));
    try {
      if (title === 'Settings') inv.saveSettings(data);
      else if (title === 'Language') inv.setLanguage(data.language);
      else if (data.mode === 'new') {
        await request('/products', { id: crypto.randomUUID(), name: data.name.trim(), category: data.category.trim() || 'General', default_unit: data.unit.trim(), minimum_stock: Number(data.minimum) });
        await inv.refresh();
      } else {
        await request('/transactions', { product_id: selected, quantity: Number(data.quantity), unit: item.unit, transaction_type: data.type, source: 'manual' });
        await inv.refresh();
      }
      toast.success('Saved successfully'); inv.close();
    } catch (e) { setMessage(e.message); } finally { setPending(false); }
  }
  const activity = <div className="dialog-activity">{inv.recentActivity.length ? inv.recentActivity.map(a => <div className="activity-item" key={a.id}><div className="activity-copy"><strong>{a.title}</strong><span>{a.detail}</span></div><time>{a.time}</time></div>) : <p>No transactions yet.</p>}</div>;
  const productForm = <form onSubmit={submit} className="entry-form"><input type="hidden" name="mode" value="new" /><label>Item name<input name="name" required maxLength={100} pattern=".*\S.*" /></label><label>Category<input name="category" defaultValue="General" /></label><label>Stock unit<input name="unit" required defaultValue="bags" pattern=".*\S.*" /></label><label>Reorder at<input name="minimum" type="number" min="0" step="any" defaultValue="10" required /></label><button className="plus-button" disabled={pending}>Create item</button></form>;
  return <dialog ref={ref} className="inventory-dialog" onCancel={inv.close} onClick={e => { if (e.target === ref.current) inv.close(); }}><div className="dialog-heading"><h2>{title === "Boli’s answer" ? inv.voiceText.answer : title === "Voice entry" ? inv.voiceText.request : title}</h2><button className="icon-button" aria-label="Close" onClick={inv.close}><X size={18} /></button></div>
    {message && <p role="alert">{message}</p>}
    {title === 'Quick add' && <><form onSubmit={submit} className="entry-form"><label>Item<select value={selected} onChange={e => setSelected(e.target.value)} required>{stock.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label><label>Movement<select name="type"><option value="PURCHASE">Stock received</option><option value="SALE">Sale</option><option value="DAMAGE">Damaged</option><option value="RETURN">Customer return</option></select></label><label>Quantity ({item?.unit || 'units'})<input name="quantity" type="number" min="0.001" step="any" required /></label><button className="plus-button" disabled={pending || !item}>{pending ? 'Saving…' : 'Save entry'}</button></form><details open={!stock.length}><summary>Create a new item</summary>{productForm}</details></>}
    {title === 'Item catalog' && <><div className="catalog-list">{stock.map(p => <button key={p.id} className="catalog-item" onClick={() => inv.open('StockStory', p)}>{p.name}<span>{p.stock} {p.unit}</span></button>)}</div><details><summary>Create a new item</summary>{productForm}</details></>}
    {title === 'StockStory' && (story ? <><h3>{story.product_name}</h3><p>{story.explanation}</p>{story.timeline.map((t, i) => <div className="activity-item" key={i}>{t.transaction_type} · {t.quantity} {t.unit}<time>{new Date(t.timestamp).toLocaleString()}</time></div>)}<button className="plus-button" onClick={() => inv.open('Quick add', dialog.item)}>Add movement</button></> : !message && <p>Loading history…</p>)}
    {title === 'Sales & buys' && <>{activity}<button className="plus-button" onClick={() => inv.open('Quick add')}>Record movement</button></>}
    {(title === 'Notifications' || title === 'Insights') && <>{stock.filter(p => p.status === 'low').length === 0 && <p>No items need reordering.</p>}{stock.filter(p => p.status === 'low').map(p => <button className="catalog-item" key={p.id} onClick={() => inv.open('Quick add', p)}>{p.name}<span>{p.stock} {p.unit} · below reorder level of {p.reorderAt}</span></button>)}{title === 'Insights' && <p>{stock.length} items tracked · {stock.filter(p => p.status === 'healthy').length} above their reorder level.</p>}</>}
    {title === 'Reports' && <><p>Current inventory: {stock.length} items. {stock.filter(p => p.status === 'low').length} need reordering.</p><button className="outline-button" onClick={inv.exportStock}>Download stock report (CSV)</button><h3>Stock movements</h3>{activity}</>}
    {title === 'Settings' && <form className="entry-form" onSubmit={submit}>{[['shop', 'Shop name'], ['location', 'Location'], ['owner', 'Owner']].map(([name, label]) => <label key={name}>{label}<input name={name} defaultValue={inv.settings[name]} required pattern=".*\S.*" /></label>)}<button className="plus-button">Save settings</button></form>}
    {title === 'Language' && <form className="entry-form" onSubmit={submit}><label>Voice input language<select name="language" defaultValue={inv.language} disabled={inv.busy}>{Object.keys(languages).map(l => <option key={l}>{l}</option>)}</select></label><p>{inv.voiceText.languageHelp}</p><button className="plus-button" disabled={inv.busy}>Save language</button></form>}
    {title === 'Help' && <><p>Tap the microphone and allow microphone access, or type in Ask Boli.</p><p>Try “Add 3 bags of rice”, “Sold 2 bags of rice”, or “What should I reorder?”</p><p>Use Quick add for exact quantities. Select an item to see its history. Reports downloads your current inventory as CSV.</p><button className="plus-button" onClick={() => inv.open('Voice entry')}>Type an entry</button></>}
    {title === 'Voice entry' && <form className="entry-form" onSubmit={e => { e.preventDefault(); inv.runCommand(); }}><p>{inv.voiceText.unavailable}</p><label>{inv.voiceText.request}<input value={inv.command} onChange={e => inv.setCommand(e.target.value)} placeholder={inv.voiceText.ready} required /></label><button className="plus-button" disabled={inv.busy}>{inv.busy ? inv.voiceText.processing : inv.voiceText.submit}</button><p role="status">{inv.transcript}</p></form>}
    {title === 'Boli’s answer' && <p style={{ whiteSpace: 'pre-line' }}>{dialog.item.answer}</p>}
  </dialog>;
}
