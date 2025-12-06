import React from 'https://esm.sh/react@18.3.1';
import { createRoot } from 'https://esm.sh/react-dom@18.3.1/client';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(React.createElement);

const canvas = document.getElementById('sim');
const ctx = canvas.getContext('2d');
const Howl = window.Howl;

function makeSound(src, opts = {}) {
  if (Howl) return new Howl({ src: [src], ...opts });
  return {
    play() {},
    stop() {},
    playing() { return false; },
  };
}

const sounds = {
  fire: makeSound('https://cdn.pixabay.com/download/audio/2022/03/15/audio_5b15144f33.mp3?filename=fire-crackling-1-6742.mp3', { loop: true, volume: 0.35 }),
  alarm: makeSound('https://cdn.pixabay.com/download/audio/2022/03/15/audio_206a695f39.mp3?filename=alarm-6107.mp3', { loop: true, volume: 0.25 }),
  bomb: makeSound('https://cdn.pixabay.com/download/audio/2022/03/15/audio_7c3dcbfdf3.mp3?filename=explosion-6055.mp3', { volume: 0.7 }),
  quake: makeSound('https://cdn.pixabay.com/download/audio/2022/03/15/audio_0dc992d7b1.mp3?filename=rumble-6054.mp3', { volume: 0.4 }),
};

const initialHud = {
  alive: 0,
  escaped: 0,
  hazards: 0,
  sensors: '0/0',
  status: 'Working',
  target: 'Camera free · click a person to follow',
  scenario: 'Electrical Fire (Server Row)',
  evacTime: '--',
  congestion: '0/0',
};

let setHudState = null;

function App({ onReset, onBomb, onQuake, onFire, onScenario, scenariosList }) {
  const [hud, setHud] = React.useState(initialHud);
  const [selectedScenario, setSelectedScenario] = React.useState(currentScenario.id);
  setHudState = (next) => setHud((prev) => ({ ...prev, ...next }));

  return html`
    <div class="overlay">
      <div class="hud">
        <div class="hud__stats">
          <div class="chips">
            <span class="chip">Alive: ${hud.alive}</span>
            <span class="chip">Escaped: ${hud.escaped}</span>
            <span class="chip">Hazards: ${hud.hazards}</span>
            <span class="chip">Sensors: ${hud.sensors}</span>
            <span class="chip">Scenario: ${hud.scenario}</span>
            <span class="chip">Status: ${hud.status}</span>
            <span class="chip">Congestion: ${hud.congestion}</span>
            <span class="chip">Evac: ${hud.evacTime}</span>
          </div>
          <div class="controls">
            WASD pan · Scroll zoom · Click follow · Space free camera · B bomb · E quake · F fire · R reset · H heatmap · V sensors · G guidance · Shift+click drop sensor · Right-click target disaster (1=fire, 2=bomb, 3=quake)
          </div>
          <div class="controls">
            Scenario:
            <select value=${selectedScenario} onChange=${(e) => { setSelectedScenario(e.target.value); onScenario(e.target.value); }}>
              ${scenariosList.map((s) => html`<option value=${s.id}>${s.name}</option>`)}
            </select>
            <span style=${{ color: 'var(--muted)', marginLeft: '6px' }}>
              ${scenariosList.find((s) => s.id === selectedScenario)?.desc || ''}
            </span>
          </div>
        </div>
        <div class="hud__actions">
          <button class="btn btn-secondary" onClick=${toggleHeatmap}>Heatmap (H)</button>
          <button class="btn btn-secondary" onClick=${toggleSensors}>Sensors (V)</button>
          <button class="btn btn-secondary" onClick=${toggleRoutes}>Guidance (G)</button>
          <button class="btn btn-secondary" onClick=${onBomb}>Bomb</button>
          <button class="btn btn-secondary" onClick=${onQuake}>Quake</button>
          <button class="btn btn-secondary" onClick=${onFire}>Fire</button>
          <button class="btn btn-primary" onClick=${onReset}>Reset</button>
        </div>
      </div>
      <div class="target-info">${hud.target}</div>
    </div>
  `;
}

const root = createRoot(document.getElementById('app'));

const ROWS = 40;
const COLS = 50;
const TOTAL_PEOPLE = 60;

const BASE_TILE_W = 32;
const BASE_TILE_H = 16;

let screenWidth = canvas.width;
let screenHeight = canvas.height;

const Colors = {
  FLOOR: '#8c8c96',
  WALL_TOP: '#464751',
  WALL_SIDE: '#2f3038',
  RUBBLE: '#3c3732',
  EXIT: '#32ff74',
  FIRE: '#ff7800',
  SMOKE: '#9aa3ad',
  SKINS: ['#ffdcb1', '#b48a78', '#8d5524'],
  SHIRTS: ['#7070d6', '#d67a7a', '#68b96b', '#d4c66b'],
};

