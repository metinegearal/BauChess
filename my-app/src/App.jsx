import { useEffect, useMemo, useState } from 'react';
import { Chess } from 'chess.js';
import { ChessBoard } from 'react-chessboard-ui';
import 'react-chessboard-ui/dist/index.css';
import EvalBar from './EvalBar';
import EvalChart from './EvalChart';
import Sidebar from './SideBar';
import { API_URL } from './api';
import './App.css';

const EMPTY = { TimePerMove: [], typeList: [], evalList: [], Pgn: '' };
const COLORS = { best: '#00a000', excellent: '#66bb44', good: '#aac000', inaccuracy: '#ffa500', mistake: '#f00000', blunder: '#800080' };

function App() {
  const [params, setParams] = useState({});
  const [review, setReview] = useState(EMPTY);
  const [boardIndex, setBoardIndex] = useState(0);
  const [evaluation, setEvaluation] = useState(0);
  const [message, setMessage] = useState('Choose a player and game date.');
  const [engineError, setEngineError] = useState('');
  const history = useMemo(() => {
    if (!review.Pgn) return [];
    try {
      const game = new Chess();
      game.loadPgn(review.Pgn);
      return game.history();
    } catch { return []; }
  }, [review.Pgn]);
  const fen = useMemo(() => {
    const board = new Chess();
    history.slice(0, boardIndex).forEach(move => board.move(move));
    return board.fen();
  }, [history, boardIndex]);

  useEffect(() => {
    const controller = new AbortController();
    if (!params.user || !params.date) return;
    async function load() {
      try {
        const response = await fetch(`${API_URL}/chart`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(params), signal: controller.signal,
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'No game found.');
        setReview(data);
        setBoardIndex(0);
        setMessage('');
      } catch (error) {
        if (error.name !== 'AbortError') { setReview(EMPTY); setMessage(error.message); }
      }
    }
    load();
    return () => controller.abort();
  }, [params]);

  useEffect(() => {
    const controller = new AbortController();
    // Briefly debounce navigation so held keys do not spawn many engines.
    const timer = setTimeout(async () => {
      try {
        const response = await fetch(`${API_URL}/eval`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ fen }), signal: controller.signal,
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Evaluation failed');
        setEvaluation(data.evaluation);
        setEngineError('');
      } catch (error) {
        if (error.name !== 'AbortError') setEngineError(error.message);
      }
    }, 200);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [fen]);

  useEffect(() => {
    const navigate = event => {
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName)) return;
      const key = event.key.toLowerCase();
      if (['arrowleft', 'a', 'arrowright', 'd'].includes(key)) {
        event.preventDefault();
        const delta = ['arrowleft', 'a'].includes(key) ? -1 : 1;
        setBoardIndex(index => Math.max(0, Math.min(history.length, index + delta)));
      }
    };
    window.addEventListener('keydown', navigate);
    return () => window.removeEventListener('keydown', navigate);
  }, [history.length]);

  const selectPly = index => setBoardIndex(Math.min(history.length, index + 1));
  return (
    <main className="app" style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
      <Sidebar onParamsChange={setParams} />
      <div>
        {message && <p role="status">{message}</p>}
        {engineError && <p role="alert">{engineError}</p>}
        <div style={{ display: 'flex', gap: 12 }}>
          <EvalBar evaluation={evaluation} />
          <ChessBoard FEN={fen} />
        </div>
        <p>Position {Math.min(boardIndex, history.length)} / {history.length}</p>
      </div>
      <div>
        <h3>Time per player move (seconds)</h3>
        <EvalChart evalData={review.TimePerMove} colorData={review.typeList.map(type => COLORS[type])}
          onSelect={index => selectPly(index * 2 + (review.UserColor === 'Black' ? 1 : 0))} />
        <h3>Evaluation per ply (centipawns, White's perspective)</h3>
        <EvalChart evalData={review.evalList} colorData={review.evalList.map((_, index) => index % 2 ? '#333' : '#ddd')}
          onSelect={selectPly} />
      </div>
    </main>
  );
}
export default App;
