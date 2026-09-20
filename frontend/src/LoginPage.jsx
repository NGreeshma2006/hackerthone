import { useState } from 'react';
import { accountRequest } from './auth';
import { ArrowRight, LockKeyhole, Mail, Store, UserRound } from 'lucide-react';

export default function LoginPage({ onLogin }) {
  const [error, setError] = useState('');
  const [signup, setSignup] = useState(false);
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    const data = new FormData(event.currentTarget);
    const email = String(data.get('email') || '').trim();
    const password = String(data.get('password') || '');
    const name = String(data.get('name') || '').trim();
    if (signup && !name) { setError('Enter your full name.'); return; }
    if (signup && password !== data.get('confirmPassword')) { setError('Passwords do not match.'); return; }
    setBusy(true); setError('');
    try {
      const user = await accountRequest(signup ? 'signup' : 'login', { email, password, ...(signup ? {name} : {}) });
      onLogin(user);
    } catch (error) { setError(error.message); }
    finally { setBusy(false); }
  }
  return <main className="login-page">
    <section className="login-intro"><div className="login-brand"><span className="login-mark">ॐ</span><span>bolistock</span></div><div className="login-copy"><p className="login-eyebrow">YOUR SHOP, IN ONE BREATH</p><h1>Good stock starts with a clear picture.</h1><p>Sign in to record sales, keep quantities accurate, and hear exactly what is left on the shelf.</p></div><div className="login-benefits"><span><Store size={18} /> Your inventory, in sync</span><span><LockKeyhole size={18} /> A private shop session</span></div></section>
    <section className="login-panel" aria-labelledby="login-title">
      <form key={signup ? 'signup' : 'login'} className="login-card" onSubmit={submit}>
        <div className="login-card-heading">
          <p>{signup ? 'WELCOME TO BOLISTOCK' : 'WELCOME BACK'}</p>
          <h2 id="login-title">{signup ? 'Create your account' : 'Sign in to BoliStock'}</h2>
          <span>{signup ? 'Tell us your name and choose your sign-in details.' : 'Use your shop account to continue.'}</span>
        </div>
        {signup && <label>Full name<div className="login-field"><UserRound size={17} /><input name="name" autoComplete="name" placeholder="Your full name" maxLength={100} required disabled={busy} /></div></label>}
        <label>Email address<div className="login-field"><Mail size={17} /><input name="email" type="email" autoComplete="email" placeholder="you@shop.com" maxLength={254} required disabled={busy} /></div></label>
        <label>Password<div className="login-field"><LockKeyhole size={17} /><input name="password" type="password" autoComplete={signup ? 'new-password' : 'current-password'} placeholder={signup ? 'At least 8 characters' : 'Enter your password'} minLength={signup ? 8 : 1} maxLength={128} required disabled={busy} /></div></label>
        {signup && <label>Confirm password<div className="login-field"><LockKeyhole size={17} /><input name="confirmPassword" type="password" autoComplete="new-password" placeholder="Enter your password again" minLength={8} maxLength={128} required disabled={busy} /></div></label>}
        {error && <p className="login-error" role="alert">{error}</p>}
        <button className="login-submit" type="submit" disabled={busy}>{busy ? 'Please wait...' : signup ? 'Create account' : 'Sign in'} <ArrowRight size={18} /></button>
        <p className="login-note">{signup ? 'Already have an account?' : 'New to BoliStock?'}{' '}
          <button className="login-switch" type="button" disabled={busy} onClick={() => {setSignup(!signup); setError('');}}>{signup ? 'Sign in' : 'Sign up'}</button>
        </p>
      </form>
    </section>
  </main>;
}