const FLOOR = 0;
const WALL = 1;
const EXIT = 2;
const RUBBLE = 3;
const workingThoughts = ['Working...', 'Crunching numbers', 'Pulling reports', 'Fixing bugs', 'On a call'];
const panicThoughts = ['Where is the exit?!', 'I can\'t see!', 'Stay low!', 'Move move move!', 'Smoke everywhere!'];
const leaderThoughts = ['Follow me!', 'This way!', 'I see a path!', 'Keep moving!'];
const hesitantThoughts = ['Is it real?', 'Should I run?', 'Wait—alarm?', 'Hold on...'];
const aidThoughts = ['Helping you!', 'Lean on me!', 'Stay together!', 'I got you!'];
let evacStarted = false;
const sensorNodes = [];
let overlayState = { showHeatmap: false, showSensors: true, showRoutes: true };
let heatGrid = [];
let smokeGrid = [];
const FIRE_DECAY = 6; // intensity decay per second
const FIRE_SPREAD = 0.14; // base spread chance multiplier
const SMOKE_DECAY = 0.95;
const scenarios = [
  {
    id: 'electrical',
    name: 'Electrical Fire (Server Row)',
    desc: 'High heat, directional wind along aisles, sprinklers late.',
    seeds: [
      { r: Math.floor(ROWS * 0.52), c: Math.floor(COLS * 0.32), intensity: 42 },
      { r: Math.floor(ROWS * 0.48), c: Math.floor(COLS * 0.36), intensity: 36 },
    ],
    suppression: [
      { t: 18, radius: 6, power: 0.55 },
      { t: 30, radius: 8, power: 0.75 },
    ],
    wind: { dx: 0.4, dy: 0 },
    smokeBoost: 1.2,
  },
  {
    id: 'chemical',
    name: 'Chemical Spill (Lab)',
    desc: 'Dense smoke, slower heat, early foam deployment.',
    seeds: [
      { r: Math.floor(ROWS * 0.68), c: Math.floor(COLS * 0.28), intensity: 32 },
      { r: Math.floor(ROWS * 0.70), c: Math.floor(COLS * 0.24), intensity: 30 },
    ],
    suppression: [
      { t: 12, radius: 7, power: 0.6 },
      { t: 24, radius: 10, power: 0.8 },
    ],
    wind: { dx: -0.25, dy: 0.1 },
    smokeBoost: 1.8,
  },
  {
    id: 'kitchen',
    name: 'Kitchen Grease Fire',
    desc: 'Fast ignition, hot but localized, quick suppression.',
    seeds: [{ r: Math.floor(ROWS * 0.24), c: Math.floor(COLS * 0.62), intensity: 44 }],
    suppression: [{ t: 10, radius: 5, power: 0.7 }],
    wind: { dx: 0.05, dy: 0.05 },
    smokeBoost: 1.1,
  },
];
let currentScenario = scenarios[0];
let scenarioTimers = [];
let occupancyGrid = [];
let metrics = {
  startedAt: performance.now(),
  evacStartedAt: null,
  evacEndedAt: null,
  congestionNow: 0,
  congestionMax: 0,
};
let mockSocket = null;
const windState = { dx: 0, dy: 0, mag: 0 };
let sensorIdCounter = 0;
let feedAttached = false;
let placementMode = 'fire'; // fire | bomb | quake

function getHeat(r, c) {
  return heatGrid?.[r]?.[c] || 0;
}

function getSmoke(r, c) {
  return smokeGrid?.[r]?.[c] || 0;
}

function hotspotKeys(hazardMap, threshold = 5) {
  const s = new Set();
  for (const [k, v] of hazardMap) {
    if (v.intensity >= threshold) s.add(k);
  }
  return s;
}

class Camera {
  constructor() {
    this.x = 0;
    this.y = 0;
    this.zoom = 1;
    this.target = null;
    this.shake = 0;
    this.tileW = BASE_TILE_W;
    this.tileH = BASE_TILE_H;
    this.centerOnMap();
  }

  centerOnMap() {
    this.x = (COLS * this.tileW) / 2 - screenWidth / 2;
    this.y = -100;
  }

  applyZoom(amount) {
    const oldZoom = this.zoom;
    this.zoom = Math.min(2.5, Math.max(0.5, this.zoom + amount));
    this.tileW = BASE_TILE_W * this.zoom;
    this.tileH = BASE_TILE_H * this.zoom;
    if (this.zoom !== oldZoom) {
      this.x *= this.zoom / oldZoom;
      this.y *= this.zoom / oldZoom;
    }
  }

  move(dx, dy) {
    this.target = null;
    this.x += dx;
    this.y += dy;
  }

  update() {
    if (this.shake > 0) {
      this.x += randInt(-this.shake, this.shake);
      this.y += randInt(-this.shake, this.shake);
      this.shake *= 0.9;
    }

    if (this.target) {
      const tx = this.target.exactC * this.tileW;
      const ty = this.target.exactR * this.tileH;
      const desiredX = tx - screenWidth / 2;
      const desiredY = ty - screenHeight / 2;
      this.x += (desiredX - this.x) * 0.1;
      this.y += (desiredY - this.y) * 0.1;
    }
  }

  toScreen(r, c, z = 0) {
    const x = c * this.tileW;
    const y = r * this.tileH;
    return { x: x - this.x, y: y - this.y - z * this.zoom };
  }
}

let camera = null;

class Pathfinder {
  findPath(start, goal, maze, hazards) {
    const open = [{ node: start, g: 0, f: 0 }];
    const cameFrom = new Map();
    const gScore = new Map([[key(start), 0]]);
    const goalKey = key(goal);

    while (open.length) {
      open.sort((a, b) => a.f - b.f || a.g - b.g);
      const current = open.shift();
      const cKey = key(current.node);
      if (cKey === goalKey) return this.reconstruct(cameFrom, current.node);

      const [r, c] = current.node;
      const neighbors = [
        [r - 1, c],
        [r + 1, c],
        [r, c - 1],
        [r, c + 1],
      ];

      for (const [nr, nc] of neighbors) {
        if (nr < 0 || nc < 0 || nr >= ROWS || nc >= COLS) continue;
        if (maze[nr][nc] === WALL) continue;

        const neighborKey = key([nr, nc]);
        let cost = 1;
        if (maze[nr][nc] === RUBBLE) cost = 8;
        if (hazards.has(neighborKey)) cost += 50;

        const tentative = current.g + cost;
        const prevG = gScore.get(neighborKey);
        if (prevG === undefined || tentative < prevG) {
          cameFrom.set(neighborKey, current.node);
          gScore.set(neighborKey, tentative);
          const h = Math.abs(nr - goal[0]) + Math.abs(nc - goal[1]);
          open.push({ node: [nr, nc], g: tentative, f: tentative + h });
        }
      }
    }
    return [];
  }

  reconstruct(cameFrom, current) {
    const path = [];
    let cursorKey = key(current);
    while (cameFrom.has(cursorKey)) {
      path.push(current);
      current = cameFrom.get(cursorKey);
      cursorKey = key(current);
    }
    path.reverse();
    return path;
  }
}

const pathfinder = new Pathfinder();

class Person {
  constructor(id, r, c) {
    this.id = id;
    this.r = r;
    this.c = c;
    this.exactR = r;
    this.exactC = c;
    this.colorSkin = pick(Colors.SKINS);
    this.colorShirt = pick(Colors.SHIRTS);

    this.alive = true;
    this.escaped = false;
    this.health = 100;
    this.injured = false;
    this.stunTimer = 0;

    this.path = [];
    this.pathIndex = 0;
    this.animOffset = Math.random() * Math.PI * 2;
    this.thought = 'Working...';
    this.thoughtTimer = randInt(1, 4);
    this.state = 'WORK';
    this.role = pick(['hesitant', 'regular', 'leader', 'aid']);
    this.noticeDelay = 1 + Math.random() * 6;
    if (this.role === 'hesitant') this.noticeDelay += 3;
    if (this.role === 'leader') this.noticeDelay *= 0.5;
    this.aware = false;
    this.lastShout = 0;
    this.lastDraw = null;
  }

