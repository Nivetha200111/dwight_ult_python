/**
 * DWIGHT UX - Neural ACO Frontend
 * ================================
 * Web frontend that connects to Python backend via WebSocket
 * Features: Neural predictions, IoT sensors, ACO visualization
 */

import React from 'https://esm.sh/react@18.3.1';
import { createRoot } from 'https://esm.sh/react-dom@18.3.1/client';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(React.createElement);

// Canvas setup
const canvas = document.getElementById('sim');
const ctx = canvas.getContext('2d');

// Configuration
const ROWS = 40;
const COLS = 50;
const BASE_TILE_W = 32;
const BASE_TILE_H = 16;

let screenWidth = canvas.width;
let screenHeight = canvas.height;

// WebSocket connection
let socket = null;
let connected = false;
let simulationState = null;

// Sound (using Howler if available)
const Howl = window.Howl;
function makeSound(src, opts = {}) {
  if (Howl) return new Howl({ src: [src], ...opts });
  return { play() {}, stop() {}, playing() { return false } };
}

const sounds = {
  fire: makeSound('https://cdn.pixabay.com/download/audio/2022/03/15/audio_5b15144f33.mp3?filename=fire-crackling-1-6742.mp3', { loop: true, volume: 0.25 }),
  alarm: makeSound('https://cdn.pixabay.com/download/audio/2022/03/15/audio_206a695f39.mp3?filename=alarm-6107.mp3', { loop: true, volume: 0.2 }),
};

// Colors
const Colors = {
  FLOOR: '#8c8c96',
  FLOOR_ALT: '#7e7e88',
  WALL: '#464751',
  WALL_SIDE: '#2f3038',
  EXIT: '#32ff74',
  FIRE: '#ff7800',
  FIRE_BRIGHT: '#ffcc00',
  SMOKE: '#5a5a64',
  RUBBLE: '#3c3732',

  // Neural/ACO
  PREDICTION: 'rgba(255, 50, 200, 0.4)',
  SAFE_PHEROMONE: 'rgba(0, 255, 150, 0.3)',
  DANGER_PHEROMONE: 'rgba(255, 80, 80, 0.35)',

  // Sensors
  SENSOR_NORMAL: '#7cd6f1',
  SENSOR_TRIGGERED: '#ff6b6b',

  // People
  WORKING: '#6b8cff',
  HEADPHONES: '#ff6bff',
  EVACUATING: '#6bff6b',
  PANICKING: '#ff6b6b',
};

// Tile types
const FLOOR = 0;
const WALL = 1;
const EXIT = 2;
const RUBBLE = 3;

// Camera
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
      this.x += (Math.random() - 0.5) * this.shake * 2;
      this.y += (Math.random() - 0.5) * this.shake * 2;
      this.shake *= 0.9;
    }

    if (this.target && simulationState) {
      const person = simulationState.people.find(p => p.id === this.target);
      if (person) {
        const tx = person.exactC * this.tileW;
        const ty = person.exactR * this.tileH;
        const desiredX = tx - screenWidth / 2;
        const desiredY = ty - screenHeight / 2;
        this.x += (desiredX - this.x) * 0.1;
        this.y += (desiredY - this.y) * 0.1;
      }
    }
  }

  toScreen(r, c) {
    const x = c * this.tileW;
    const y = r * this.tileH;
    return { x: x - this.x, y: y - this.y };
  }
}

let camera = new Camera();

// Overlay state
let overlayState = {
  showPredictions: true,
  showPheromones: true,
  showSensors: true,
  showPaths: true
};

// HUD state
let setHudState = null;
const initialHud = {
  alive: 0,
  escaped: 0,
  deaths: 0,
  hazards: 0,
  alarm: false,
  neural: { confidence: 0, predictions: 0 },
  sensors: { triggered: 0, total: 0, temp: 22, smoke: 0 },
  rl: { decisions: 0, reward: 0 },
  aco: { safe: 0, danger: 0 },
  target: 'Click person to follow',
  connected: false
};

// ═══════════════════════════════════════════════════════════════════════════════
// WEBSOCKET CONNECTION
// ═══════════════════════════════════════════════════════════════════════════════

