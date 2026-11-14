import { useEffect, useState } from 'react';
import { API_URL } from './api';

export default function Sidebar({ onParamsChange }) {
  const [users, setUsers] = useState([]);
  const [user, setUser] = useState('');
  const now = new Date();
  const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  const [date, setDate] = useState(today);
  const [num, setNum] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_URL}/users`, { signal: controller.signal })
      .then(response => response.ok ? response.json() : [])
      .then(setUsers).catch(() => {});
    return () => controller.abort();
  }, []);
  useEffect(() => { onParamsChange({ user, date, num }); }, [user, date, num, onParamsChange]);
  return (
    <aside style={{ width: 240, padding: 16 }}>
      <h2>BauChess</h2>
      <label>Chess.com username
        <input list="players" value={user} onChange={event => { setUser(event.target.value); setNum(0); }} />
      </label>
      <datalist id="players">{users.map(name => <option key={name} value={name} />)}</datalist>
      <label>Game date
        <input type="date" value={date} max={today} onChange={event => { setDate(event.target.value); setNum(0); }} />
      </label>
      <label>Game index (starts at 0)
        <input type="number" min={0} step={1} value={num} onChange={event => setNum(Math.max(0, Number(event.target.value)))} />
      </label>
      <p>Use the arrow keys or A/D to move through a game.</p>
    </aside>
  );
}
