import { useState } from 'react';
import { ArrowRight, LockKeyhole, Mail, Store } from 'lucide-react';

export default function LoginPage({ onLogin }) {
  const [error, setError] = useState('');
  function submit(event) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const email = String(data.get('email') || '').trim();
    const password = String(data.get('password') || '');
    if (!email || !password) { setError('Enter your email and password to continue.'); return; }
    onLogin({ email, name: email.split('@')[0] });
  }
  return <main className="login-page">
    <section className="login-intro"><div className="login-brand"><span className="login-mark">ॐ</span><span>bolistock</span></div><div className="login-copy"><p className="login-eyebrow">YOUR SHOP, IN ONE BREATH</p><h1>Good stock starts with a clear picture.</h1><p>Sign in to record sales, keep quantities accurate, and hear exactly what is left on the shelf.</p></div><div className="login-benefits"><span><Store size={18} /> Your inventory, in sync</span><span><LockKeyhole size={18} /> A private shop session</span></div></section>
    <section className="login-panel" aria-labelledby="login-title"><form className="login-card" onSubmit={submit}><div className="login-card-heading"><p>WELCOME BACK</p><h2 id="login-title">Sign in to BoliStock</h2><span>Use your shop account to continue.</span></div><label>Email address<div className="login-field"><Mail size={17} /><input name="email" type="email" autoComplete="email" placeholder="you@shop.com" required /></div></label><label>Password<div className="login-field"><LockKeyhole size={17} /><input name="password" type="password" autoComplete="current-password" placeholder="Enter your password" minLength="4" required /></div></label>{error && <p className="login-error" role="alert">{error}</p>}<button className="login-submit" type="submit">Sign in <ArrowRight size={18} /></button><p className="login-note">Your inventory opens only after you sign in.</p></form></section>
  </main>;
}