  setThought(text) {
    if (this.thought !== text) {
      this.thought = text;
      this.thoughtTimer = 2;
    }
  }

  findExit(maze, hazards) {
    let best = null;
    let minD = Infinity;
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        if (maze[r][c] === EXIT) {
          const d = Math.abs(this.r - r) + Math.abs(this.c - c);
          if (d < minD) {
            minD = d;
            best = [r, c];
          }
        }
      }
    }

    if (best) {
      const hazardSet = hotspotKeys(hazards, 5);
      this.path = pathfinder.findPath([this.r, this.c], best, maze, hazardSet);
      this.pathIndex = 0;
    }
  }

  update(dt, maze, hazards) {
    if (!this.alive) return;

    if (this.thoughtTimer > 0) this.thoughtTimer -= dt;

    if (!evacStarted) {
      this.state = 'WORK';
      if (this.thoughtTimer <= 0) {
        this.setThought(pick(workingThoughts));
        this.thoughtTimer = randInt(3, 6);
      }
      return;
    }

    if (!this.aware) {
      this.noticeDelay -= dt;
      if (this.noticeDelay <= 0) {
        this.aware = true;
        this.setThought('What happened?');
        if (this.role === 'hesitant' && Math.random() < 0.4) {
          this.stunTimer = 2;
          this.setThought('Frozen...');
        }
        if (this.role === 'leader') this.setThought(pick(leaderThoughts));
        if (this.role === 'aid') this.setThought(pick(aidThoughts));
      } else {
        return;
      }
    }

    const heatHere = getHeat(this.r, this.c);
    const smokeHere = getSmoke(this.r, this.c);

    if (!this.escaped && heatHere > 0) {
      this.health -= (8 + heatHere * 0.4) * dt;
      if (Math.random() < 0.3) this.setThought('Too hot!');
      this.state = 'PANIC';
    }

    if (!this.escaped && smokeHere > 12) {
      this.health -= (smokeHere - 10) * 0.15 * dt;
      if (Math.random() < 0.3) this.setThought('Smoke!');
    }

    if (!this.escaped && this.stunTimer > 0) {
      this.stunTimer -= dt;
      this.setThought("Can't hear...");
      return;
    }

    if (this.health < 50) {
      this.injured = true;
      if (this.state !== 'PANIC') this.setThought('Hurts to walk...');
    }

    if (this.health <= 0) {
      this.alive = false;
      this.setThought('...');
      return;
    }

    if (maze[this.r][this.c] === EXIT) {
      if (!this.escaped) {
        this.escaped = true;
        this.setThought('Made it!');
      }
      return;
    }

    if (!this.path.length || Math.random() < 0.05) {
      this.findExit(maze, hazards);
      if (!this.path.length) {
        this.setThought('TRAPPED!');
        this.state = 'PANIC';
      } else if (this.state !== 'MOVING') {
        this.setThought('Exit found.');
        this.state = 'MOVING';
      }
    }

    if (this.path.length && this.pathIndex < this.path.length) {
      const [nr, nc] = this.path[this.pathIndex];
      let speed = 4;
      speed *= Math.max(0.35, 1 - heatHere * 0.01);
      if (smokeHere > 12) speed *= 0.6;
      if (this.role === 'hesitant') speed *= 0.8;
      if (this.role === 'leader') speed *= 1.2;
      if (this.injured) speed = 1.5;
      if (maze[this.r][this.c] === RUBBLE) {
        speed *= 0.3;
        this.setThought('Ugh, debris...');
      }

      const dr = nr - this.exactR;
      const dc = nc - this.exactC;
      const dist = Math.hypot(dr, dc);

      if (dist > 0) {
        const move = Math.min(dist, speed * dt);
        this.exactR += (dr / dist) * move;
        this.exactC += (dc / dist) * move;

        const curR = clamp(Math.round(this.exactR), 0, ROWS - 1);
        const curC = clamp(Math.round(this.exactC), 0, COLS - 1);
        if (maze[curR][curC] === WALL) {
          this.path = [];
        } else {
          this.r = curR;
          this.c = curC;
          if (dist < 0.1) this.pathIndex += 1;
        }
      }
    }

    // occasional shouts
    this.lastShout += dt;
    if (this.lastShout > 3 + Math.random() * 5) {
      if (this.role === 'leader') this.setThought(pick(leaderThoughts));
      else if (this.role === 'aid') this.setThought(pick(aidThoughts));
      else if (this.state === 'PANIC') this.setThought(pick(panicThoughts));
      this.lastShout = 0;
    }
  }
}

const hazards = new Map(); // key -> { intensity }
let maze = [];
let people = [];
let last = performance.now();
const keysDown = new Set();

function key(node) {
  return `${node[0]},${node[1]}`;
}

function parseKey(k) {
  const [r, c] = k.split(',').map(Number);
  return [r, c];
}

function clamp(val, min, max) {
  return Math.min(max, Math.max(min, val));
}

function randInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function pick(arr) {
  return arr[randInt(0, arr.length - 1)];
}

function formatTime(ms) {
  if (!ms || Number.isNaN(ms)) return '--';
  const s = ms / 1000;
  const m = Math.floor(s / 60);
  const sec = (s % 60).toFixed(1);
  return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
}

class FakeSocket extends EventTarget {
  send() {}
  close() {}
}

function startMockSocket() {
  if (mockSocket) return mockSocket;
  mockSocket = new FakeSocket();
  setInterval(() => {
    if (!sensorNodes.length) return;
    const s = pick(sensorNodes);
    const reading = Math.max(0, getHeat(s.r, s.c) * 0.6 + getSmoke(s.r, s.c) * 0.8 + randInt(0, 12));
    const msg = { sensorId: s.id, reading, r: s.r, c: s.c, ts: Date.now() };
    mockSocket.dispatchEvent(new MessageEvent('message', { data: JSON.stringify(msg) }));
  }, 1200);
  return mockSocket;
}

function wireMockFeed() {
  if (feedAttached) return;
  const sock = startMockSocket();
  sock.addEventListener('message', handleSensorMessage);
  feedAttached = true;
}

