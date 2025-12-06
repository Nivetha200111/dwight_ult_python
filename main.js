import React from 'https://esm.sh/react@18.3.1';
import { createRoot } from 'https://esm.sh/react-dom@18.3.1/client';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(React.createElement);

const canvas = document.getElementById('sim');
const ctx = canvas.getContext('2d');

const initialHud = {
  alive: 0,
  escaped: 0,
  hazards: 0,
  sensors: '0/0',
  status: 'Working',
  target: 'Camera free · click a person to follow',
};

let setHudState = null;

function App({ onReset, onBomb, onQuake, onFire }) {
  const [hud, setHud] = React.useState(initialHud);
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
            <span class="chip">Status: ${hud.status}</span>
          </div>
          <div class="controls">
            WASD pan · Scroll zoom · Click follow · Space free camera · B bomb · E quake · F fire · R reset
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
  SKINS: ['#ffdcb1', '#b48a78', '#8d5524'],
  SHIRTS: ['#7070d6', '#d67a7a', '#68b96b', '#d4c66b'],
};

const FLOOR = 0;
const WALL = 1;
const EXIT = 2;
const RUBBLE = 3;
const workingThoughts = ['Working...', 'Crunching numbers', 'Pulling reports', 'Fixing bugs', 'On a call'];
let evacStarted = false;
const sensorNodes = [];
let overlayState = { showHeatmap: false, showSensors: true, showRoutes: true };

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
      const hazardSet = new Set(hazards.keys());
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

    if (!this.escaped && hazards.has(key([this.r, this.c]))) {
      this.health -= 40 * dt;
      this.setThought("I'M BURNING!");
      this.state = 'PANIC';
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
  }
}

const hazards = new Map();
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
  const count = 8;
  for (let i = 0; i < count; i++) {
    sensorNodes.push({
      r: randInt(3, ROWS - 4),
      c: randInt(3, COLS - 4),
      radius: randInt(3, 6),
      triggered: false,
    });
  }
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
  hazards.clear();
  maze = createMaze();
  people = spawnPeople(maze);
  spawnSensors();
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
      sensorNodes.push({ r: gridR, c: gridC, radius: randInt(3, 6), triggered: false });
    }
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

function beginEvac() {
  if (evacStarted) return;
  evacStarted = true;
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
    if (Math.random() < 0.5) hazards.set(key([ir, ic]), 20);
  }
}

function triggerQuake() {
  beginEvac();
  camera.shake = 25;
  for (let i = 0; i < 60; i++) {
    const rx = randInt(2, ROWS - 2);
    const ry = randInt(2, COLS - 2);
    if (maze[rx][ry] === FLOOR) maze[rx][ry] = RUBBLE;
  }
}

function triggerFire() {
  beginEvac();
  for (let i = 0; i < 10; i++) {
    const fx = randInt(2, ROWS - 2);
    const fy = randInt(2, COLS - 2);
    if (maze[fx][fy] !== WALL) hazards.set(key([fx, fy]), 25);
  }
}

function update(dt) {
  handleCameraMovement(dt);
  camera.update();
  updateHazards(dt);
  updateSensors();

  for (const p of people) {
    p.update(dt, maze, hazards);
  }
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
  for (const [k, timer] of [...hazards.entries()]) {
    const next = timer - dt;
    if (next <= 0) hazards.delete(k);
    else hazards.set(k, next);
  }

  if (Math.random() < 0.1 && hazards.size) {
    const keys = [...hazards.keys()];
    const src = parseKey(pick(keys));
    const nr = src[0] + randInt(-1, 1);
    const nc = src[1] + randInt(-1, 1);
    if (nr >= 0 && nc >= 0 && nr < ROWS && nc < COLS && maze[nr][nc] !== WALL) {
      const k = key([nr, nc]);
      if (!hazards.has(k)) hazards.set(k, 10);
    }
  }

  if (hazards.size && !evacStarted) beginEvac();
}

function updateSensors() {
  for (const s of sensorNodes) {
    s.triggered = false;
    for (const [hk] of hazards) {
      const [hr, hc] = parseKey(hk);
      const d = Math.hypot(hr - s.r, hc - s.c);
      if (d <= s.radius) {
        s.triggered = true;
        break;
      }
    }
  }
}

function draw() {
  ctx.clearRect(0, 0, screenWidth, screenHeight);
  ctx.fillStyle = '#0c0f15';
  ctx.fillRect(0, 0, screenWidth, screenHeight);

  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      drawTile(r, c, maze[r][c]);
    }
  }

  if (overlayState.showHeatmap) drawHeatmap();

  drawSensors();

  for (const [k] of hazards) {
    const [r, c] = parseKey(k);
    const pos = camera.toScreen(r, c);
    ctx.beginPath();
    ctx.fillStyle = Colors.FIRE;
    ctx.arc(pos.x + camera.tileW / 2, pos.y + camera.tileH / 2, 6 * camera.zoom, 0, Math.PI * 2);
    ctx.fill();
  }

  people.sort((a, b) => a.exactR + a.exactC - (b.exactR + b.exactC));
  const timeVal = performance.now() / 1000;
  for (const p of people) {
    drawPerson(p, timeVal);
  }

  if (overlayState.showRoutes) drawGuidancePath();

  drawLightingMask();
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
}

function drawHeatmap() {
  const maxRisk = 60;
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const pos = camera.toScreen(r, c);
      if (pos.x < -camera.tileW || pos.x > screenWidth + camera.tileW || pos.y < -camera.tileH || pos.y > screenHeight + camera.tileH) continue;
      const cellKey = key([r, c]);
      let risk = 0;
      if (hazards.has(cellKey)) risk += hazards.get(cellKey) * 2;
      for (const [hk] of hazards) {
        const [hr, hc] = parseKey(hk);
        const d = Math.abs(hr - r) + Math.abs(hc - c);
        risk += Math.max(0, 20 - d);
      }
      if (risk <= 0) continue;
      const alpha = Math.min(0.35, risk / maxRisk);
      ctx.fillStyle = `rgba(255, 99, 71, ${alpha})`;
      ctx.fillRect(pos.x, pos.y, camera.tileW, camera.tileH);
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
  const path = pathfinder.findPath([candidate.r, candidate.c], bestExit, maze, new Set(hazards.keys()));
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
  const radius = 200 * camera.zoom;

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

  if (setHudState) {
    setHudState({
      alive,
      escaped,
      hazards: hazards.size,
      sensors: `${activeSensors}/${sensorNodes.length}`,
      status: evacStarted ? 'Evacuating' : 'Working',
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

root.render(html`<${App} onReset=${resetWorld} onBomb=${triggerBomb} onQuake=${triggerQuake} onFire=${triggerFire} />`);

resetWorld();
requestAnimationFrame(loop);
