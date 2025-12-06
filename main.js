/**
 * ╔═══════════════════════════════════════════════════════════════════════════════╗
 * ║  DWIGHT - DUNDER MIFFLIN EMERGENCY RESPONSE SYSTEM                            ║
 * ║  Neural ACO + IoT + Deep Learning Fire Safety Simulation                      ║
 * ╠═══════════════════════════════════════════════════════════════════════════════╣
 * ║  Features:                                                                    ║
 * ║  • Dunder Mifflin Scranton office layout from The Office                      ║
 * ║  • LSTM Neural Network for fire spread prediction                             ║
 * ║  • Ant Colony Optimization with neural-modulated pheromones                   ║
 * ║  • IoT sensor network with Kalman filtering                                   ║
 * ║  • Character-based employees with unique behaviors                            ║
 * ╚═══════════════════════════════════════════════════════════════════════════════╝
 */

import React from 'https://esm.sh/react@18.3.1';
import { createRoot } from 'https://esm.sh/react-dom@18.3.1/client';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(React.createElement);

// ═══════════════════════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════════

const TILE = 12;
const ROWS = 50;
const COLS = 80;

const canvas = document.getElementById('sim');
const ctx = canvas.getContext('2d');

let W = window.innerWidth;
let H = window.innerHeight;
let selectedDisaster = 'fire'; // fire | bomb | quake | flood

// Tile Types
const FLOOR = 0;
const WALL = 1;
const EXIT = 2;
const DOOR = 3;
const DESK = 4;
const CARPET = 5;
const KITCHEN = 6;
const BATHROOM = 7;
const WINDOW = 8;

// Room definitions for Dunder Mifflin
const ROOMS = {
  RECEPTION: 'Reception',
  MAIN_FLOOR: 'Sales Floor',
  MICHAEL_OFFICE: "Michael's Office",
  CONFERENCE: 'Conference Room',
  BREAK_ROOM: 'Break Room',
  ANNEX: 'Annex',
  ACCOUNTING: 'Accounting',
  WAREHOUSE_ENTRANCE: 'Warehouse',
  KITCHEN: 'Kitchen',
  BATHROOM: 'Restroom',
};

// The Office Characters
const CHARACTERS = [
  { name: 'Michael Scott', role: 'manager', color: '#4a90d9', desk: 'MICHAEL_OFFICE', traits: { panic: 0.8, speed: 0.9, awareness: 0.4 } },
  { name: 'Dwight Schrute', role: 'warden', color: '#8b4513', desk: 'MAIN_FLOOR', traits: { panic: 0.1, speed: 1.3, awareness: 1.0 } },
  { name: 'Jim Halpert', role: 'sales', color: '#5c9ead', desk: 'MAIN_FLOOR', traits: { panic: 0.2, speed: 1.1, awareness: 0.8 } },
  { name: 'Pam Beesly', role: 'reception', color: '#e8a0bf', desk: 'RECEPTION', traits: { panic: 0.3, speed: 0.9, awareness: 0.9 } },
  { name: 'Andy Bernard', role: 'sales', color: '#d4a574', desk: 'MAIN_FLOOR', traits: { panic: 0.6, speed: 0.85, awareness: 0.5 } },
  { name: 'Angela Martin', role: 'accounting', color: '#c9b1ff', desk: 'ACCOUNTING', traits: { panic: 0.4, speed: 0.8, awareness: 0.7 } },
  { name: 'Kevin Malone', role: 'accounting', color: '#90b77d', desk: 'ACCOUNTING', traits: { panic: 0.5, speed: 0.6, awareness: 0.3 } },
  { name: 'Oscar Martinez', role: 'accounting', color: '#7eb5a6', desk: 'ACCOUNTING', traits: { panic: 0.2, speed: 0.95, awareness: 0.85 } },
  { name: 'Stanley Hudson', role: 'sales', color: '#a0522d', desk: 'MAIN_FLOOR', traits: { panic: 0.1, speed: 0.5, awareness: 0.6 } },
  { name: 'Phyllis Vance', role: 'sales', color: '#dda0dd', desk: 'MAIN_FLOOR', traits: { panic: 0.4, speed: 0.7, awareness: 0.65 } },
  { name: 'Ryan Howard', role: 'temp', color: '#708090', desk: 'ANNEX', traits: { panic: 0.5, speed: 1.0, awareness: 0.5 } },
  { name: 'Kelly Kapoor', role: 'customer_service', color: '#ff69b4', desk: 'ANNEX', traits: { panic: 0.7, speed: 1.0, awareness: 0.4 } },
  { name: 'Toby Flenderson', role: 'hr', color: '#8fbc8f', desk: 'ANNEX', traits: { panic: 0.2, speed: 0.8, awareness: 0.75 } },
  { name: 'Creed Bratton', role: 'quality', color: '#696969', desk: 'MAIN_FLOOR', traits: { panic: 0.0, speed: 0.7, awareness: 0.2 } },
  { name: 'Meredith Palmer', role: 'supplier', color: '#cd5c5c', desk: 'MAIN_FLOOR', traits: { panic: 0.3, speed: 0.75, awareness: 0.4 } },
  { name: 'Darryl Philbin', role: 'warehouse', color: '#2f4f4f', desk: 'WAREHOUSE_ENTRANCE', traits: { panic: 0.15, speed: 1.1, awareness: 0.8 } },
];

// Colors
const Colors = {
  floor: '#c4bfb6',
  floorAlt: '#b8b3aa',
  carpet: '#3d5a80',
  carpetAlt: '#364f6b',
  wall: '#4a4a4a',
  wallTop: '#5a5a5a',
  desk: '#8b7355',
  deskTop: '#a08060',
  exit: '#32cd32',
  exitGlow: '#90ee90',
  door: '#6b4423',
  window: '#87ceeb',
  kitchen: '#d3d3d3',
  bathroom: '#e0e0e0',
  fire: '#ff4500',
  fireGlow: '#ff8c00',
  smoke: '#505050',
  safeTrail: 'rgba(0, 255, 150, 0.3)',
  dangerZone: 'rgba(255, 80, 80, 0.25)',
  prediction: 'rgba(255, 60, 200, 0.35)',
  sensor: '#00bfff',
  sensorTriggered: '#ff4444',
};

// ═══════════════════════════════════════════════════════════════════════════════
// NEURAL NETWORK - LSTM FIRE PREDICTOR
// ═══════════════════════════════════════════════════════════════════════════════

class LSTMPredictor {
  constructor() {
    this.hiddenSize = 24;
    this.hidden = new Float32Array(this.hiddenSize);
    this.cell = new Float32Array(this.hiddenSize);
    this.history = [];
    this.confidence = 0;

    // Pre-trained weights (simplified)
    this.initWeights();
  }

  initWeights() {
    const hs = this.hiddenSize;
    const inputSize = 6;
    this.Wf = this.randomMatrix(hs, hs + inputSize, 0.1);
    this.Wi = this.randomMatrix(hs, hs + inputSize, 0.1);
    this.Wo = this.randomMatrix(hs, hs + inputSize, 0.1);
    this.Wc = this.randomMatrix(hs, hs + inputSize, 0.1);
    this.Wp = this.randomMatrix(4, hs, 0.1);
  }

  randomMatrix(rows, cols, scale) {
    const m = [];
    for (let i = 0; i < rows; i++) {
      m[i] = [];
      for (let j = 0; j < cols; j++) {
        m[i][j] = (Math.random() - 0.5) * scale * 2;
      }
    }
    return m;
  }

  sigmoid(x) { return 1 / (1 + Math.exp(-Math.max(-500, Math.min(500, x)))); }
  tanh(x) { return Math.tanh(Math.max(-500, Math.min(500, x))); }

  matVec(mat, vec) {
    return mat.map(row => row.reduce((sum, w, i) => sum + w * (vec[i] || 0), 0));
  }