function handleSensorMessage(evt) {
  try {
    const payload = JSON.parse(evt.data);
    const s = sensorNodes.find((n) => n.id === payload.sensorId) || sensorNodes.find((n) => Math.abs(n.r - payload.r) + Math.abs(n.c - payload.c) < 3);
    if (!s) return;
    s.reading = payload.reading;
    s.triggered = s.reading > 15;
  } catch (err) {
    console.warn('Sensor feed parse failed', err);
  }
}

function rebuildOccupancy() {
  occupancyGrid = Array.from({ length: ROWS }, () => Array.from({ length: COLS }, () => 0));
  for (const p of people) {
    if (!p.alive || p.escaped) continue;
    const r = clamp(Math.round(p.exactR), 0, ROWS - 1);
    const c = clamp(Math.round(p.exactC), 0, COLS - 1);
    occupancyGrid[r][c] += 1;
  }
}

function resizeCanvas() {
  const prevW = screenWidth;
  const prevH = screenHeight;
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  screenWidth = canvas.width;
  screenHeight = canvas.height;
  if (camera) {
    camera.x += (screenWidth - prevW) / 2;
    camera.y += (screenHeight - prevH) / 2;
  }
}

resizeCanvas();
camera = new Camera();
window.addEventListener('resize', resizeCanvas);

function createMaze() {
  const m = Array.from({ length: ROWS }, () => Array.from({ length: COLS }, () => FLOOR));

  for (let r = 0; r < ROWS; r++) {
    m[r][0] = WALL;
    m[r][COLS - 1] = WALL;
  }
  for (let c = 0; c < COLS; c++) {
    m[0][c] = WALL;
    m[ROWS - 1][c] = WALL;
  }

  for (let r = 5; r < ROWS - 5; r += 8) {
    for (let c = 5; c < COLS - 5; c += 8) {
      m[r][c] = WALL;
      m[r + 1][c] = WALL;
      m[r][c + 1] = WALL;
    }
  }

  m[Math.floor(ROWS / 2)][0] = EXIT;
  m[Math.floor(ROWS / 2)][COLS - 1] = EXIT;
  return m;
}

function spawnSensors() {
  sensorNodes.length = 0;
  sensorIdCounter = 0;
  const count = 8;
  for (let i = 0; i < count; i++) {
    sensorNodes.push({
      id: sensorIdCounter++,
      r: randInt(3, ROWS - 4),
      c: randInt(3, COLS - 4),
      radius: randInt(3, 6),
      triggered: false,
      reading: 0,
    });
  }
}

function clearScenarioTimers() {
  scenarioTimers.forEach((t) => clearTimeout(t));
  scenarioTimers = [];
}

function seedScenario(scenario) {
  if (!scenario?.seeds) return;
  for (const seed of scenario.seeds) {
    const keyStr = key([seed.r, seed.c]);
    if (maze[seed.r][seed.c] !== WALL) {
      hazards.set(keyStr, { intensity: seed.intensity });
    }
  }
}

function scheduleSuppressions(scenario) {
  clearScenarioTimers();
  (scenario?.suppression || []).forEach((step) => {
    const tid = setTimeout(() => {
      for (const [hk, data] of [...hazards.entries()]) {
        const [r, c] = parseKey(hk);
        const d = Math.hypot(r - (scenario.seeds?.[0]?.r || r), c - (scenario.seeds?.[0]?.c || c));
        if (d <= (step.radius || 6)) {
          data.intensity *= 1 - step.power;
          if (data.intensity < 2) hazards.delete(hk);
        }
      }
    }, step.t * 1000);
    scenarioTimers.push(tid);
  });
}

function applyWind(scenario) {
  const dx = scenario?.wind?.dx || 0;
  const dy = scenario?.wind?.dy || 0;
  windState.dx = dx;
  windState.dy = dy;
  windState.mag = Math.hypot(dx, dy);
}

function applyScenario(id) {
  const next = scenarios.find((s) => s.id === id);
  if (!next) return;
  currentScenario = next;
  resetWorld();
}

function spawnPeople(m) {
  const list = [];
  for (let i = 0; i < TOTAL_PEOPLE; i++) {
    let r = randInt(2, ROWS - 2);
    let c = randInt(2, COLS - 2);
    while (m[r][c] === WALL) {
      r = randInt(2, ROWS - 2);
      c = randInt(2, COLS - 2);
    }
    list.push(new Person(i, r, c));
  }
  return list;
}

function resetWorld() {
  evacStarted = false;
  metrics = {
    startedAt: performance.now(),
    evacStartedAt: null,
    evacEndedAt: null,
    congestionNow: 0,
    congestionMax: 0,
  };
  clearScenarioTimers();
  hazards.clear();
  heatGrid = Array.from({ length: ROWS }, () => Array.from({ length: COLS }, () => 0));
  smokeGrid = Array.from({ length: ROWS }, () => Array.from({ length: COLS }, () => 0));
  maze = createMaze();
  people = spawnPeople(maze);
  spawnSensors();
  seedScenario(currentScenario);
  scheduleSuppressions(currentScenario);
  applyWind(currentScenario);
  startMockSocket();
  wireMockFeed();
  camera.centerOnMap();
  camera.target = null;
  updateHUD();
}

function handleKeyDown(e) {
  const k = e.key.toLowerCase();
  keysDown.add(k);

  if (k === ' ') {
    e.preventDefault();
    camera.target = null;
  }
  if (k === 'r') {
    resetWorld();
  }
  if (k === 'b') triggerBomb();
  if (k === 'e') triggerQuake();
  if (k === 'f') triggerFire();
  if (k === 'h') toggleHeatmap();
  if (k === 'v') toggleSensors();
  if (k === 'g') toggleRoutes();
  if (k === '1') placementMode = 'fire';
  if (k === '2') placementMode = 'bomb';
  if (k === '3') placementMode = 'quake';
  if (k === 't') triggerRandomDisaster();
}

function handleKeyUp(e) {
  keysDown.delete(e.key.toLowerCase());
}

window.addEventListener('keydown', handleKeyDown);
window.addEventListener('keyup', handleKeyUp);

