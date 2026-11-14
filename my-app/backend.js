const express = require('express');
const cors = require('cors');
const { MongoClient } = require('mongodb');
const { Chess } = require('chess.js');
const { spawn } = require('node:child_process');
const path = require('node:path');
const fs = require('node:fs');

const root = path.resolve(__dirname, '..');
if (fs.existsSync(path.join(root, '.env'))) process.loadEnvFile(path.join(root, '.env'));
const app = express();
app.use(cors({ origin: ['http://localhost:5173', 'http://127.0.0.1:5173', 'null'] }));
app.use(express.json({ limit: '32kb' }));
const client = new MongoClient(process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017', {
  serverSelectionTimeoutMS: 10000,
});
const db = client.db(process.env.MONGODB_DATABASE || 'chessDB');

app.get('/users', async (_req, res) => {
  const roster = path.resolve(root, process.env.PEOPLE_FILE || 'people.txt');
  const users = fs.existsSync(roster)
    ? fs.readFileSync(roster, 'utf8').split(/\r?\n/).map(line => line.trim()).filter(line => line && !line.startsWith('#'))
    : await db.collection('games').distinct('User');
  res.json([...new Set(users)]);
});

app.post('/eval', (req, res) => {
  const { fen } = req.body;
  try {
    if (typeof fen !== 'string' || /[\r\n]/.test(fen)) throw new Error('Invalid FEN');
    new Chess(fen);
  } catch {
    return res.status(400).json({ error: 'Invalid FEN' });
  }
  // Executable configuration is controlled by the host, never by an HTTP request.
  const engine = spawn(process.env.STOCKFISH_PATH || 'stockfish');
  let output = '';
  let done = false;
  const finish = (status, data) => {
    if (done) return;
    done = true;
    clearTimeout(timer);
    engine.kill();
    res.status(status).json(data);
  };
  const timer = setTimeout(() => finish(504, { error: 'Stockfish evaluation timed out' }), 30000);
  engine.on('error', () => finish(503, { error: 'Cannot start Stockfish; check STOCKFISH_PATH' }));
  engine.stdin.on('error', () => finish(503, { error: 'Stockfish input failed' }));
  engine.stdout.on('data', data => {
    output += data.toString();
    if (!/(?:^|\n)bestmove\s/.test(output)) return;
    const matches = [...output.matchAll(/score (cp|mate) (-?\d+)/g)];
    const score = matches.at(-1);
    if (!score) return finish(502, { error: 'No Stockfish score available' });
    const value = score[1] === 'cp' ? Number(score[2]) : 100000 * (Math.sign(Number(score[2])) || -1);
    // UCI scores are relative to the side to move; the viewer uses White's perspective.
    finish(200, { evaluation: value * (fen.split(' ')[1] === 'w' ? 1 : -1) });
  });
  engine.on('close', () => finish(502, { error: 'Stockfish exited before returning a score' }));
  engine.stdin.write(`uci\nisready\nposition fen ${fen}\ngo depth 14\n`);
});

app.post('/chart', async (req, res) => {
  const { user, date, num } = req.body;
  if (typeof user !== 'string' || typeof date !== 'string' || !Number.isInteger(num) || num < 0) {
    return res.status(400).json({ error: 'Expected user, date, and a nonnegative game index' });
  }
  const day = date.split('T')[0];
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return res.status(400).json({ error: 'Invalid date' });
  const result = await db.collection('games').find({ User: user, Date: day.replace(/-/g, '.') })
    .sort({ game_id: 1 }).skip(num).limit(1).next();
  if (!result) return res.status(404).json({ error: 'No game found for this player, date, and index' });
  const { typeList, evalList, AverageTimePerMove, TimePerMove, Pgn, UserColor } = result;
  res.json({ typeList, evalList, AverageTimePerMove, TimePerMove, Pgn, UserColor });
});

// Express 5 forwards rejected async handlers here.
app.use((error, _req, res, _next) => {
  console.error(error.message);
  res.status(503).json({ error: 'Backend request failed; check MongoDB and server logs' });
});

if (require.main === module) {
  const port = Number(process.env.PORT || 8000);
  const server = app.listen(port, '127.0.0.1', () => console.log(`Backend: http://127.0.0.1:${port}`));
  const stop = () => server.close(() => client.close().then(() => process.exit(0)));
  process.on('SIGTERM', stop);
  process.on('SIGINT', stop);
}
module.exports = app;