  predict(firePositions, smokeData) {
    if (firePositions.length === 0) {
      this.confidence = 0;
      return [];
    }

    // Extract features
    const centerR = firePositions.reduce((s, f) => s + f.r, 0) / firePositions.length;
    const centerC = firePositions.reduce((s, f) => s + f.c, 0) / firePositions.length;
    const fireCount = Math.min(firePositions.length / 10, 1);
    const avgIntensity = firePositions.reduce((s, f) => s + f.intensity, 0) / firePositions.length / 50;

    let spreadR = 0, spreadC = 0;
    if (this.history.length > 0) {
      const prev = this.history[this.history.length - 1];
      spreadR = (centerR - prev.r) / ROWS;
      spreadC = (centerC - prev.c) / COLS;
    }
    this.history.push({ r: centerR, c: centerC });
    if (this.history.length > 10) this.history.shift();

    const input = [centerR / ROWS, centerC / COLS, spreadR, spreadC, fireCount, avgIntensity];
    const concat = [...this.hidden, ...input];

    // LSTM forward pass
    const ft = this.matVec(this.Wf, concat).map(x => this.sigmoid(x));
    const it = this.matVec(this.Wi, concat).map(x => this.sigmoid(x));
    const ot = this.matVec(this.Wo, concat).map(x => this.sigmoid(x));
    const ct = this.matVec(this.Wc, concat).map(x => this.tanh(x));

    for (let i = 0; i < this.hiddenSize; i++) {
      this.cell[i] = ft[i] * this.cell[i] + it[i] * ct[i];
      this.hidden[i] = ot[i] * this.tanh(this.cell[i]);
    }

    // Predict spread directions
    const dirProbs = this.matVec(this.Wp, Array.from(this.hidden)).map(x => this.sigmoid(x));
    this.confidence = Math.max(...dirProbs);

    // Generate predictions
    const predictions = [];
    const dirs = [[-1, 0], [1, 0], [0, -1], [0, 1]];

    for (const fire of firePositions) {
      for (let d = 0; d < 4; d++) {
        if (dirProbs[d] > 0.25) {
          for (let step = 1; step <= 3; step++) {
            const nr = fire.r + dirs[d][0] * step;
            const nc = fire.c + dirs[d][1] * step;
            if (nr > 0 && nr < ROWS - 1 && nc > 0 && nc < COLS - 1) {
              predictions.push({ r: nr, c: nc, prob: dirProbs[d] * Math.pow(0.7, step) });
            }
          }
        }
      }
    }

    return predictions;
  }

  reset() {
    this.hidden.fill(0);
    this.cell.fill(0);
    this.history = [];
    this.confidence = 0;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// NEURAL ANT COLONY OPTIMIZATION
// ═══════════════════════════════════════════════════════════════════════════════

class NeuralACO {
  constructor(lstm) {
    this.lstm = lstm;
    this.safePheromone = this.createGrid(0.1);
    this.dangerPheromone = this.createGrid(0);
    this.predictedDanger = this.createGrid(0);
    this.evaporationRate = 0.02;
  }

  createGrid(val) {
    return Array.from({ length: ROWS }, () => Array(COLS).fill(val));
  }

  updatePredictions(fires, smoke, maze) {
    const predictions = this.lstm.predict(fires, smoke);

    // Decay predicted danger
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        this.predictedDanger[r][c] *= 0.85;
      }
    }

    // Apply new predictions
    for (const pred of predictions) {
      const modulated = pred.prob * (0.5 + 0.5 * this.lstm.confidence);
      this.predictedDanger[pred.r][pred.c] = Math.max(this.predictedDanger[pred.r][pred.c], modulated);
      this.dangerPheromone[pred.r][pred.c] += modulated * 1.5;
    }

    return predictions;
  }

  depositSafe(path) {
    if (!path || path.length === 0) return;
    const amount = 1.0 + this.lstm.confidence * 0.5;
    for (let i = 0; i < path.length; i++) {
      const decay = 1 - (i / path.length) * 0.5;
      const [r, c] = path[i];
      this.safePheromone[r][c] = Math.min(this.safePheromone[r][c] + amount * decay, 8);
    }
  }

  depositDanger(r, c, severity) {
    this.dangerPheromone[r][c] = Math.min(this.dangerPheromone[r][c] + severity, 15);
    for (let dr = -2; dr <= 2; dr++) {
      for (let dc = -2; dc <= 2; dc++) {
        const nr = r + dr, nc = c + dc;
        if (nr >= 0 && nr < ROWS && nc >= 0 && nc < COLS) {
          const dist = Math.abs(dr) + Math.abs(dc);
          this.dangerPheromone[nr][nc] += severity * 0.2 / (dist + 1);
        }
      }
    }
  }