canvas.addEventListener('mousedown', (e) => {
  const rect = canvas.getBoundingClientRect();
  const mx = ((e.clientX - rect.left) / rect.width) * canvas.width;
  const my = ((e.clientY - rect.top) / rect.height) * canvas.height;
  let bestDist = 40 * camera.zoom;
  let selected = null;
  if (e.shiftKey) {
    // place sensor
    const gridR = Math.floor((my + camera.y) / camera.tileH);
    const gridC = Math.floor((mx + camera.x) / camera.tileW);
    if (gridR >= 1 && gridR < ROWS - 1 && gridC >= 1 && gridC < COLS - 1) {
      sensorNodes.push({ id: sensorIdCounter++, r: gridR, c: gridC, radius: randInt(3, 6), triggered: false, reading: 0 });
    }
  } else if (e.button === 2 || e.ctrlKey) {
    // targeted disaster placement
    const gridR = Math.floor((my + camera.y) / camera.tileH);
    const gridC = Math.floor((mx + camera.x) / camera.tileW);
    spawnDisasterAt(gridR, gridC, placementMode);
  } else {
    for (const p of people) {
      const pos = camera.toScreen(p.exactR, p.exactC);
      const d = Math.hypot(pos.x + camera.tileW / 2 - mx, pos.y + camera.tileH / 2 - my);
      if (d < bestDist) {
        bestDist = d;
        selected = p;
      }
    }
    if (selected) camera.target = selected;
  }
});

canvas.addEventListener('wheel', (e) => {
  e.preventDefault();
  camera.applyZoom(-e.deltaY * 0.0015);
});

canvas.addEventListener('contextmenu', (e) => e.preventDefault());

function beginEvac() {
  if (evacStarted) return;
  evacStarted = true;
  sounds.alarm.play();
  for (const p of people) {
    p.path = [];
    p.state = 'IDLE';
    p.setThought('Move! Move!');
  }
}

function toggleHeatmap() { overlayState.showHeatmap = !overlayState.showHeatmap; }
function toggleSensors() { overlayState.showSensors = !overlayState.showSensors; }
function toggleRoutes() { overlayState.showRoutes = !overlayState.showRoutes; }

function triggerBomb() {
  beginEvac();
  sounds.bomb.play();
  camera.shake = 15;
  for (let i = 0; i < 4; i++) {
    let ir = randInt(2, ROWS - 2);
    let ic = randInt(2, COLS - 2);
    maze[ir][ic] = RUBBLE;
    for (let dr = -1; dr <= 1; dr++) {
      for (let dc = -1; dc <= 1; dc++) {
        const nr = ir + dr;
        const nc = ic + dc;
        if (nr >= 0 && nc >= 0 && nr < ROWS && nc < COLS && Math.random() < 0.8) {
          maze[nr][nc] = RUBBLE;
        }
      }
    }
    for (const p of people) {
      if (Math.abs(p.r - ir) + Math.abs(p.c - ic) < 6) {
        p.stunTimer = 3;
        p.setThought('EARS RINGING!');
      }
    }
    if (Math.random() < 0.5) hazards.set(key([ir, ic]), { intensity: 28 });
  }
}

function triggerQuake() {
  beginEvac();
  sounds.quake.play();
  camera.shake = 25;
  for (let i = 0; i < 60; i++) {
    const rx = randInt(2, ROWS - 2);
    const ry = randInt(2, COLS - 2);
    if (maze[rx][ry] === FLOOR) maze[rx][ry] = RUBBLE;
  }
}

function triggerFire() {
  beginEvac();
  sounds.fire.play();
  for (let i = 0; i < 10; i++) {
    const fx = randInt(2, ROWS - 2);
    const fy = randInt(2, COLS - 2);
    if (maze[fx][fy] !== WALL) hazards.set(key([fx, fy]), { intensity: 35 });
  }
}

function triggerRandomDisaster() {
  const roll = Math.random();
  if (roll < 0.33) triggerBomb();
  else if (roll < 0.66) triggerQuake();
  else triggerFire();
}

function spawnDisasterAt(r, c, type) {
  if (r < 1 || c < 1 || r >= ROWS - 1 || c >= COLS - 1) return;
  if (type === 'fire') {
    hazards.set(key([r, c]), { intensity: 42 });
  } else if (type === 'bomb') {
    camera.shake = 12;
    for (let i = 0; i < 3; i++) {
      const ir = clamp(r + randInt(-1, 1), 1, ROWS - 2);
      const ic = clamp(c + randInt(-1, 1), 1, COLS - 2);
      maze[ir][ic] = RUBBLE;
      for (const p of people) {
        if (Math.abs(p.r - ir) + Math.abs(p.c - ic) < 5) {
          p.stunTimer = 2.5;
          p.setThought('EARS RINGING!');
        }
      }
      if (Math.random() < 0.8) hazards.set(key([ir, ic]), { intensity: 30 });
    }
  } else if (type === 'quake') {
    camera.shake = 18;
    for (let dr = -3; dr <= 3; dr++) {
      for (let dc = -3; dc <= 3; dc++) {
        const nr = r + dr;
        const nc = c + dc;
        if (nr > 0 && nc > 0 && nr < ROWS - 1 && nc < COLS - 1 && maze[nr][nc] === FLOOR) {
          maze[nr][nc] = RUBBLE;
        }
      }
    }
  }
  beginEvac();
}

function update(dt) {
  handleCameraMovement(dt);
  camera.update();
  rebuildOccupancy();
  updateHazards(dt);
  updateSensors();

  for (const p of people) {
    p.update(dt, maze, hazards);
  }
  updateMetrics();
}

function handleCameraMovement(dt) {
  let dx = 0;
  let dy = 0;
  const speed = 420 * dt;
  if (keysDown.has('w') || keysDown.has('arrowup')) dy -= speed;
  if (keysDown.has('s') || keysDown.has('arrowdown')) dy += speed;
  if (keysDown.has('a') || keysDown.has('arrowleft')) dx -= speed;
  if (keysDown.has('d') || keysDown.has('arrowright')) dx += speed;
  if (dx !== 0 || dy !== 0) camera.move(dx, dy);
}

