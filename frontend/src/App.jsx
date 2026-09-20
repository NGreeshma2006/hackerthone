import { useMemo } from "react";
import { useInventory, InventoryDialog } from "./inventory.jsx";
import { Toaster } from "sonner";
import {
  Bell,
  ChevronDown,
  CircleHelp,
  ClipboardList,
  Command,
  Package,
  Download,
  FileText,
  Gauge,
  Globe2,
  Home as HomeIcon,
  Languages,
  LayoutGrid,
  Mic,
  MoreHorizontal,
  PackageCheck,
  Plus,
  RefreshCw,
  Search,
  Settings2,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Volume2,
  WandSparkles,
  X,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import { getStockFill, getStockStatus } from "./stockMath";



const navItems = [
  { label: "Today", hindi: "आज", icon: HomeIcon },
  { label: "My stock", hindi: "मेरा स्टॉक", icon: Package },
  { label: "Sales & buys", hindi: "लेन-देन", icon: RefreshCw },
  { label: "Insights", hindi: "नज़र", icon: Gauge },
];


export default function Home() {
  const inventory = useInventory();
  const { stock, activeNav, navigate, language, isListening, transcript, filter, setFilter,
    search, setSearch, command, setCommand, startListening, stopListening, runCommand,
    recentActivity, open, exportStock, settings, error, refresh, busy, voiceText, recognizedText, replayResponse, isSpeaking } = inventory;
  const lowCount = stock.filter((item) => item.status === "low").length;
  const visibleStock = useMemo(() => {
    return stock.filter((item) => {
      const matchesFilter = filter === "all" || item.status === "low";
      const query = search.toLowerCase();
      return matchesFilter && `${item.name} ${item.localName}`.toLowerCase().includes(query);
    });
  }, [filter, search, stock]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div className="brand-mark"><span>ॐ</span></div>
          <div>
            <div className="brand-name">bolistock</div>
            <div className="brand-tag">suno · samjho · sambhalo</div>
          </div>
        </div>

        <div className="shop-switcher">
          <div className="shop-avatar">S</div>
          <div className="shop-copy"><strong>{settings.shop}</strong><span>{settings.location}</span></div>
          <ChevronDown size={16} />
        </div>

        <nav className="side-nav" aria-label="Main navigation">
          <div className="nav-label">YOUR SHOP <span>आपकी दुकान</span></div>
          {navItems.map(({ label, hindi, icon: Icon }) => (
            <button key={label} aria-label={label} className={`nav-item ${activeNav === label ? "active" : ""}`} onClick={() => navigate(label)}>
              <Icon size={18} strokeWidth={activeNav === label ? 2.4 : 1.8} />
              <span>{label}</span>
              <em>{hindi}</em>
              {label === "Today" && <span className="nav-dot" />}
            </button>
          ))}
          <div className="nav-label second">TOOLS <span>सहूलियत</span></div>
          <button className="nav-item" onClick={() => navigate("Item catalog")}><LayoutGrid size={18} /><span>Item catalog</span></button>
          <button className="nav-item" onClick={() => navigate("Reports")}><FileText size={18} /><span>Reports</span></button>
        </nav>

        <div className="sidebar-bottom">
          <div className="tip-card">
            <div className="tip-icon"><Sparkles size={15} /></div>
            <div><strong>Small tip</strong><p>Say “what is low?” anytime.</p></div>
          </div>
          <button className="nav-item muted" onClick={() => open("Settings")}><Settings2 size={18} /><span>Settings</span></button>
          <div className="profile-row"><div className="profile-avatar">RS</div><div><strong>{settings.owner}</strong><span>Owner</span></div><MoreHorizontal size={17} /></div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb"><span>Today</span><span className="slash">/</span><strong>{activeNav === "Today" ? `Good morning, ${settings.owner.split(" ")[0]}` : activeNav}</strong></div>
          <div className="top-actions">
            <button className="lang-pill" onClick={() => open("Language")}><Languages size={16} /><span>{language}</span><ChevronDown size={14} /></button>
            <button className="icon-button" aria-label="Help" onClick={() => open("Help")}><CircleHelp size={18} /></button>
            <button className="icon-button has-badge" aria-label="Notifications" onClick={() => open("Notifications")}><Bell size={18} />{lowCount > 0 && <span className="badge-dot" />}</button>
          </div>
        </header>

        {error && <div role="alert" className="connection-error">{error} <button onClick={refresh}>Retry</button></div>}
        <section className="welcome-row">
          <div><p className="eyebrow">{new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric" }).toUpperCase()}</p><h1>Your shop, <span>in one breath.</span></h1><p className="lede">Speak naturally. We’ll keep the shelves, numbers and next steps in sync.</p></div>
          <button className="outline-button" onClick={() => exportStock()}><Download size={16} /> Share today’s view</button>
        </section>

        <section className={`voice-card ${isListening ? "is-listening" : ""}`}>
          <div className="voice-copy">
            <div className="voice-kicker"><span className="pulse-dot" /> VOICE ENTRY · आवाज़ से एंट्री</div>
            <h2>What happened in<br /><i>your shop?</i></h2>
            <p>Tell BoliStock what came in or went out.<br />No forms. No hunting through menus.</p>
            <div className="language-note"><Globe2 size={15} /> Listening in {language.toLowerCase()}</div>
          </div>
          <div className="voice-center">
            <div className="waveform" aria-hidden="true">{Array.from({ length: 22 }).map((_, index) => <span key={index} style={{ height: `${18 + ((index * 17) % 34)}px` }} className={isListening ? "wave-active" : ""} />)}</div>
            <button className="speak-button" onClick={startListening} disabled={busy} aria-label={isListening ? voiceText.stop : voiceText.tap} aria-pressed={isListening}><Mic size={32} strokeWidth={2.2} /><span>{busy ? voiceText.processing : isListening ? voiceText.listening : voiceText.tap}</span></button>
            <div className="transcript"><button className="response-speaker" onClick={replayResponse} disabled={busy || isListening} aria-label={voiceText.play} aria-pressed={isSpeaking}><Volume2 size={14} /></button><span role="status">{transcript}</span></div>{recognizedText && <div className="recognized-text">{voiceText.heard}: {recognizedText}</div>}
          </div>
          <div className="voice-example"><div className="example-label">IT UNDERSTANDS</div><div className="phrase">“Aaj 3 bori<br />toor dal aayi”</div><div className="translation">आज 3 बोरी तूर दाल आई</div><div className="understood-row"><span>+3</span><span>bags</span><span>Toor dal</span></div></div>
        </section>

        <div className="section-heading"><div><p className="eyebrow">YOUR SHELVES · आपकी शेल्फ</p><h2>Stock at a glance <span>({stock.length} items)</span></h2></div><div className="heading-actions"><div className="search-box"><Search size={16} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Find an item…" /></div><button className="plus-button" onClick={() => open("Quick add")}><Plus size={17} /> Quick add</button></div></div>

        <div className="filter-row"><div className="filter-tabs"><button className={filter === "all" ? "selected" : ""} onClick={() => setFilter("all")}>All items <b>{stock.length}</b></button><button className={filter === "low" ? "selected low-tab" : ""} onClick={() => setFilter("low")}><span className="tiny-alert" />Running low <b>{lowCount}</b></button></div><span className="updated-label"><span className="green-dot" /> {error ? "Connection unavailable" : "Synced with your shop"}</span></div>

        <div className="stock-grid" id="stock-section">{visibleStock.map((item) => (
          <button className="stock-card" key={item.id} onClick={() => open("StockStory", item)}>
            <div className="stock-card-top"><div className="item-icon" style={{ background: item.accent }}>{item.initials}</div><div className={`status-chip ${item.status}`}>{item.status === "low" ? "Reorder soon" : "In good shape"}</div><MoreHorizontal size={16} className="more-icon" /></div>
            <div className="item-name">{item.name}<small>{item.localName}</small></div>
            <div className="stock-number"><strong>{item.stock}</strong><span>{item.unit}</span></div>
            <div className="stock-meter"><span style={{ width: `${getStockFill(item.stock, item.reorderAt)}%`, background: getStockStatus(item.stock, item.reorderAt) === "low" ? "#eb8659" : item.accent }} /></div>
            <div className="stock-card-bottom"><span>Reorder at {item.reorderAt} {item.unit}</span><span className={item.change < 0 ? "down" : "up"}>{item.change > 0 ? <TrendingUp size={13} /> : <TrendingDown size={13} />}{Math.abs(item.change)}%</span></div>
          </button>
        ))}</div>
        {visibleStock.length === 0 && <p className="empty-stock">{search || filter === "low" ? "No matching items." : "No products yet. Use Quick add to create your first item."}</p>}

        <section className="lower-grid">
          <div className="activity-panel"><div className="panel-heading"><div><p className="eyebrow">JUST NOW · अभी</p><h2>Recent activity</h2></div><button className="text-button" onClick={() => navigate("Sales & buys")}>See all <span>→</span></button></div><div className="activity-list">{recentActivity.slice(0, 3).map((entry) => <div className="activity-item" key={entry.id}><div className={`activity-icon ${entry.color}`}>{entry.type === "in" ? <TrendingUp size={16} /> : <TrendingDown size={16} />}</div><div className="activity-copy"><strong>{entry.title}</strong><span>{entry.detail}</span></div><time>{entry.time}</time></div>)}</div></div>
          <div className="ask-panel"><div className="ask-orb"><WandSparkles size={19} /></div><div><p className="eyebrow">ASK BOLI · पूछिए</p><h2>Have a stock question?</h2><p className="ask-sub">Ask in your own words. Boli will look at your actual stock.</p></div><div className="suggestion-row"><button onClick={() => setCommand("What should I reorder today?")}>What should I reorder?</button><button onClick={() => setCommand("How much rice is left?")}>How much rice is left?</button></div><div className="command-box"><Command size={16} /><input value={command} onChange={(event) => setCommand(event.target.value)} onKeyDown={(event) => event.key === "Enter" && runCommand()} placeholder="Type or ask something…" /><button onClick={() => runCommand()} disabled={busy} aria-label="Ask"><Zap size={16} /></button></div></div>
        </section>

        <footer className="main-footer"><span><PackageCheck size={15} /> Stock calm, one conversation at a time.</span><span>Built for dukandars · दुकानदारों के लिए</span></footer>
      </main>
      <Toaster richColors position="bottom-right" /><InventoryDialog inventory={inventory} />
      {isListening && <button className="listening-bar" onClick={() => { stopListening(); }}><span className="bar-mic"><Mic size={16} /></span><span><strong>{voiceText.listening}</strong> · {voiceText.stop}</span><X size={16} /></button>}
    </div>
  );
}
