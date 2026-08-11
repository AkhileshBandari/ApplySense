import { FormEvent, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { login, register } = useAuth();

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError('');

    try {
      if (isRegister) {
        await register({ username: email.split('@')[0], email, password, role: 'candidate' });
      } else {
        await login(email, password);
      }
      navigate('/');
    } catch (err) {
      setError('Authentication failed. Please check your credentials and try again.');
      console.error(err);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-darkBg px-4 text-primaryText">
      <div className="w-full max-w-md rounded-xl border border-cardBorder bg-card p-8 shadow-2xl">
        <h1 className="text-2xl font-semibold">{isRegister ? 'Create an account' : 'Welcome back'}</h1>
        <p className="mt-2 text-sm text-slate-400">Sign in to continue with ApplySense.</p>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <input
            className="w-full rounded border border-cardBorder bg-darkBg p-3"
            placeholder="Email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          <input
            className="w-full rounded border border-cardBorder bg-darkBg p-3"
            placeholder="Password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
          {error ? <p className="text-sm text-red-400">{error}</p> : null}
          <button className="w-full rounded bg-accentTeal px-4 py-3 font-semibold text-darkBg" type="submit">
            {isRegister ? 'Create account' : 'Sign in'}
          </button>
        </form>
        <p className="mt-4 text-sm text-slate-400">
          {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
          <button className="text-accentTeal" type="button" onClick={() => setIsRegister((value) => !value)}>
            {isRegister ? 'Sign in' : 'Create one'}
          </button>
        </p>
        <Link className="mt-3 inline-block text-sm text-slate-400" to="/">Continue without login</Link>
      </div>
    </div>
  );
}