function connectWebSocket() {
  // Try Socket.IO first
  if (window.io) {
    socket = io('http://localhost:5000');

    socket.on('connect', () => {
      console.log('Connected to backend');
      connected = true;
      if (setHudState) setHudState({ connected: true });
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from backend');
      connected = false;
      if (setHudState) setHudState({ connected: false });
    });

    socket.on('state', (state) => {
      simulationState = state;
      updateHUD();
    });
  } else {
    // Fallback to polling
    setInterval(async () => {
      try {
        const res = await fetch('http://localhost:5000/api/state');
        simulationState = await res.json();
        connected = true;
        updateHUD();
      } catch (e) {
        connected = false;
      }
    }, 50);
  }
}

function sendCommand(cmd, data = {}) {
  if (socket && socket.emit) {
    socket.emit(cmd, data);
  } else {
    // REST fallback
    fetch(`http://localhost:5000/api/${cmd}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// DRAWING FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

function drawTile(r, c, tile) {
  const pos = camera.toScreen(r, c);
  if (pos.x < -camera.tileW || pos.x > screenWidth + camera.tileW) return;
  if (pos.y < -camera.tileH || pos.y > screenHeight + camera.tileH) return;

  let color = (r + c) % 2 === 0 ? Colors.FLOOR : Colors.FLOOR_ALT;

  if (tile === WALL) color = Colors.WALL;
  else if (tile === RUBBLE) color = Colors.RUBBLE;
  else if (tile === EXIT) {
    const pulse = 0.7 + Math.sin(performance.now() / 300) * 0.3;
    color = `rgba(50, 255, 116, ${pulse})`;
  }

  ctx.fillStyle = color;
  ctx.fillRect(pos.x, pos.y, camera.tileW, camera.tileH);

  // Wall side
  if (tile === WALL) {
    ctx.fillStyle = Colors.WALL_SIDE;
    ctx.fillRect(pos.x, pos.y + camera.tileH - 4 * camera.zoom, camera.tileW, 4 * camera.zoom);
  }
}

function drawFire(hazard) {
  const pos = camera.toScreen(hazard.r, hazard.c);
  const cx = pos.x + camera.tileW / 2;
  const cy = pos.y + camera.tileH / 2;
  const time = performance.now() / 1000;

  const intensity = hazard.intensity / 50;
  const flicker = 0.7 + Math.sin(time * 12 + hazard.r + hazard.c) * 0.3;
  const size = (8 + intensity * 8) * camera.zoom * flicker;

  // Glow
  const grad = ctx.createRadialGradient(cx, cy, size * 0.3, cx, cy - 4, size * 2);
  grad.addColorStop(0, 'rgba(255, 220, 100, 0.9)');
  grad.addColorStop(0.4, 'rgba(255, 140, 50, 0.6)');
  grad.addColorStop(1, 'rgba(180, 50, 20, 0)');

  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.ellipse(cx, cy - 4, size * 1.5, size * 2, 0, 0, Math.PI * 2);
  ctx.fill();

  // Flame
  ctx.fillStyle = Colors.FIRE_BRIGHT;
  ctx.beginPath();
  ctx.moveTo(cx, cy - size * 1.5);
  ctx.lineTo(cx - size * 0.5, cy + size * 0.3);
  ctx.lineTo(cx + size * 0.5, cy + size * 0.3);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

function drawSmoke(smokeData) {
  for (const s of smokeData) {
    const pos = camera.toScreen(s.r, s.c);
    const alpha = Math.min(0.4, s.level * 0.3);
    const wobble = Math.sin(performance.now() / 600 + s.r * 0.5) * 0.1;

    ctx.fillStyle = `rgba(90, 95, 105, ${alpha + wobble})`;
    ctx.beginPath();
    ctx.ellipse(
      pos.x + camera.tileW / 2,
      pos.y + camera.tileH / 2,
      camera.tileW * 0.6,
      camera.tileH * 0.7,
      0, 0, Math.PI * 2
    );
    ctx.fill();
  }
}

function drawPredictions(predictions) {
  if (!overlayState.showPredictions) return;

  for (const pred of predictions) {
    const pos = camera.toScreen(pred.r, pred.c);
    const pulse = 0.5 + Math.sin(performance.now() / 200) * 0.3;
    const alpha = pred.prob * pulse * 0.5;

    ctx.fillStyle = `rgba(255, 50, 200, ${alpha})`;
    ctx.fillRect(pos.x, pos.y, camera.tileW, camera.tileH);

    // Border
    ctx.strokeStyle = `rgba(255, 100, 255, ${alpha + 0.2})`;
    ctx.lineWidth = 2;
    ctx.strokeRect(pos.x + 2, pos.y + 2, camera.tileW - 4, camera.tileH - 4);
  }
}

function drawPheromones(acoData) {
  if (!overlayState.showPheromones) return;

  // Safe pheromones (green)
  for (const p of acoData.safe || []) {
    const pos = camera.toScreen(p.r, p.c);
    const alpha = Math.min(0.4, (p.v - 0.3) * 0.15);
    ctx.fillStyle = `rgba(0, 255, 150, ${alpha})`;
    ctx.fillRect(pos.x, pos.y, camera.tileW, camera.tileH);
  }

  // Danger pheromones (red)
  for (const p of acoData.danger || []) {
    const pos = camera.toScreen(p.r, p.c);
    const alpha = Math.min(0.35, p.v * 0.05);
    ctx.fillStyle = `rgba(255, 80, 80, ${alpha})`;
    ctx.fillRect(pos.x, pos.y, camera.tileW, camera.tileH);
  }
}

function drawSensors(sensors) {
  if (!overlayState.showSensors) return;

  for (const s of sensors) {
    const pos = camera.toScreen(s.r, s.c);
    const cx = pos.x + camera.tileW / 2;
    const cy = pos.y + camera.tileH / 2;

    // Sensor dot
    ctx.fillStyle = s.triggered ? Colors.SENSOR_TRIGGERED : Colors.SENSOR_NORMAL;
    ctx.beginPath();
    ctx.arc(cx, cy, 5 * camera.zoom, 0, Math.PI * 2);
    ctx.fill();

    // Range circle
    ctx.strokeStyle = s.triggered ? 'rgba(255, 107, 107, 0.4)' : 'rgba(124, 214, 241, 0.25)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(cx, cy, 5 * camera.tileW, 0, Math.PI * 2);
    ctx.stroke();

    // Pulse if triggered
    if (s.triggered) {
      const pulseSize = ((performance.now() / 50) % 30) + 10;
      const pulseAlpha = 1 - pulseSize / 40;
      ctx.strokeStyle = `rgba(255, 107, 107, ${pulseAlpha})`;
      ctx.beginPath();
      ctx.arc(cx, cy, pulseSize * camera.zoom, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Type label
    ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
    ctx.font = `${10 * camera.zoom}px monospace`;
    const label = s.type === 'temperature' ? 'T' : s.type === 'smoke' ? 'S' : 'C';
    ctx.fillText(label, cx - 3 * camera.zoom, cy + 3 * camera.zoom);
  }
}

function drawPerson(p, timeVal) {
  const pos = camera.toScreen(p.exactR, p.exactC);
  if (pos.x < -50 || pos.x > screenWidth + 50) return;
  if (pos.y < -50 || pos.y > screenHeight + 50) return;

  const cx = pos.x + camera.tileW / 2;
  const cy = pos.y + camera.tileH / 2;
  const zoom = camera.zoom;

  if (!p.alive) {
    ctx.fillStyle = '#666';
    ctx.fillRect(cx - 8 * zoom, cy - 2 * zoom, 16 * zoom, 4 * zoom);
    return;
  }

  // Animation
  let bob = 0;
  if (p.state === 'evacuating' || p.state === 'panicking') {
    bob = Math.sin(timeVal * 10 + p.id) * 2 * zoom;
  }

  // Shadow
  ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
  ctx.beginPath();
  ctx.ellipse(cx, cy + 6 * zoom, 8 * zoom, 4 * zoom, 0, 0, Math.PI * 2);
  ctx.fill();

  // Body color based on state
  let bodyColor = Colors.WORKING;
  if (p.state === 'headphones') bodyColor = Colors.HEADPHONES;
  else if (p.state === 'evacuating') bodyColor = Colors.EVACUATING;
  else if (p.state === 'panicking') bodyColor = Colors.PANICKING;
  else if (p.state === 'aware') bodyColor = '#ffff6b';

  // Body
  ctx.fillStyle = bodyColor;
  ctx.beginPath();
  ctx.arc(cx, cy + bob, 8 * zoom, 0, Math.PI * 2);
  ctx.fill();

  // Head
  ctx.fillStyle = '#ffd6b1';
  ctx.beginPath();
  ctx.arc(cx, cy - 6 * zoom + bob, 5 * zoom, 0, Math.PI * 2);
  ctx.fill();

  // Selection indicator
  if (camera.target === p.id) {
    const arrowY = cy - 18 * zoom + Math.sin(timeVal * 5) * 4;
    ctx.fillStyle = '#ffd600';
    ctx.beginPath();
    ctx.moveTo(cx, arrowY + 8 * zoom);
    ctx.lineTo(cx - 6 * zoom, arrowY);
    ctx.lineTo(cx + 6 * zoom, arrowY);
    ctx.closePath();
    ctx.fill();
  }

  // Health bar
  if (p.health < 90) {
    const barW = 16 * zoom;
    const healthW = barW * (p.health / 100);
    ctx.fillStyle = '#600';
    ctx.fillRect(cx - barW / 2, cy - 14 * zoom + bob, barW, 3 * zoom);
    ctx.fillStyle = '#0c0';
    ctx.fillRect(cx - barW / 2, cy - 14 * zoom + bob, healthW, 3 * zoom);
  }
}

function drawNeuralConfidence(confidence) {
  // Draw confidence meter in corner
  const x = 20;
  const y = screenHeight - 100;
  const w = 150;
  const h = 20;

  ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
  ctx.fillRect(x - 5, y - 25, w + 10, h + 35);

  ctx.fillStyle = '#fff';
  ctx.font = '12px monospace';
  ctx.fillText('NEURAL CONFIDENCE', x, y - 8);

  ctx.fillStyle = '#333';
  ctx.fillRect(x, y, w, h);

  const confColor = confidence > 0.7 ? '#4f4' : confidence > 0.4 ? '#ff4' : '#f44';
  ctx.fillStyle = confColor;
  ctx.fillRect(x, y, w * confidence, h);

  ctx.fillStyle = '#fff';
  ctx.fillText(`${(confidence * 100).toFixed(0)}%`, x + w + 8, y + 15);
}

function draw() {
  ctx.clearRect(0, 0, screenWidth, screenHeight);

  // Background gradient
  const grd = ctx.createLinearGradient(0, 0, screenWidth, screenHeight);
  grd.addColorStop(0, '#0b1020');
  grd.addColorStop(1, '#080b12');
  ctx.fillStyle = grd;
  ctx.fillRect(0, 0, screenWidth, screenHeight);

  if (!simulationState) {
    ctx.fillStyle = '#fff';
    ctx.font = '24px sans-serif';
    ctx.fillText('Connecting to backend...', screenWidth / 2 - 120, screenHeight / 2);
    ctx.font = '14px sans-serif';
    ctx.fillText('Run: python backend_server.py', screenWidth / 2 - 100, screenHeight / 2 + 30);
    return;
  }

  const { maze, people, hazards, smoke, neural, sensors } = simulationState;

  // Draw tiles
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      drawTile(r, c, maze[r][c]);
    }
  }

  // Draw pheromones
  if (neural?.aco) {
    drawPheromones(neural.aco);
  }

  // Draw predictions
  if (neural?.predictions) {
    drawPredictions(neural.predictions);
  }

  // Draw smoke
  if (smoke) {
    drawSmoke(smoke);
  }

  // Draw fires
  for (const h of hazards || []) {
    drawFire(h);
  }

  // Draw sensors
  if (sensors?.list) {
    drawSensors(sensors.list);
  }

  // Draw people
  const timeVal = performance.now() / 1000;
  const sortedPeople = [...(people || [])].sort((a, b) => a.exactR - b.exactR);
  for (const p of sortedPeople) {
    drawPerson(p, timeVal);
  }

  // Draw neural confidence
  if (neural) {
    drawNeuralConfidence(neural.confidence);
  }

  // Connection status
  if (!connected) {
    ctx.fillStyle = 'rgba(255, 0, 0, 0.8)';
    ctx.fillRect(screenWidth - 150, 10, 140, 30);
    ctx.fillStyle = '#fff';
    ctx.font = '14px sans-serif';
    ctx.fillText('DISCONNECTED', screenWidth - 140, 30);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// HUD UPDATE
// ═══════════════════════════════════════════════════════════════════════════════

function updateHUD() {
  if (!setHudState || !simulationState) return;

  const { stats, neural, sensors, rl, alarm, people } = simulationState;

  setHudState({
    alive: stats?.alive || 0,
    escaped: stats?.escaped || 0,
    deaths: stats?.deaths || 0,
    hazards: simulationState.hazards?.length || 0,
    alarm: alarm,
    neural: {
      confidence: neural?.confidence || 0,
      predictions: neural?.predictions?.length || 0
    },
    sensors: {
      triggered: sensors?.fusion?.triggered_count || 0,
      total: sensors?.fusion?.total_sensors || 0,
      temp: sensors?.fusion?.temp_avg || 22,
      smoke: sensors?.fusion?.smoke_avg || 0
    },
    rl: rl || { decisions: 0, reward: 0 },
    aco: {
      safe: neural?.aco?.safe?.length || 0,
      danger: neural?.aco?.danger?.length || 0
    },
    target: camera.target !== null
      ? `Following Person ${camera.target}`
      : 'Click person to follow',
    connected: connected
  });

  // Sound management
  if (alarm && !sounds.alarm.playing()) {
    sounds.alarm.play();
  } else if (!alarm && sounds.alarm.playing()) {
    sounds.alarm.stop();
  }

  if (simulationState.hazards?.length > 0 && !sounds.fire.playing()) {
    sounds.fire.play();
  } else if (simulationState.hazards?.length === 0) {
    sounds.fire.stop();
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// INPUT HANDLING
// ═══════════════════════════════════════════════════════════════════════════════

const keysDown = new Set();

function handleKeyDown(e) {
  const k = e.key.toLowerCase();
  keysDown.add(k);

  if (k === ' ') {
    e.preventDefault();
    camera.target = null;
  }
  if (k === 'r') sendCommand('reset');
  if (k === 'a') sendCommand('trigger_alarm');
  if (k === 'p') overlayState.showPredictions = !overlayState.showPredictions;
  if (k === 't') overlayState.showPheromones = !overlayState.showPheromones;
  if (k === 'v') overlayState.showSensors = !overlayState.showSensors;
}

function handleKeyUp(e) {
  keysDown.delete(e.key.toLowerCase());
}

function handleCameraMovement(dt) {
  let dx = 0, dy = 0;
  const speed = 400 * dt;
  if (keysDown.has('w') || keysDown.has('arrowup')) dy -= speed;
  if (keysDown.has('s') || keysDown.has('arrowdown')) dy += speed;
  if (keysDown.has('a') || keysDown.has('arrowleft')) dx -= speed;
  if (keysDown.has('d') || keysDown.has('arrowright')) dx += speed;
  if (dx !== 0 || dy !== 0) camera.move(dx, dy);
}

canvas.addEventListener('mousedown', (e) => {
  const rect = canvas.getBoundingClientRect();
  const mx = ((e.clientX - rect.left) / rect.width) * canvas.width;
  const my = ((e.clientY - rect.top) / rect.height) * canvas.height;

  if (e.button === 2 || e.ctrlKey) {
    // Right click - add fire
    const gridR = Math.floor((my + camera.y) / camera.tileH);
    const gridC = Math.floor((mx + camera.x) / camera.tileW);
    sendCommand('add_fire', { r: gridR, c: gridC });
  } else {
    // Left click - select person
    if (simulationState?.people) {
      let bestDist = 40 * camera.zoom;
      let selected = null;

      for (const p of simulationState.people) {
        if (!p.alive) continue;
        const pos = camera.toScreen(p.exactR, p.exactC);
        const d = Math.hypot(
          pos.x + camera.tileW / 2 - mx,
          pos.y + camera.tileH / 2 - my
        );
        if (d < bestDist) {
          bestDist = d;
          selected = p;
        }
      }

      camera.target = selected ? selected.id : null;
    }
  }
});

canvas.addEventListener('wheel', (e) => {
  e.preventDefault();
  camera.applyZoom(-e.deltaY * 0.0015);
});

canvas.addEventListener('contextmenu', (e) => e.preventDefault());

window.addEventListener('keydown', handleKeyDown);
window.addEventListener('keyup', handleKeyUp);

// ═══════════════════════════════════════════════════════════════════════════════
// REACT HUD
// ═══════════════════════════════════════════════════════════════════════════════

function App({ onReset, onAlarm }) {
  const [hud, setHud] = React.useState(initialHud);
  setHudState = (next) => setHud((prev) => ({ ...prev, ...next }));

  return html`
    <div class="overlay">
      <div class="hud">
        <div class="hud__stats">
          <div class="chips">
            <span class="chip" style=${{ background: hud.connected ? 'rgba(0,255,100,0.2)' : 'rgba(255,0,0,0.3)' }}>
              ${hud.connected ? '● Connected' : '○ Disconnected'}
            </span>
            <span class="chip">Alive: ${hud.alive}</span>
            <span class="chip" style=${{ color: '#6f6' }}>Escaped: ${hud.escaped}</span>
            <span class="chip" style=${{ color: hud.deaths > 0 ? '#f66' : '#fff' }}>Deaths: ${hud.deaths}</span>
            <span class="chip" style=${{ color: hud.hazards > 0 ? '#f80' : '#fff' }}>Fires: ${hud.hazards}</span>
            <span class="chip" style=${{ color: hud.alarm ? '#f44' : '#888' }}>
              ${hud.alarm ? '🚨 ALARM' : 'Standby'}
            </span>
          </div>

          <div class="chips" style=${{ marginTop: '6px' }}>
            <span class="chip" style=${{ background: 'rgba(255,50,200,0.2)', borderColor: 'rgba(255,50,200,0.4)' }}>
              🧠 Neural: ${(hud.neural.confidence * 100).toFixed(0)}%
            </span>
            <span class="chip" style=${{ background: 'rgba(0,255,200,0.15)' }}>
              🔮 Predictions: ${hud.neural.predictions}
            </span>
            <span class="chip" style=${{ background: hud.sensors.triggered > 0 ? 'rgba(255,100,100,0.2)' : 'rgba(100,200,255,0.15)' }}>
              📡 Sensors: ${hud.sensors.triggered}/${hud.sensors.total}
            </span>
            <span class="chip">🌡️ ${hud.sensors.temp.toFixed(1)}°C</span>
            <span class="chip">💨 Smoke: ${hud.sensors.smoke.toFixed(2)}</span>
          </div>

          <div class="chips" style=${{ marginTop: '6px' }}>
            <span class="chip" style=${{ background: 'rgba(0,255,150,0.15)' }}>
              🐜 Safe trails: ${hud.aco.safe}
            </span>
            <span class="chip" style=${{ background: 'rgba(255,80,80,0.15)' }}>
              ⚠️ Danger zones: ${hud.aco.danger}
            </span>
            <span class="chip">🤖 RL: ${hud.rl.decisions} decisions</span>
          </div>

          <div class="controls">
            WASD pan · Scroll zoom · Click follow · Space free · Right-click fire · R reset · A alarm
            · P predictions · T pheromones · V sensors
          </div>
        </div>

        <div class="hud__actions">
          <button class="btn btn-secondary" onClick=${() => { overlayState.showPredictions = !overlayState.showPredictions; }}>
            Predictions (P)
          </button>
          <button class="btn btn-secondary" onClick=${() => { overlayState.showPheromones = !overlayState.showPheromones; }}>
            Pheromones (T)
          </button>
          <button class="btn btn-secondary" onClick=${() => { overlayState.showSensors = !overlayState.showSensors; }}>
            Sensors (V)
          </button>
          <button class="btn btn-secondary" onClick=${onAlarm}>Alarm (A)</button>
          <button class="btn btn-primary" onClick=${onReset}>Reset (R)</button>
        </div>
      </div>

      <div class="target-info">${hud.target}</div>
    </div>
  `;
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN LOOP
// ═══════════════════════════════════════════════════════════════════════════════

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  screenWidth = canvas.width;
  screenHeight = canvas.height;
}

resizeCanvas();
window.addEventListener('resize', resizeCanvas);

let lastTime = performance.now();

function loop(ts) {
  const dt = Math.min(0.05, (ts - lastTime) / 1000);
  lastTime = ts;

  handleCameraMovement(dt);
  camera.update();
  draw();

  requestAnimationFrame(loop);
}

// Initialize
const root = createRoot(document.getElementById('app'));
root.render(html`<${App}
  onReset=${() => sendCommand('reset')}
  onAlarm=${() => sendCommand('trigger_alarm')}
/>`);

// Load Socket.IO and connect
const script = document.createElement('script');
script.src = 'https://cdn.socket.io/4.7.2/socket.io.min.js';
script.onload = () => {
  connectWebSocket();
};
document.head.appendChild(script);

// Start render loop
requestAnimationFrame(loop);

console.log('DWIGHT UX Frontend loaded');
console.log('Run: python backend_server.py');