function updateHazards(dt) {
  // decay smoke and clear heat
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      heatGrid[r][c] = 0;
      smokeGrid[r][c] *= Math.pow(SMOKE_DECAY, dt * 30);
    }
  }

  const additions = [];
  for (const [k, data] of [...hazards.entries()]) {
    let { intensity } = data;
    intensity = Math.max(0, intensity - FIRE_DECAY * dt);
    if (intensity <= 1) {
      hazards.delete(k);
      continue;
    }
    data.intensity = intensity;
    const [r, c] = parseKey(k);

    // accumulate heat & smoke diffusion
    for (let dr = -4; dr <= 4; dr++) {
      for (let dc = -4; dc <= 4; dc++) {
        const nr = r + dr;
        const nc = c + dc;
        if (nr < 0 || nc < 0 || nr >= ROWS || nc >= COLS) continue;
        const dist = Math.abs(dr) + Math.abs(dc);
        const falloff = Math.max(0, 1 - dist * 0.2);
        heatGrid[nr][nc] += intensity * falloff;
        smokeGrid[nr][nc] += intensity * 0.1 * falloff * (currentScenario?.smokeBoost || 1);
      }
    }

    if (intensity > 32 && maze[r][c] === FLOOR) maze[r][c] = RUBBLE;

    for (const [dr, dc] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) {
      const nr = r + dr;
      const nc = c + dc;
      if (nr < 1 || nc < 1 || nr >= ROWS - 1 || nc >= COLS - 1) continue;
      if (maze[nr][nc] === WALL) continue;
      const occ = occupancyGrid?.[nr]?.[nc] || 0;
      const predicted = predictSpread(intensity, heatGrid[nr][nc], smokeGrid[nr][nc], occ, windState.mag);
      const chance = FIRE_SPREAD * dt * (intensity / 30) * (1 + windState.mag * 0.8) * predicted;
      if (Math.random() < chance) additions.push([nr, nc, intensity * 0.65 + 6]);
      const wr = r + Math.sign(windState.dy);
      const wc = c + Math.sign(windState.dx);
      if (wr >= 1 && wc >= 1 && wr < ROWS - 1 && wc < COLS - 1 && maze[wr][wc] !== WALL) {
        if (Math.random() < chance * 0.6) additions.push([wr, wc, intensity * 0.55 + 4]);
      }
    }
  }

  for (const [r, c, power] of additions) {
    const k = key([r, c]);
    if (!hazards.has(k)) hazards.set(k, { intensity: power });
    else hazards.get(k).intensity = Math.max(hazards.get(k).intensity, power);
  }

  if (hazards.size && !evacStarted) beginEvac();
  if (hazards.size && !sounds.fire.playing()) sounds.fire.play();
  if (!hazards.size) sounds.fire.stop();
}

function predictSpread(intensity, heat, smoke, occupancy, windMag) {
  const baseline = Math.min(1, 0.25 + intensity / 60 + smoke / 120 + occupancy * 0.1 + windMag * 0.4);
  if (!window.tf || !tf?.tensor) return baseline;
  return tf.tidy(() => {
    const input = tf.tensor2d([[intensity / 60, heat / 80, smoke / 90, occupancy / 5, windMag / 3]]);
    const weights = tf.tensor2d([[0.6], [0.4], [0.5], [0.35], [0.3]]);
    const bias = tf.scalar(0.1);
    const score = input.matMul(weights).add(bias).sigmoid();
    return score.dataSync()[0];
  });
}

function updateSensors() {
  for (const s of sensorNodes) {
    s.reading *= 0.92;
    let hazardTriggered = false;
    for (const [hk] of hazards) {
      const [hr, hc] = parseKey(hk);
      const d = Math.hypot(hr - s.r, hc - s.c);
      if (d <= s.radius) {
        hazardTriggered = true;
        s.reading = Math.max(s.reading, Math.max(getHeat(hr, hc), getSmoke(hr, hc)));
        break;
      }
    }
    s.triggered = hazardTriggered || s.reading > 15;
  }
}

function updateMetrics() {
  let maxCell = 0;
  for (let r = 0; r < occupancyGrid.length; r++) {
    for (let c = 0; c < occupancyGrid[r].length; c++) {
      if (occupancyGrid[r][c] > maxCell) maxCell = occupancyGrid[r][c];
    }
  }
  metrics.congestionNow = maxCell;
  metrics.congestionMax = Math.max(metrics.congestionMax, maxCell);

  if (evacStarted && !metrics.evacStartedAt) metrics.evacStartedAt = performance.now();

  const alive = people.filter((p) => p.alive && !p.escaped).length;
  const escaped = people.filter((p) => p.escaped).length;
  if (evacStarted && (escaped === people.length || alive === 0) && !metrics.evacEndedAt) {
    metrics.evacEndedAt = performance.now();
    console.log('Evac complete', {
      evacTimeMs: metrics.evacEndedAt - metrics.evacStartedAt,
      congestionMax: metrics.congestionMax,
      escaped,
    });
  }
}

function draw() {
  ctx.clearRect(0, 0, screenWidth, screenHeight);
  const grd = ctx.createLinearGradient(0, 0, screenWidth, screenHeight);
  grd.addColorStop(0, '#0b1020');
  grd.addColorStop(1, '#080b12');
  ctx.fillStyle = grd;
  ctx.fillRect(0, 0, screenWidth, screenHeight);

  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      drawTile(r, c, maze[r][c]);
    }
  }

  drawSmoke();
  if (overlayState.showHeatmap) drawHeatmap();

  drawSensors();

  for (const [k, data] of hazards) {
    const [r, c] = parseKey(k);
    drawFireCell(r, c, data.intensity);
  }

  people.sort((a, b) => a.exactR + a.exactC - (b.exactR + b.exactC));
  const timeVal = performance.now() / 1000;
  for (const p of people) {
    drawPerson(p, timeVal);
  }

  if (overlayState.showRoutes) drawGuidancePath();

  drawLightingMask();
  drawVignette();
  updateHUD();
}

function drawTile(r, c, tile) {
  const pos = camera.toScreen(r, c);
  if (pos.x < -camera.tileW || pos.x > screenWidth + camera.tileW || pos.y < -camera.tileH || pos.y > screenHeight + camera.tileH) return;

  const w = camera.tileW;
  const hTile = camera.tileH;
  let col = Colors.FLOOR;

  if (tile === WALL) col = Colors.WALL_TOP;
  else if (tile === RUBBLE) col = Colors.RUBBLE;
  else if (tile === EXIT) col = Colors.EXIT;

  ctx.fillStyle = col;
  ctx.fillRect(pos.x, pos.y, w, hTile);

  if (tile === WALL) {
    ctx.fillStyle = Colors.WALL_SIDE;
    ctx.fillRect(pos.x, pos.y + hTile - 4 * camera.zoom, w, 4 * camera.zoom);
  } else if (tile === EXIT) {
    const pulse = 0.7 + Math.sin(performance.now() / 300 + r + c) * 0.3;
    ctx.fillStyle = `rgba(50,255,116,${pulse})`;
    ctx.fillRect(pos.x, pos.y, w, hTile);
  }
}