  evaporate() {
    const safeRate = this.evaporationRate * (1 - this.lstm.confidence * 0.3);
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        this.safePheromone[r][c] = Math.max(0.1, this.safePheromone[r][c] * (1 - safeRate));
        this.dangerPheromone[r][c] *= (1 - this.evaporationRate * 1.2);
      }
    }
  }

  getPathCost(r, c) {
    const danger = this.dangerPheromone[r][c] + this.predictedDanger[r][c] * 2;
    const safe = this.safePheromone[r][c];
    return 1 + danger * 10 - safe * 0.3;
  }

  reset() {
    this.safePheromone = this.createGrid(0.1);
    this.dangerPheromone = this.createGrid(0);
    this.predictedDanger = this.createGrid(0);
    this.lstm.reset();
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// IOT SENSOR NETWORK
// ═══════════════════════════════════════════════════════════════════════════════

class IoTSensor {
  constructor(id, r, c, type) {
    this.id = id;
    this.r = r;
    this.c = c;
    this.type = type; // 'temp', 'smoke', 'motion'
    this.value = type === 'temp' ? 22 : 0;
    this.triggered = false;
    this.threshold = type === 'temp' ? 45 : type === 'smoke' ? 0.3 : 0.5;
    this.kalmanState = { estimate: this.value, error: 1 };
  }

  update(fires, smoke, people) {
    let raw = 0;

    if (this.type === 'temp') {
      raw = 22;
      for (const fire of fires) {
        const dist = Math.abs(this.r - fire.r) + Math.abs(this.c - fire.c);
        if (dist < 12) raw += (fire.intensity * 2) / (dist + 1);
      }
      raw = Math.min(raw, 150);
    } else if (this.type === 'smoke') {
      raw = smoke[this.r]?.[this.c] || 0;
    } else if (this.type === 'motion') {
      for (const p of people) {
        if (p.alive && !p.escaped) {
          const dist = Math.abs(this.r - p.r) + Math.abs(this.c - p.c);
          if (dist < 5) raw += 1 / (dist + 1);
        }
      }
    }

    // Kalman filter
    const noise = (Math.random() - 0.5) * 0.5;
    const measurement = raw + noise;
    const gain = this.kalmanState.error / (this.kalmanState.error + 0.1);
    this.kalmanState.estimate += gain * (measurement - this.kalmanState.estimate);
    this.kalmanState.error = (1 - gain) * this.kalmanState.error + 0.01;

    this.value = this.kalmanState.estimate;
    this.triggered = this.value > this.threshold;
  }
}

class SensorNetwork {
  constructor() {
    this.sensors = [];
  }

  addSensor(r, c, type) {
    this.sensors.push(new IoTSensor(this.sensors.length, r, c, type));
  }

  update(fires, smoke, people) {
    for (const s of this.sensors) {
      s.update(fires, smoke, people);
    }
  }

  getTriggeredCount() {
    return this.sensors.filter(s => s.triggered).length;
  }

  getAvgTemp() {
    const temps = this.sensors.filter(s => s.type === 'temp');
    if (temps.length === 0) return 22;
    return temps.reduce((sum, s) => sum + s.value, 0) / temps.length;
  }

  reset() {
    for (const s of this.sensors) {
      s.value = s.type === 'temp' ? 22 : 0;
      s.triggered = false;
      s.kalmanState = { estimate: s.value, error: 1 };
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// DUNDER MIFFLIN OFFICE LAYOUT
// ═══════════════════════════════════════════════════════════════════════════════

function createDunderMifflinOffice() {
  const maze = Array.from({ length: ROWS }, () => Array(COLS).fill(FLOOR));
  const roomPositions = {};

  // Helper functions
  const fillRect = (r1, c1, r2, c2, tile) => {
    for (let r = r1; r <= r2; r++) {
      for (let c = c1; c <= c2; c++) {
        if (r >= 0 && r < ROWS && c >= 0 && c < COLS) maze[r][c] = tile;
      }
    }
  };

  const drawWalls = (r1, c1, r2, c2) => {
    for (let c = c1; c <= c2; c++) { maze[r1][c] = WALL; maze[r2][c] = WALL; }
    for (let r = r1; r <= r2; r++) { maze[r][c1] = WALL; maze[r][c2] = WALL; }
  };

  const addDoor = (r, c) => { maze[r][c] = DOOR; };
  const addDesk = (r, c) => { maze[r][c] = DESK; };

  // Outer walls
  drawWalls(0, 0, ROWS - 1, COLS - 1);

  // Main floor carpet
  fillRect(1, 1, ROWS - 2, COLS - 2, CARPET);

  // ═══════════════════════════════════════════════════════════════════════════
  // RECEPTION AREA (Front, left side)
  // ═══════════════════════════════════════════════════════════════════════════
  drawWalls(1, 1, 12, 20);
  fillRect(2, 2, 11, 19, FLOOR);
  addDoor(12, 10);
  addDesk(6, 8); addDesk(6, 9); addDesk(6, 10); // Pam's reception desk
  roomPositions.RECEPTION = { r: 6, c: 10 };

  // Main entrance
  maze[6][1] = EXIT;
  maze[7][1] = EXIT;

  // ═══════════════════════════════════════════════════════════════════════════
  // MICHAEL'S OFFICE (Top left corner)
  // ═══════════════════════════════════════════════════════════════════════════
  drawWalls(1, 22, 14, 38);
  fillRect(2, 23, 13, 37, CARPET);
  addDoor(14, 30);
  addDesk(5, 30); addDesk(5, 31); addDesk(6, 30); addDesk(6, 31); // Michael's desk
  maze[3][23] = WINDOW; maze[3][24] = WINDOW; maze[3][25] = WINDOW; // Windows
  roomPositions.MICHAEL_OFFICE = { r: 6, c: 30 };

  // ═══════════════════════════════════════════════════════════════════════════
  // CONFERENCE ROOM (Next to Michael's office)
  // ═══════════════════════════════════════════════════════════════════════════
  drawWalls(1, 40, 14, 58);
  fillRect(2, 41, 13, 57, FLOOR);
  addDoor(14, 48);
  // Conference table
  fillRect(5, 46, 10, 52, DESK);
  roomPositions.CONFERENCE = { r: 7, c: 50 };

  // ═══════════════════════════════════════════════════════════════════════════
  // MAIN SALES FLOOR (Center of office)
  // ═══════════════════════════════════════════════════════════════════════════
  // Jim & Dwight's desks (facing each other)
  addDesk(20, 25); addDesk(20, 26); addDesk(21, 25); addDesk(21, 26);
  addDesk(20, 28); addDesk(20, 29); addDesk(21, 28); addDesk(21, 29);
  roomPositions.JIM_DESK = { r: 20, c: 26 };
  roomPositions.DWIGHT_DESK = { r: 21, c: 28 };

  // Stanley & Phyllis desks
  addDesk(20, 35); addDesk(20, 36); addDesk(21, 35); addDesk(21, 36);
  addDesk(20, 38); addDesk(20, 39); addDesk(21, 38); addDesk(21, 39);

  // Andy's desk
  addDesk(25, 25); addDesk(25, 26); addDesk(26, 25); addDesk(26, 26);

  // Creed & Meredith
  addDesk(25, 35); addDesk(25, 36); addDesk(26, 35); addDesk(26, 36);

  roomPositions.MAIN_FLOOR = { r: 23, c: 32 };

  // ═══════════════════════════════════════════════════════════════════════════
  // ACCOUNTING (Right side, enclosed)
  // ═══════════════════════════════════════════════════════════════════════════
  drawWalls(16, 55, 30, 78);
  fillRect(17, 56, 29, 77, CARPET);
  addDoor(23, 55);
  // Angela, Kevin, Oscar desks
  addDesk(20, 60); addDesk(20, 61); addDesk(21, 60); addDesk(21, 61);
  addDesk(20, 65); addDesk(20, 66); addDesk(21, 65); addDesk(21, 66);
  addDesk(24, 60); addDesk(24, 61); addDesk(25, 60); addDesk(25, 61);
  roomPositions.ACCOUNTING = { r: 22, c: 65 };

  // ═══════════════════════════════════════════════════════════════════════════
  // BREAK ROOM / KITCHEN (Back area)
  // ═══════════════════════════════════════════════════════════════════════════
  drawWalls(32, 1, 44, 25);
  fillRect(33, 2, 43, 24, KITCHEN);
  addDoor(32, 12);
  // Vending machines, fridge etc
  maze[35][3] = DESK; maze[36][3] = DESK;
  maze[35][5] = DESK; maze[36][5] = DESK;
  roomPositions.BREAK_ROOM = { r: 38, c: 12 };
  roomPositions.KITCHEN = { r: 38, c: 12 };

  // ═══════════════════════════════════════════════════════════════════════════
  // ANNEX (Kelly, Ryan, Toby area - back right)
  // ═══════════════════════════════════════════════════════════════════════════
  drawWalls(32, 40, 44, 65);
  fillRect(33, 41, 43, 64, CARPET);
  addDoor(32, 52);
  // Desks
  addDesk(36, 45); addDesk(36, 46); addDesk(37, 45); addDesk(37, 46);
  addDesk(36, 55); addDesk(36, 56); addDesk(37, 55); addDesk(37, 56);
  addDesk(40, 50); addDesk(40, 51); addDesk(41, 50); addDesk(41, 51);
  roomPositions.ANNEX = { r: 38, c: 52 };

  // ═══════════════════════════════════════════════════════════════════════════
  // BATHROOMS (Near break room)
  // ═══════════════════════════════════════════════════════════════════════════
  drawWalls(32, 27, 40, 38);
  fillRect(33, 28, 39, 37, BATHROOM);
  addDoor(32, 32);
  roomPositions.BATHROOM = { r: 36, c: 32 };

  // ═══════════════════════════════════════════════════════════════════════════
  // WAREHOUSE ENTRANCE (Back)
  // ═══════════════════════════════════════════════════════════════════════════
  maze[ROWS - 2][35] = EXIT;
  maze[ROWS - 2][36] = EXIT;
  maze[ROWS - 2][37] = EXIT;
  roomPositions.WAREHOUSE_ENTRANCE = { r: ROWS - 3, c: 36 };

  // Side exit (fire exit)
  maze[25][COLS - 2] = EXIT;
  maze[26][COLS - 2] = EXIT;

  return { maze, roomPositions };
}

// ═══════════════════════════════════════════════════════════════════════════════
// PERSON CLASS (Office Employee)
// ═══════════════════════════════════════════════════════════════════════════════

class Person {
  constructor(id, charData, startPos) {
    this.id = id;
    this.name = charData.name;
    this.role = charData.role;
    this.color = charData.color;
    this.traits = charData.traits;

    this.r = startPos.r;
    this.c = startPos.c;
    this.exactR = startPos.r;
    this.exactC = startPos.c;

    this.alive = true;
    this.escaped = false;
    this.health = 100;
    this.state = 'working'; // working, aware, evacuating, panicking
    this.awareness = charData.role === 'warden' ? 1.0 : 0;
    this.path = [];
    this.pathIndex = 0;
    this.thought = this.getWorkingThought();
    this.thoughtTimer = 3;
  }

  getWorkingThought() {
    const thoughts = {
      manager: ["That's what she said!", "Big boss energy", "World's best boss (self-awarded)"],
      warden: ["Bears. Beets. Battlestar Galactica.", "MICHAEL!", "Fire drills are my cardio"],
      sales: ["Big sale coming", "Dialing for dollars", "Working on leads"],
      reception: ["Dunder Mifflin, this is Pam", "Color-coding forms", "Sketching on sticky notes"],
      accounting: ["Crunching numbers", "Balancing books", "Tax season..."],
      hr: ["Nobody likes HR", "Filing complaint", "Mediation time"],
      temp: ["I'm a temp", "Business school", "Fire Guy was ONE time"],
      customer_service: ["OMG did you hear", "So anyway...", "Fashion emergency"],
      warehouse: ["Moving boxes", "Forklift time", "Warehouse hustle"],
      default: ["Working...", "Busy busy", "Almost Friday"]
    };
    return thoughts[this.role]?.[Math.floor(Math.random() * thoughts[this.role].length)] || thoughts.default[0];
  }

  getPanicThought() {
    const thoughts = {
      manager: ["EVERYBODY STAY CALM!", "I DECLARE EVACUATE!", "Not again!"],
      warden: ["Follow me! I know the exits!", "Stay low!", "I trained for this!"],
      sales: ["Where's the exit?!", "Not my commission!", "Run!"],
      reception: ["Phones down—move!", "Jim, this way!", "Pam sprinting!"],
      accounting: ["Save the ledgers!", "Receipts later—run now!", "Do not trip, Kevin!"],
      default: ["FIRE!", "Help!", "Where do I go?!", "Stay calm stay calm"]
    };
    return thoughts[this.role]?.[Math.floor(Math.random() * (thoughts[this.role]?.length || 1))] ||
           thoughts.default[Math.floor(Math.random() * thoughts.default.length)];
  }

  update(dt, maze, fires, smoke, people, exits, aco, alarmActive) {
    if (!this.alive || this.escaped) return;

    this.thoughtTimer -= dt;

    // Damage from fire
    const fireHere = fires.find(f => f.r === this.r && f.c === this.c);
    if (fireHere) {
      this.health -= 25 * dt;
      this.state = 'panicking';
    }

    // Smoke damage
    const smokeLevel = smoke[this.r]?.[this.c] || 0;
    if (smokeLevel > 0.5) {
      this.health -= smokeLevel * 8 * dt;
    }

    if (this.health <= 0) {
      this.alive = false;
      aco.depositDanger(this.r, this.c, 30);
      return;
    }

    // Check escape
    if (maze[this.r][this.c] === EXIT) {
      this.escaped = true;
      this.thought = "Made it out!";
      aco.depositSafe(this.path.slice(0, this.pathIndex));
      return;
    }

    // Awareness update
    if (this.state === 'working') {
      if (alarmActive) {
        const rate = this.role === 'warden' ? 0.5 : 0.15 * this.traits.awareness;
        this.awareness += rate * dt;
      }

      for (const fire of fires) {
        const dist = Math.abs(this.r - fire.r) + Math.abs(this.c - fire.c);
        if (dist < 10) {
          this.awareness += (0.3 * this.traits.awareness) / (dist + 1) * dt;
        }
      }

      if (this.awareness >= 0.7) {
        this.state = Math.random() < this.traits.panic ? 'panicking' : 'aware';
        this.thought = this.getPanicThought();
      }
    }

    if (this.state === 'aware') {
      this.state = 'evacuating';
    }

    // Movement
    if (this.state === 'evacuating' || this.state === 'panicking') {
      if (!this.path.length || this.pathIndex >= this.path.length) {
        this.findPath(maze, exits, fires, aco);
      }

      if (this.path.length && this.pathIndex < this.path.length) {
        const [nr, nc] = this.path[this.pathIndex];
        const speed = 3.5 * this.traits.speed * (this.state === 'panicking' ? 1.3 : 1);

        const dr = nr - this.exactR;
        const dc = nc - this.exactC;
        const dist = Math.hypot(dr, dc);

        if (dist > 0) {
          const move = Math.min(dist, speed * dt);
          this.exactR += (dr / dist) * move;
          this.exactC += (dc / dist) * move;
          this.r = Math.round(this.exactR);
          this.c = Math.round(this.exactC);

          if (dist < 0.15) this.pathIndex++;
        }
      }

      if (this.thoughtTimer <= 0) {
        this.thought = this.getPanicThought();
        this.thoughtTimer = 2 + Math.random() * 2;
      }
    } else {
      if (this.thoughtTimer <= 0) {
        this.thought = this.getWorkingThought();
        this.thoughtTimer = 4 + Math.random() * 3;
      }
    }
  }

  findPath(maze, exits, fires, aco) {
    const fireSet = new Set(fires.map(f => `${f.r},${f.c}`));

    // Find best exit
    let bestExit = null;
    let bestScore = Infinity;
    for (const exit of exits) {
      const dist = Math.abs(this.r - exit.r) + Math.abs(this.c - exit.c);
      let danger = 0;
      for (const fire of fires) {
        const fireDist = Math.abs(exit.r - fire.r) + Math.abs(exit.c - fire.c);
        if (fireDist < 8) danger += 50;
      }
      const score = dist + danger;
      if (score < bestScore) {
        bestScore = score;
        bestExit = exit;
      }
    }

    if (!bestExit) return;

    // A* pathfinding with ACO costs
    const open = [{ r: this.r, c: this.c, g: 0, f: 0, parent: null }];
    const closed = new Set();
    const cameFrom = new Map();

    while (open.length > 0) {
      open.sort((a, b) => a.f - b.f);
      const current = open.shift();
      const key = `${current.r},${current.c}`;

      if (current.r === bestExit.r && current.c === bestExit.c) {
        // Reconstruct path
        this.path = [];
        let node = current;
        while (node) {
          this.path.unshift([node.r, node.c]);
          node = cameFrom.get(`${node.r},${node.c}`);
        }
        this.pathIndex = 0;
        return;
      }

      if (closed.has(key)) continue;
      closed.add(key);

      for (const [dr, dc] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) {
        const nr = current.r + dr;
        const nc = current.c + dc;
        const nkey = `${nr},${nc}`;

        if (nr < 0 || nr >= ROWS || nc < 0 || nc >= COLS) continue;
        if (closed.has(nkey)) continue;

        const tile = maze[nr][nc];
        if (tile === WALL || tile === DESK || tile === WINDOW) continue;

        let cost = 1;
        if (fireSet.has(nkey)) cost += 200;
        cost += aco.getPathCost(nr, nc);

        const g = current.g + cost;
        const h = Math.abs(nr - bestExit.r) + Math.abs(nc - bestExit.c);
        const f = g + h;

        const existing = open.find(n => n.r === nr && n.c === nc);
        if (!existing || g < existing.g) {
          if (existing) {
            existing.g = g;
            existing.f = f;
          } else {
            open.push({ r: nr, c: nc, g, f, parent: current });
          }
          cameFrom.set(nkey, current);
        }
      }
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// FIRE & HAZARD SYSTEM
// ═══════════════════════════════════════════════════════════════════════════════

class Fire {
  constructor(r, c, intensity = 40) {
    this.r = r;
    this.c = c;
    this.intensity = intensity;
    this.age = 0;
  }
}

class Rubble {
  constructor(r, c, duration = 30) {
    this.r = r;
    this.c = c;
    this.duration = duration;
    this.age = 0;
  }
}

class FloodTile {
  constructor(r, c, depth = 0.5) {
    this.r = r;
    this.c = c;
    this.depth = depth;
    this.age = 0;
  }
}

class HazardSystem {
  constructor() {
    this.fires = [];
    this.smoke = Array.from({ length: ROWS }, () => Array(COLS).fill(0));
    this.rubble = [];
    this.flood = [];
    this.earthquakeActive = false;
    this.earthquakeIntensity = 0;
    this.earthquakeTimer = 0;
    this.bombExplosions = [];
    this.currentDisaster = 'fire'; // fire, earthquake, bomb, flood
  }

  addFire(r, c) {
    if (!this.fires.find(f => f.r === r && f.c === c)) {
      this.fires.push(new Fire(r, c));
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // EARTHQUAKE SYSTEM
  // ═══════════════════════════════════════════════════════════════════════════
  triggerEarthquake(intensity = 8) {
    this.earthquakeActive = true;
    this.earthquakeIntensity = intensity;
    this.earthquakeTimer = 5 + Math.random() * 3; // 5-8 seconds

    // Create rubble at random locations
    const rubbleCount = Math.floor(intensity * 3);
    for (let i = 0; i < rubbleCount; i++) {
      const r = Math.floor(Math.random() * (ROWS - 4)) + 2;
      const c = Math.floor(Math.random() * (COLS - 4)) + 2;
      if (!this.rubble.find(rb => rb.r === r && rb.c === c)) {
        this.rubble.push(new Rubble(r, c, 20 + Math.random() * 20));
      }
    }

    // Stun nearby people
    for (const person of people) {
      if (person.alive && !person.escaped) {
        person.stunned = true;
        person.stunnedTimer = 1 + Math.random() * 2;
        person.state = 'panicking';
        person.thought = 'EARTHQUAKE!!!';
      }
    }
  }

  updateEarthquake(dt) {
    if (!this.earthquakeActive) return;

    this.earthquakeTimer -= dt;
    this.earthquakeIntensity *= 0.98;

    if (this.earthquakeTimer <= 0 || this.earthquakeIntensity < 0.5) {
      this.earthquakeActive = false;
      this.earthquakeIntensity = 0;
    }

    // Update rubble
    for (const rb of this.rubble) {
      rb.age += dt;
    }
    this.rubble = this.rubble.filter(rb => rb.age < rb.duration);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // BOMB SYSTEM
  // ═══════════════════════════════════════════════════════════════════════════
  triggerBomb(r, c, radius = 6) {
    // Create explosion effect
    this.bombExplosions.push({
      r, c, radius,
      age: 0,
      maxAge: 1.5
    });

    // Create fires at explosion site
    for (let dr = -radius; dr <= radius; dr++) {
      for (let dc = -radius; dc <= radius; dc++) {
        const nr = r + dr, nc = c + dc;
        const dist = Math.hypot(dr, dc);
        if (dist <= radius && nr > 0 && nr < ROWS - 1 && nc > 0 && nc < COLS - 1) {
          if (Math.random() < 0.4) {
            this.addFire(nr, nc);
          }
          if (dist < radius / 2 && Math.random() < 0.6) {
            this.rubble.push(new Rubble(nr, nc, 30 + Math.random() * 20));
          }
        }
      }
    }

    // Stun and damage people in blast radius
    for (const person of people) {
      if (person.alive && !person.escaped) {
        const dist = Math.hypot(person.r - r, person.c - c);
        if (dist <= radius * 2) {
          const damage = Math.max(0, 80 - dist * 10);
          person.health -= damage;
          person.stunned = true;
          person.stunnedTimer = 2 + Math.random();
          person.state = 'panicking';
          person.thought = 'EXPLOSION!!!';
        }
      }
    }
  }

  updateBombs(dt) {
    for (const exp of this.bombExplosions) {
      exp.age += dt;
    }
    this.bombExplosions = this.bombExplosions.filter(e => e.age < e.maxAge);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // FLOOD SYSTEM
  // ═══════════════════════════════════════════════════════════════════════════
  triggerFlood(startR, startC) {
    // Initial flood point
    this.flood.push(new FloodTile(startR, startC, 1.0));
    this.floodActive = true;
  }

  updateFlood(dt, maze, aco) {
    if (this.flood.length === 0) {
      this.floodActive = false;
      return;
    }

    // Spread flood water
    const newFlood = [];
    for (const tile of this.flood) {
      tile.age += dt;
      tile.depth = Math.max(0.1, tile.depth - 0.01 * dt);

      if (tile.depth > 0.3 && Math.random() < 0.03 * dt) {
        for (const [dr, dc] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) {
          const nr = tile.r + dr, nc = tile.c + dc;
          if (nr > 0 && nr < ROWS - 1 && nc > 0 && nc < COLS - 1) {
            const mazeTile = maze[nr][nc];
            if (mazeTile !== WALL && mazeTile !== WINDOW && mazeTile !== DESK) {
              if (!this.flood.find(f => f.r === nr && f.c === nc) &&
                  !newFlood.find(f => f.r === nr && f.c === nc)) {
                newFlood.push(new FloodTile(nr, nc, tile.depth * 0.85));
              }
            }
          }
        }
      }

      // Flood deposits danger pheromones
      aco.depositDanger(tile.r, tile.c, 0.5 * dt);
    }

    this.flood.push(...newFlood);

    // Remove very shallow water
    this.flood = this.flood.filter(f => f.depth > 0.05);

    // Flood can extinguish fires
    for (const floodTile of this.flood) {
      const fireIdx = this.fires.findIndex(f => f.r === floodTile.r && f.c === floodTile.c);
      if (fireIdx !== -1) {
        this.fires[fireIdx].intensity -= floodTile.depth * 20 * dt;
      }
    }
  }

  isFlooded(r, c) {
    const tile = this.flood.find(f => f.r === r && f.c === c);
    return tile ? tile.depth : 0;
  }

  isRubble(r, c) {
    return this.rubble.some(rb => rb.r === r && rb.c === c);
  }

  update(dt, maze, aco) {
    // Update smoke
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        this.smoke[r][c] *= 0.97;
      }
    }

    const newFires = [];
    const toRemove = [];

    for (const fire of this.fires) {
      fire.age += dt;
      fire.intensity -= 2 * dt;

      if (fire.intensity <= 0) {
        toRemove.push(fire);
        continue;
      }

      // Generate smoke
      for (let dr = -4; dr <= 4; dr++) {
        for (let dc = -4; dc <= 4; dc++) {
          const nr = fire.r + dr, nc = fire.c + dc;
          if (nr >= 0 && nr < ROWS && nc >= 0 && nc < COLS) {
            const dist = Math.abs(dr) + Math.abs(dc);
            this.smoke[nr][nc] = Math.min(this.smoke[nr][nc] + fire.intensity * 0.01 / (dist + 1), 1.5);
          }
        }
      }

      // Spread fire
      if (fire.intensity > 25 && Math.random() < 0.015 * dt) {
        for (const [dr, dc] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) {
          const nr = fire.r + dr, nc = fire.c + dc;
          if (nr > 0 && nr < ROWS - 1 && nc > 0 && nc < COLS - 1) {
            const tile = maze[nr][nc];
            if (tile !== WALL && tile !== WINDOW && !this.fires.find(f => f.r === nr && f.c === nc)) {
              newFires.push(new Fire(nr, nc, fire.intensity * 0.7));
              break;
            }
          }
        }
      }

      aco.depositDanger(fire.r, fire.c, 1.5 * dt);
    }

    for (const fire of toRemove) {
      const idx = this.fires.indexOf(fire);
      if (idx !== -1) this.fires.splice(idx, 1);
    }

    this.fires.push(...newFires);

    // Update other disaster systems
    this.updateEarthquake(dt);
    this.updateBombs(dt);
    this.updateFlood(dt, maze, aco);
  }

  reset() {
    this.fires = [];
    this.smoke = Array.from({ length: ROWS }, () => Array(COLS).fill(0));
    this.rubble = [];
    this.flood = [];
    this.earthquakeActive = false;
    this.earthquakeIntensity = 0;
    this.earthquakeTimer = 0;
    this.bombExplosions = [];
    this.floodActive = false;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN SIMULATION
// ═══════════════════════════════════════════════════════════════════════════════

// Create systems
const lstm = new LSTMPredictor();
const aco = new NeuralACO(lstm);
const hazards = new HazardSystem();
const sensors = new SensorNetwork();

let { maze, roomPositions } = createDunderMifflinOffice();
let people = [];
let exits = [];
let predictions = [];
let alarmActive = false;
let paused = false;

// Camera
const camera = {
  x: 0, y: 0, zoom: 1,
  target: null,
  toScreen(r, c) {
    return {
      x: c * TILE * this.zoom - this.x,
      y: r * TILE * this.zoom - this.y
    };
  }
};

// Initialize
function init() {
  // Find exits
  exits = [];
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      if (maze[r][c] === EXIT) exits.push({ r, c });
    }
  }

  // Spawn people
  people = [];
  for (let i = 0; i < CHARACTERS.length; i++) {
    const char = CHARACTERS[i];
    const roomPos = roomPositions[char.desk] || roomPositions.MAIN_FLOOR;
    const offsetR = Math.floor(Math.random() * 3) - 1;
    const offsetC = Math.floor(Math.random() * 3) - 1;
    people.push(new Person(i, char, { r: roomPos.r + offsetR, c: roomPos.c + offsetC }));
  }

  // Add sensors
  sensors.sensors = [];
  const sensorLocations = [
    { r: 6, c: 10, type: 'temp' }, // Reception
    { r: 6, c: 30, type: 'smoke' }, // Michael's office
    { r: 7, c: 50, type: 'temp' }, // Conference
    { r: 23, c: 32, type: 'smoke' }, // Main floor
    { r: 22, c: 65, type: 'temp' }, // Accounting
    { r: 38, c: 12, type: 'smoke' }, // Break room
    { r: 38, c: 52, type: 'temp' }, // Annex
    { r: 36, c: 32, type: 'motion' }, // Bathroom
  ];
  for (const loc of sensorLocations) {
    sensors.addSensor(loc.r, loc.c, loc.type);
  }

  // Center camera
  camera.x = (COLS * TILE * camera.zoom) / 2 - W / 2;
  camera.y = (ROWS * TILE * camera.zoom) / 2 - H / 2;

  alarmActive = false;
  aco.reset();
  hazards.reset();
  sensors.reset();
}

function reset() {
  const result = createDunderMifflinOffice();
  maze = result.maze;
  roomPositions = result.roomPositions;
  init();
}

// ═══════════════════════════════════════════════════════════════════════════════
// RENDERING
// ═══════════════════════════════════════════════════════════════════════════════

function drawTile(r, c) {
  const pos = camera.toScreen(r, c);
  const size = TILE * camera.zoom;

  if (pos.x < -size || pos.x > W + size || pos.y < -size || pos.y > H + size) return;

  const tile = maze[r][c];
  let color;

  switch (tile) {
    case FLOOR: color = (r + c) % 2 === 0 ? Colors.floor : Colors.floorAlt; break;
    case CARPET: color = (r + c) % 2 === 0 ? Colors.carpet : Colors.carpetAlt; break;
    case WALL: color = Colors.wall; break;
    case DESK: color = Colors.desk; break;
    case EXIT: color = Colors.exit; break;
    case DOOR: color = Colors.door; break;
    case WINDOW: color = Colors.window; break;
    case KITCHEN: color = Colors.kitchen; break;
    case BATHROOM: color = Colors.bathroom; break;
    default: color = Colors.floor;
  }

  ctx.fillStyle = color;
  ctx.fillRect(pos.x, pos.y, size, size);

  // Wall top highlight
  if (tile === WALL) {
    ctx.fillStyle = Colors.wallTop;
    ctx.fillRect(pos.x, pos.y, size, 2);
  }

  // Desk top
  if (tile === DESK) {
    ctx.fillStyle = Colors.deskTop;
    ctx.fillRect(pos.x + 1, pos.y + 1, size - 2, size - 2);
  }

  // Exit glow
  if (tile === EXIT) {
    const pulse = 0.5 + Math.sin(performance.now() / 300) * 0.3;
    ctx.fillStyle = `rgba(50, 255, 50, ${pulse * 0.5})`;
    ctx.fillRect(pos.x - 2, pos.y - 2, size + 4, size + 4);
  }
}

function drawFire(fire) {
  const pos = camera.toScreen(fire.r, fire.c);
  const size = TILE * camera.zoom;
  const cx = pos.x + size / 2;
  const cy = pos.y + size / 2;
  const time = performance.now() / 1000;

  const flicker = 0.7 + Math.sin(time * 12 + fire.r + fire.c) * 0.3;
  const fireSize = (fire.intensity / 50) * size * flicker;

  // Glow
  const grad = ctx.createRadialGradient(cx, cy, fireSize * 0.3, cx, cy - 4, fireSize * 2);
  grad.addColorStop(0, 'rgba(255, 200, 100, 0.9)');
  grad.addColorStop(0.5, 'rgba(255, 100, 50, 0.5)');
  grad.addColorStop(1, 'rgba(150, 30, 10, 0)');

  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.arc(cx, cy, fireSize * 2, 0, Math.PI * 2);
  ctx.fill();

  // Flame
  ctx.fillStyle = Colors.fireGlow;
  ctx.beginPath();
  ctx.moveTo(cx, cy - fireSize);
  ctx.lineTo(cx - fireSize * 0.5, cy + fireSize * 0.3);
  ctx.lineTo(cx + fireSize * 0.5, cy + fireSize * 0.3);
  ctx.closePath();
  ctx.fill();

  // Sparks
  for (let i = 0; i < 2; i++) {
    const sx = cx + (Math.random() - 0.5) * fireSize;
    const sy = cy - Math.random() * fireSize * 1.5;
    ctx.fillStyle = 'rgba(255,220,120,0.8)';
    ctx.beginPath();
    ctx.arc(sx, sy, 1.5 * camera.zoom, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}

function drawSmoke() {
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const level = hazards.smoke[r][c];
      if (level > 0.1) {
        const pos = camera.toScreen(r, c);
        const size = TILE * camera.zoom;
        const t = performance.now() / 900;
        const wobble = Math.sin(t + r * 0.4 + c * 0.3) * 0.2;
        const alpha = Math.min(level * 0.35 + wobble * 0.05, 0.6);
        ctx.fillStyle = `rgba(120, 130, 140, ${Math.max(0.08, alpha)})`;
        ctx.beginPath();
        ctx.ellipse(pos.x + size / 2, pos.y + size / 2 - 2, size * 0.7, size * 0.9, 0, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }
}

function drawFlood() {
  for (const tile of hazards.flood) {
    const pos = camera.toScreen(tile.r, tile.c);
    const size = TILE * camera.zoom;
    const pulse = 0.6 + Math.sin(performance.now() / 400 + tile.r + tile.c) * 0.2;
    const depthAlpha = Math.min(0.4, tile.depth * 0.4);
    const grad = ctx.createRadialGradient(pos.x + size / 2, pos.y + size / 2, size * 0.2, pos.x + size / 2, pos.y + size / 2, size * 0.9);
    grad.addColorStop(0, `rgba(80, 150, 255, ${depthAlpha + 0.1})`);
    grad.addColorStop(1, `rgba(40, 90, 180, ${depthAlpha * 0.6})`);
    ctx.fillStyle = grad;
    ctx.fillRect(pos.x, pos.y, size, size);

    ctx.strokeStyle = `rgba(120, 180, 255, ${depthAlpha})`;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(pos.x + size / 2, pos.y + size / 2, size * 0.35 * pulse, 0, Math.PI * 2);
    ctx.stroke();
  }
}

function drawBombExplosions() {
  for (const exp of hazards.bombExplosions) {
    const pos = camera.toScreen(exp.r, exp.c);
    const size = TILE * camera.zoom;
    const t = exp.age / exp.maxAge;
    const radius = exp.radius * size * (0.8 + t * 1.2);
    const alpha = Math.max(0, 0.6 - t * 0.6);
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    ctx.strokeStyle = `rgba(255, 200, 60, ${alpha})`;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(pos.x + size / 2, pos.y + size / 2, radius, 0, Math.PI * 2);
    ctx.stroke();
    ctx.strokeStyle = `rgba(255, 80, 40, ${alpha * 0.7})`;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(pos.x + size / 2, pos.y + size / 2, radius * 0.65, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  }
}

function drawScanlines() {
  ctx.fillStyle = 'rgba(0,0,0,0.07)';
  for (let y = 0; y < H; y += 6) {
    ctx.fillRect(0, y, W, 2);
  }
}

function drawPheromones() {
  const size = TILE * camera.zoom;

  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const pos = camera.toScreen(r, c);

      // Safe pheromones
      const safe = aco.safePheromone[r][c];
      if (safe > 0.3) {
        const alpha = Math.min((safe - 0.3) * 0.15, 0.35);
        ctx.fillStyle = `rgba(0, 255, 150, ${alpha})`;
        ctx.fillRect(pos.x, pos.y, size, size);
      }

      // Danger pheromones
      const danger = aco.dangerPheromone[r][c];
      if (danger > 0.5) {
        const alpha = Math.min(danger * 0.04, 0.3);
        ctx.fillStyle = `rgba(255, 80, 80, ${alpha})`;
        ctx.fillRect(pos.x, pos.y, size, size);
      }
    }
  }
}

function drawPredictions() {
  const size = TILE * camera.zoom;
  const pulse = 0.5 + Math.sin(performance.now() / 200) * 0.3;

  for (const pred of predictions) {
    const pos = camera.toScreen(pred.r, pred.c);
    const alpha = pred.prob * pulse * 0.5;
    ctx.fillStyle = `rgba(255, 60, 200, ${alpha})`;
    ctx.fillRect(pos.x, pos.y, size, size);

    ctx.strokeStyle = `rgba(255, 100, 255, ${alpha + 0.2})`;
    ctx.lineWidth = 1;
    ctx.strokeRect(pos.x + 1, pos.y + 1, size - 2, size - 2);
  }
}

function drawSensors() {
  for (const sensor of sensors.sensors) {
    const pos = camera.toScreen(sensor.r, sensor.c);
    const size = TILE * camera.zoom;
    const cx = pos.x + size / 2;
    const cy = pos.y + size / 2;

    // Sensor dot
    ctx.fillStyle = sensor.triggered ? Colors.sensorTriggered : Colors.sensor;
    ctx.beginPath();
    ctx.arc(cx, cy, 4 * camera.zoom, 0, Math.PI * 2);
    ctx.fill();

    // Range
    ctx.strokeStyle = sensor.triggered ? 'rgba(255, 68, 68, 0.3)' : 'rgba(0, 191, 255, 0.2)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(cx, cy, 5 * TILE * camera.zoom, 0, Math.PI * 2);
    ctx.stroke();

    // Pulse if triggered
    if (sensor.triggered) {
      const pulseSize = ((performance.now() / 50) % 25) + 8;
      const pulseAlpha = 1 - pulseSize / 33;
      ctx.strokeStyle = `rgba(255, 68, 68, ${pulseAlpha})`;
      ctx.beginPath();
      ctx.arc(cx, cy, pulseSize * camera.zoom, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Label
    ctx.fillStyle = 'rgba(255,255,255,0.6)';
    ctx.font = `${8 * camera.zoom}px monospace`;
    const label = sensor.type === 'temp' ? 'T' : sensor.type === 'smoke' ? 'S' : 'M';
    ctx.fillText(label, cx - 3, cy + 3);
  }
}

function drawPerson(person) {
  if (!person.alive && !person.escaped) return;
  if (person.escaped) return;

  const pos = camera.toScreen(person.exactR, person.exactC);
  const size = TILE * camera.zoom;
  const cx = pos.x + size / 2;
  const cy = pos.y + size / 2;
  const time = performance.now() / 1000;

  // Movement bob
  let bob = 0;
  if (person.state === 'evacuating' || person.state === 'panicking') {
    bob = Math.sin(time * 10 + person.id) * 2 * camera.zoom;
  }

  // Shadow
  ctx.fillStyle = 'rgba(0,0,0,0.25)';
  ctx.beginPath();
  ctx.ellipse(cx, cy + 5 * camera.zoom, 6 * camera.zoom, 3 * camera.zoom, 0, 0, Math.PI * 2);
  ctx.fill();

  // Body color based on state
  let bodyColor = person.color;
  if (person.state === 'panicking') {
    bodyColor = Colors.fire;
  } else if (person.state === 'evacuating') {
    bodyColor = '#4cff88';
  }

  // Outline for warden
  if (person.role === 'warden') {
    ctx.fillStyle = '#ffd700';
    ctx.beginPath();
    ctx.arc(cx, cy + bob, 9 * camera.zoom, 0, Math.PI * 2);
    ctx.fill();
  }

  // Body
  ctx.fillStyle = bodyColor;
  ctx.beginPath();
  ctx.arc(cx, cy + bob, 7 * camera.zoom, 0, Math.PI * 2);
  ctx.fill();

  // Head
  ctx.fillStyle = '#ffd6b1';
  ctx.beginPath();
  ctx.arc(cx, cy - 5 * camera.zoom + bob, 5 * camera.zoom, 0, Math.PI * 2);
  ctx.fill();

  // Health bar
  if (person.health < 90) {
    const barW = 14 * camera.zoom;
    ctx.fillStyle = '#600';
    ctx.fillRect(cx - barW / 2, cy - 12 * camera.zoom + bob, barW, 3 * camera.zoom);
    ctx.fillStyle = '#0c0';
    ctx.fillRect(cx - barW / 2, cy - 12 * camera.zoom + bob, barW * (person.health / 100), 3 * camera.zoom);
  }

  // Name tag on hover / selection
  if (camera.target === person.id) {
    ctx.fillStyle = 'rgba(0,0,0,0.7)';
    const nameWidth = ctx.measureText(person.name).width + 10;
    ctx.fillRect(cx - nameWidth / 2, cy - 28 * camera.zoom + bob, nameWidth, 14 * camera.zoom);
    ctx.fillStyle = '#fff';
    ctx.font = `${10 * camera.zoom}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.fillText(person.name, cx, cy - 18 * camera.zoom + bob);
    ctx.textAlign = 'left';

    // Selection arrow
    const arrowY = cy - 35 * camera.zoom + Math.sin(time * 5) * 3;
    ctx.fillStyle = '#ffd700';
    ctx.beginPath();
    ctx.moveTo(cx, arrowY + 8);
    ctx.lineTo(cx - 5, arrowY);
    ctx.lineTo(cx + 5, arrowY);
    ctx.closePath();
    ctx.fill();
  }
}

function render() {
  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, W, H);

  // Background
  ctx.fillStyle = '#1a1c20';
  ctx.fillRect(0, 0, W, H);

  // Earthquake shake
  let shakeX = 0, shakeY = 0;
  if (hazards.earthquakeActive) {
    const mag = hazards.earthquakeIntensity * 0.8;
    shakeX = (Math.random() - 0.5) * mag;
    shakeY = (Math.random() - 0.5) * mag;
    ctx.save();
    ctx.translate(shakeX, shakeY);
  }

  // Draw tiles
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      drawTile(r, c);
    }
  }

  // Draw pheromones
  drawPheromones();

  // Draw predictions
  drawPredictions();

  // Draw smoke
  drawSmoke();

  // Draw fires
  for (const fire of hazards.fires) {
    drawFire(fire);
  }

  // Draw flood
  drawFlood();

  // Draw bomb blasts
  drawBombExplosions();

  // Draw sensors
  drawSensors();

  // Draw people (sorted by Y)
  const sortedPeople = [...people].sort((a, b) => a.exactR - b.exactR);
  for (const person of sortedPeople) {
    drawPerson(person);
  }

  // Alarm overlay
  if (alarmActive) {
    const flash = Math.sin(performance.now() / 150) > 0;
    if (flash) {
      ctx.fillStyle = 'rgba(255, 0, 0, 0.08)';
      ctx.fillRect(0, 0, W, H);
    }
  }

  drawScanlines();

  if (hazards.earthquakeActive) {
    ctx.restore();
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// GAME LOOP
// ═══════════════════════════════════════════════════════════════════════════════

let lastTime = performance.now();
let setHudState = null;

function update(dt) {
  if (paused) return;

  // Auto alarm on fire
  if (hazards.fires.length > 0 && !alarmActive) {
    alarmActive = true;
  }

  // Update hazards
  hazards.update(dt, maze, aco);

  // Update neural predictions
  predictions = aco.updatePredictions(hazards.fires, hazards.smoke, maze);

  // Update sensors
  sensors.update(hazards.fires, hazards.smoke, people);

  // Update people
  for (const person of people) {
    person.update(dt, maze, hazards.fires, hazards.smoke, people, exits, aco, alarmActive);
  }

  // Evaporate pheromones
  aco.evaporate();

  // Update camera
  if (camera.target !== null) {
    const person = people.find(p => p.id === camera.target);
    if (person && person.alive && !person.escaped) {
      const targetX = person.exactC * TILE * camera.zoom - W / 2;
      const targetY = person.exactR * TILE * camera.zoom - H / 2;
      camera.x += (targetX - camera.x) * 0.1;
      camera.y += (targetY - camera.y) * 0.1;
    }
  }
}

function updateHUD() {
  if (!setHudState) return;

  const alive = people.filter(p => p.alive && !p.escaped).length;
  const escaped = people.filter(p => p.escaped).length;
  const deaths = people.filter(p => !p.alive).length;

  const targetPerson = camera.target !== null ? people.find(p => p.id === camera.target) : null;

  setHudState({
    alive,
    escaped,
    deaths,
    fires: hazards.fires.length,
    alarm: alarmActive,
    neural: {
      confidence: lstm.confidence,
      predictions: predictions.length
    },
    aco: {
      pheromone: getAcoStrength()
    },
    hazards: {
      bombs: hazards.bombExplosions.length,
      flood: hazards.flood.length,
      quake: hazards.earthquakeActive,
      tool: selectedDisaster
    },
    sensors: {
      triggered: sensors.getTriggeredCount(),
      total: sensors.sensors.length,
      temp: sensors.getAvgTemp()
    },
    target: targetPerson ? {
      name: targetPerson.name,
      state: targetPerson.state,
      health: targetPerson.health,
      thought: targetPerson.thought
    } : null
  });

  // Bridge to external UI (CRT wrapper)
  if (typeof window.updateApocStats === 'function') {
    window.updateApocStats({
      alive,
      escaped,
      deaths,
      fires: hazards.fires.length,
      bombs: hazards.bombExplosions.length,
      flood: hazards.flood.length,
      quake: hazards.earthquakeActive,
      neural: lstm.confidence,
      aco: getAcoStrength(),
      sensors: `${sensors.getTriggeredCount()}/${sensors.sensors.length}`,
      temp: sensors.getAvgTemp().toFixed(1) + 'C'
    });
  }
}

function loop(ts) {
  const dt = Math.min((ts - lastTime) / 1000, 0.05);
  lastTime = ts;

  update(dt);
  render();
  updateHUD();

  requestAnimationFrame(loop);
}

function getAcoStrength() {
  let sum = 0;
  let count = 0;
  for (let r = 0; r < ROWS; r += 5) {
    for (let c = 0; c < COLS; c += 5) {
      sum += aco.safePheromone[r][c];
      count++;
    }
  }
  return count ? sum / count : 0;
}

// ═══════════════════════════════════════════════════════════════════════════════
// INPUT HANDLING
// ═══════════════════════════════════════════════════════════════════════════════

const keys = new Set();

window.addEventListener('keydown', (e) => {
  keys.add(e.key.toLowerCase());

  if (e.key === ' ') {
    e.preventDefault();
    camera.target = null;
  }
  if (e.key.toLowerCase() === 'r') reset();
  if (e.key.toLowerCase() === 'a') alarmActive = true;
  if (e.key.toLowerCase() === 'p') paused = !paused;
  if (e.key === '1') selectedDisaster = 'fire';
  if (e.key === '2') selectedDisaster = 'bomb';
  if (e.key === '3') selectedDisaster = 'quake';
  if (e.key === '4') selectedDisaster = 'flood';
  if (setHudState) setHudState({ hazards: { ...initialHud.hazards, tool: selectedDisaster } });
});

window.addEventListener('keyup', (e) => {
  keys.delete(e.key.toLowerCase());
});

canvas.addEventListener('mousedown', (e) => {
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) / rect.width * W;
  const my = (e.clientY - rect.top) / rect.height * H;

  const gridC = Math.floor((mx + camera.x) / (TILE * camera.zoom));
  const gridR = Math.floor((my + camera.y) / (TILE * camera.zoom));

  if (e.button === 2 || e.ctrlKey) {
    // Right click - place selected hazard
    if (gridR > 0 && gridR < ROWS - 1 && gridC > 0 && gridC < COLS - 1) {
      const tile = maze[gridR][gridC];
      if (tile !== WALL && tile !== WINDOW) {
        if (selectedDisaster === 'fire') hazards.addFire(gridR, gridC);
        else if (selectedDisaster === 'bomb') hazards.triggerBomb(gridR, gridC, 6);
        else if (selectedDisaster === 'quake') hazards.triggerEarthquake(8);
        else if (selectedDisaster === 'flood') hazards.triggerFlood(gridR, gridC);
      }
    }
  } else {
    // Left click - select person
    let closest = null;
    let closestDist = 30 * camera.zoom;

    for (const person of people) {
      if (!person.alive || person.escaped) continue;
      const pos = camera.toScreen(person.exactR, person.exactC);
      const dist = Math.hypot(pos.x + TILE * camera.zoom / 2 - mx, pos.y + TILE * camera.zoom / 2 - my);
      if (dist < closestDist) {
        closestDist = dist;
        closest = person;
      }
    }

    camera.target = closest ? closest.id : null;
  }
});

canvas.addEventListener('wheel', (e) => {
  e.preventDefault();
  const oldZoom = camera.zoom;
  camera.zoom = Math.max(0.5, Math.min(2.5, camera.zoom - e.deltaY * 0.001));

  // Adjust camera position to zoom toward mouse
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) / rect.width * W;
  const my = (e.clientY - rect.top) / rect.height * H;

  camera.x = (camera.x + mx) * (camera.zoom / oldZoom) - mx;
  camera.y = (camera.y + my) * (camera.zoom / oldZoom) - my;
});

canvas.addEventListener('contextmenu', (e) => e.preventDefault());

// Camera movement
setInterval(() => {
  const speed = 8;
  if (keys.has('w') || keys.has('arrowup')) camera.y -= speed;
  if (keys.has('s') || keys.has('arrowdown')) camera.y += speed;
  if (keys.has('a') || keys.has('arrowleft')) camera.x -= speed;
  if (keys.has('d') || keys.has('arrowright')) camera.x += speed;
}, 16);

// Resize
function resize() {
  W = window.innerWidth;
  H = window.innerHeight;
  canvas.width = W;
  canvas.height = H;
}
window.addEventListener('resize', resize);
resize();

// ═══════════════════════════════════════════════════════════════════════════════
// REACT HUD
// ═══════════════════════════════════════════════════════════════════════════════

const initialHud = {
  alive: 0, escaped: 0, deaths: 0, fires: 0, alarm: false,
  neural: { confidence: 0, predictions: 0 },
  sensors: { triggered: 0, total: 0, temp: 22 },
  aco: { pheromone: 0 },
  hazards: { bombs: 0, flood: 0, quake: false, tool: 'fire' },
  target: null
};

function App() {
  const [hud, setHud] = React.useState(initialHud);
  setHudState = (next) => setHud(prev => ({ ...prev, ...next }));

  const targetInfo = hud.target
    ? `${hud.target.name} | ${hud.target.state} | HP: ${Math.round(hud.target.health)}% | "${hud.target.thought}"`
    : 'Click a person to follow (Right-click to place disaster)';

  const setTool = (tool) => {
    selectedDisaster = tool;
    setHudState({ hazards: { ...hud.hazards, tool } });
  };

  const randomDrop = (tool) => {
    const r = Math.floor(ROWS / 2) + Math.floor(Math.random() * 10) - 5;
    const c = Math.floor(COLS / 2) + Math.floor(Math.random() * 10) - 5;
    if (tool === 'fire') hazards.addFire(r, c);
    else if (tool === 'bomb') hazards.triggerBomb(r, c, 6);
    else if (tool === 'quake') hazards.triggerEarthquake(8);
    else if (tool === 'flood') hazards.triggerFlood(r, c);
  };

  return html`
    <div class="overlay ${hud.alarm ? 'alarm-active' : ''}">
      <div class="hud">
        <div class="hud__left">
          <div class="hud__title">
            <h1>DWIGHT</h1>
            <span>Dunder Mifflin Emergency Response</span>
          </div>

          <div class="chips">
            <span class="chip">Employees: ${hud.alive}</span>
            <span class="chip success">Escaped: ${hud.escaped}</span>
            <span class="chip ${hud.deaths > 0 ? 'danger' : ''}">Deaths: ${hud.deaths}</span>
            <span class="chip ${hud.fires > 0 ? 'warning' : ''}">Fires: ${hud.fires}</span>
            <span class="chip">Bombs: ${hud.hazards.bombs}</span>
            <span class="chip">Flood: ${hud.hazards.flood}</span>
            <span class="chip ${hud.hazards.quake ? 'warning' : ''}">Quake: ${hud.hazards.quake ? 'Active' : 'Idle'}</span>
            <span class="chip ${hud.alarm ? 'danger' : ''}">
              ${hud.alarm ? 'ALARM ACTIVE' : 'Standby'}
            </span>
          </div>

          <div class="chips">
            <span class="chip neural">
              Neural: ${(hud.neural.confidence * 100).toFixed(0)}%
            </span>
            <span class="chip neural">
              Predictions: ${hud.neural.predictions}
            </span>
            <span class="chip neural">
              ACO Phero: ${(hud.aco.pheromone * 100).toFixed(0)}%
            </span>
            <span class="chip sensor">
              Sensors: ${hud.sensors.triggered}/${hud.sensors.total}
            </span>
            <span class="chip">
              Temp: ${hud.sensors.temp.toFixed(1)}C
            </span>
            <span class="chip">
              Tool: ${hud.hazards.tool.toUpperCase()}
            </span>
          </div>

          <div class="controls-hint">
            WASD: Pan | Scroll: Zoom | Click: Follow | Right-click: Place hazard | 1 Fire | 2 Bomb | 3 Quake | 4 Flood | A Alarm | R Reset | P Pause
          </div>
        </div>

        <div class="hud__actions">
          <button class="btn btn-secondary" onClick=${() => { alarmActive = true; }}>
            Trigger Alarm
          </button>
          <div class="chips">
            <button class=${`btn btn-toggle ${hud.hazards.tool === 'fire' ? 'active' : ''}`} onClick=${() => setTool('fire')}>Fire</button>
            <button class=${`btn btn-toggle ${hud.hazards.tool === 'bomb' ? 'active' : ''}`} onClick=${() => setTool('bomb')}>Bomb</button>
            <button class=${`btn btn-toggle ${hud.hazards.tool === 'quake' ? 'active' : ''}`} onClick=${() => setTool('quake')}>Quake</button>
            <button class=${`btn btn-toggle ${hud.hazards.tool === 'flood' ? 'active' : ''}`} onClick=${() => setTool('flood')}>Flood</button>
            <button class="btn btn-danger" onClick=${() => randomDrop(hud.hazards.tool)}>Drop ${hud.hazards.tool.toUpperCase()}</button>
          </div>
          <button class="btn btn-primary" onClick=${reset}>
            Reset
          </button>
        </div>
      </div>

      <div class="bottom-bar">
        <div class="bottom-bar__left">
          <span class="person-info">${targetInfo}</span>
        </div>
        <div class="bottom-bar__right">
          <div class="neural-meter">
            <span>Neural ACO</span>
            <div class="neural-meter__bar">
              <div class="neural-meter__fill" style=${{ width: `${hud.neural.confidence * 100}%` }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

// Initialize React
const root = createRoot(document.getElementById('app'));
root.render(html`<${App} />`);

// Start
init();
requestAnimationFrame(loop);

console.log('%c DWIGHT - Dunder Mifflin Emergency Response System ', 'background: #1e3a5f; color: #fff; padding: 8px; font-size: 14px;');
console.log('Controls: WASD pan, Scroll zoom, Click follow, Right-click fire, A alarm, R reset');