function drawPerson(p, timeVal) {
  const pos = camera.toScreen(p.exactR, p.exactC);
  if (pos.x < -50 || pos.x > screenWidth + 50 || pos.y < -50 || pos.y > screenHeight + 50) return;

  const zoom = camera.zoom;
  if (!p.alive) {
    ctx.fillStyle = p.colorShirt;
    ctx.fillRect(pos.x - 8 * zoom, pos.y - 2 * zoom, 16 * zoom, 4 * zoom);
    return;
  }

  let bob = 0;
  if (p.state === 'MOVING') bob = Math.sin(timeVal * 10 + p.animOffset) * 2 * zoom;
  else if (p.state === 'WORK') bob = Math.sin(timeVal * 2 + p.animOffset) * 1.2 * zoom;

  // shadow
  ctx.fillStyle = 'rgba(0,0,0,0.35)';
  ctx.beginPath();
  ctx.ellipse(pos.x + camera.tileW / 2, pos.y + camera.tileH / 2 + 6 * zoom, 9 * zoom, 5 * zoom, 0, 0, Math.PI * 2);
  ctx.fill();

  if (p.state === 'MOVING' && p.lastDraw) {
    ctx.strokeStyle = 'rgba(124,214,241,0.25)';
    ctx.lineWidth = 2 * zoom;
    ctx.beginPath();
    ctx.moveTo(p.lastDraw.x, p.lastDraw.y);
    ctx.lineTo(pos.x + camera.tileW / 2, pos.y + camera.tileH / 2);
    ctx.stroke();
  }

  const radius = 7 * zoom;
  ctx.fillStyle = p.colorShirt;
  ctx.beginPath();
  ctx.arc(pos.x + camera.tileW / 2, pos.y + camera.tileH / 2 + bob, radius + 2 * zoom, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = p.colorSkin;
  ctx.beginPath();
  ctx.arc(pos.x + camera.tileW / 2, pos.y + camera.tileH / 2 - 5 * zoom + bob, radius, 0, Math.PI * 2);
  ctx.fill();

  if (p.stunTimer > 0) {
    ctx.fillStyle = '#ffd600';
    ctx.beginPath();
    ctx.arc(pos.x + camera.tileW / 2, pos.y + camera.tileH / 2 - 12 * zoom, 3 * zoom, 0, Math.PI * 2);
    ctx.fill();
  }

  if (camera.target === p) {
    const arrowY = pos.y + camera.tileH / 2 - 18 * zoom + Math.sin(timeVal * 5) * 5;
    const cx = pos.x + camera.tileW / 2;
    ctx.fillStyle = '#ffd600';
    ctx.beginPath();
    ctx.moveTo(cx, arrowY + 10 * zoom);
    ctx.lineTo(cx - 6 * zoom, arrowY);
    ctx.lineTo(cx + 6 * zoom, arrowY);
    ctx.closePath();
    ctx.fill();
  }

  p.lastDraw = { x: pos.x + camera.tileW / 2, y: pos.y + camera.tileH / 2 };
}

function drawHeatmap() {
  const maxRisk = 60;
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const pos = camera.toScreen(r, c);
      if (pos.x < -camera.tileW || pos.x > screenWidth + camera.tileW || pos.y < -camera.tileH || pos.y > screenHeight + camera.tileH) continue;
      const risk = heatGrid[r][c];
      if (risk <= 0) continue;
      const alpha = Math.min(0.35, risk / maxRisk);
      ctx.fillStyle = `rgba(255, 99, 71, ${alpha})`;
      ctx.fillRect(pos.x, pos.y, camera.tileW, camera.tileH);
    }
  }
}

function drawSmoke() {
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const level = smokeGrid[r][c];
      if (level < 8) continue;
      const pos = camera.toScreen(r, c);
      const wobble = Math.sin((performance.now() / 600) + r * 0.5 + c * 0.3) * 0.2;
      const alpha = Math.min(0.45, level / 80) + wobble * 0.05;
      ctx.fillStyle = `rgba(120, 130, 140, ${Math.max(0.05, alpha)})`;
      ctx.beginPath();
      ctx.ellipse(pos.x + camera.tileW / 2, pos.y + camera.tileH / 2, camera.tileW * 0.7, camera.tileH * 0.8, 0, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}

function drawSensors() {
  if (!overlayState.showSensors) return;
  for (const s of sensorNodes) {
    const pos = camera.toScreen(s.r, s.c);
    const cx = pos.x + camera.tileW / 2;
    const cy = pos.y + camera.tileH / 2;
    ctx.strokeStyle = s.triggered ? '#ff6b6b' : '#7cd6f1';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(cx, cy, s.radius * camera.tileW, 0, Math.PI * 2);
    ctx.stroke();

    ctx.fillStyle = s.triggered ? '#ff6b6b' : '#7cd6f1';
    ctx.beginPath();
    ctx.arc(cx, cy, 4, 0, Math.PI * 2);
    ctx.fill();
  }
}

function drawGuidancePath() {
  const candidate = people.find((p) => p.alive && !p.escaped);
  if (!candidate) return;
  let bestExit = null;
  let minD = Infinity;
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      if (maze[r][c] === EXIT) {
        const d = Math.abs(candidate.r - r) + Math.abs(candidate.c - c);
        if (d < minD) {
          minD = d;
          bestExit = [r, c];
        }
      }
    }
  }
  if (!bestExit) return;
  const path = pathfinder.findPath([candidate.r, candidate.c], bestExit, maze, hotspotKeys(hazards, 5));
  if (!path.length) return;
  ctx.strokeStyle = 'rgba(124, 214, 241, 0.9)';
  ctx.lineWidth = 3;
  ctx.beginPath();
  const first = camera.toScreen(candidate.r, candidate.c);
  ctx.moveTo(first.x + camera.tileW / 2, first.y + camera.tileH / 2);
  for (const [r, c] of path) {
    const pos = camera.toScreen(r, c);
    ctx.lineTo(pos.x + camera.tileW / 2, pos.y + camera.tileH / 2);
  }
  ctx.stroke();
}

function drawLightingMask() {
  if (!camera.target) return;
  const pos = camera.toScreen(camera.target.exactR, camera.target.exactC);
  const smokeLevel = getSmoke(camera.target.r, camera.target.c);
  const radius = Math.max(120 * camera.zoom, (200 - smokeLevel * 2) * camera.zoom);

  ctx.save();
  ctx.fillStyle = 'rgba(30,30,30,0.8)';
  ctx.fillRect(0, 0, screenWidth, screenHeight);
  ctx.globalCompositeOperation = 'destination-out';
  const g = ctx.createRadialGradient(
    pos.x + camera.tileW / 2,
    pos.y + camera.tileH / 2,
    radius * 0.25,
    pos.x + camera.tileW / 2,
    pos.y + camera.tileH / 2,
    radius
  );
  g.addColorStop(0, 'rgba(0,0,0,0.9)');
  g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g;
  ctx.beginPath();
  ctx.arc(pos.x + camera.tileW / 2, pos.y + camera.tileH / 2, radius, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  drawThoughtBubble(camera.target, pos);
}

function drawVignette() {
  ctx.save();
  const rad = Math.max(screenWidth, screenHeight);
  const g = ctx.createRadialGradient(screenWidth / 2, screenHeight / 2, rad * 0.2, screenWidth / 2, screenHeight / 2, rad * 0.7);
  g.addColorStop(0, 'rgba(0,0,0,0)');
  g.addColorStop(1, 'rgba(0,0,0,0.3)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, screenWidth, screenHeight);
  ctx.restore();
}

function drawFireCell(r, c, intensity) {
  const pos = camera.toScreen(r, c);
  const baseX = pos.x + camera.tileW / 2;
  const baseY = pos.y + camera.tileH / 2;
  const time = performance.now() / 1000;
  const flicker = 0.6 + Math.sin(time * 12 + (r + c)) * 0.15 + Math.random() * 0.05;
  const core = Math.min(12 * camera.zoom, 6 + intensity * 0.2) * flicker;
  const glow = core * 2.2;

  const grad = ctx.createRadialGradient(baseX, baseY, core * 0.4, baseX, baseY - 4, glow);
  grad.addColorStop(0, 'rgba(255, 210, 120, 0.95)');
  grad.addColorStop(0.4, 'rgba(255, 150, 60, 0.75)');
  grad.addColorStop(1, 'rgba(180, 50, 20, 0)');

  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.ellipse(baseX, baseY - 6, glow * 0.6, glow, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = `rgba(255, ${Math.max(120, 180 - intensity)}, 80, 0.9)`;
  ctx.beginPath();
  ctx.moveTo(baseX, baseY - core * 1.5);
  ctx.lineTo(baseX - core * 0.6, baseY + core * 0.4);
  ctx.lineTo(baseX + core * 0.6, baseY + core * 0.4);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

function drawThoughtBubble(p, pos) {
  const bubbleW = 190;
  const bubbleH = 56;
  const x = clamp(pos.x + 30, 12, screenWidth - bubbleW - 12);
  const y = clamp(pos.y - 60, 12, screenHeight - bubbleH - 12);

  ctx.save();
  ctx.fillStyle = 'rgba(255,255,255,0.98)';
  roundRect(ctx, x, y, bubbleW, bubbleH, 10);
  ctx.fill();
  ctx.beginPath();
  ctx.moveTo(x, y + bubbleH - 10);
  ctx.lineTo(x - 12, y + bubbleH + 6);
  ctx.lineTo(x + 12, y + bubbleH - 10);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = '#0b0c10';
  ctx.font = '14px "Space Grotesk", sans-serif';
  ctx.fillText(p.thought, x + 14, y + 26);

  ctx.fillStyle = '#545972';
  ctx.font = '11px "JetBrains Mono", monospace';
  ctx.fillText(`ID ${p.id} · ${p.state}`, x + 14, y + 44);
  ctx.restore();
}

function shade(hex, factor) {
  const c = hex.startsWith('#') ? hex.slice(1) : hex;
  const num = parseInt(c, 16);
  const r = Math.max(0, Math.min(255, Math.floor(((num >> 16) & 255) * factor)));
  const g = Math.max(0, Math.min(255, Math.floor(((num >> 8) & 255) * factor)));
  const b = Math.max(0, Math.min(255, Math.floor((num & 255) * factor)));
  return `rgb(${r},${g},${b})`;
}

function roundRect(context, x, y, w, h, r) {
  context.beginPath();
  context.moveTo(x + r, y);
  context.lineTo(x + w - r, y);
  context.quadraticCurveTo(x + w, y, x + w, y + r);
  context.lineTo(x + w, y + h - r);
  context.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  context.lineTo(x + r, y + h);
  context.quadraticCurveTo(x, y + h, x, y + h - r);
  context.lineTo(x, y + r);
  context.quadraticCurveTo(x, y, x + r, y);
  context.closePath();
}

function updateHUD() {
  const alive = people.filter((p) => p.alive).length;
  const escaped = people.filter((p) => p.escaped).length;
  const activeSensors = sensorNodes.filter((s) => s.triggered).length;
  const targetText = camera.target
    ? `Tracking ID ${camera.target.id} · ${camera.target.thought}`
    : 'Camera free · click a person to follow';
  const evacTime =
    metrics.evacEndedAt && metrics.evacStartedAt
      ? metrics.evacEndedAt - metrics.evacStartedAt
      : metrics.evacStartedAt
      ? performance.now() - metrics.evacStartedAt
      : null;

  if (setHudState) {
    setHudState({
      alive,
      escaped,
      hazards: hazards.size,
      sensors: `${activeSensors}/${sensorNodes.length}`,
      status: evacStarted ? 'Evacuating' : 'Working',
       scenario: currentScenario.name,
       congestion: `${metrics.congestionNow}/${metrics.congestionMax}`,
       evacTime: formatTime(evacTime),
      target: targetText,
    });
  }
}

function loop(ts) {
  const dt = Math.min(0.05, (ts - last) / 1000);
  last = ts;
  update(dt);
  draw();
  requestAnimationFrame(loop);
}

root.render(html`<${App} scenariosList=${scenarios} onScenario=${applyScenario} onReset=${resetWorld} onBomb=${triggerBomb} onQuake=${triggerQuake} onFire=${triggerFire} />`);

resetWorld();
requestAnimationFrame(loop);
