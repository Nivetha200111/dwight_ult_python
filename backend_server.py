"""
DWIGHT UX - Neural ACO Backend Server
=====================================
Flask + WebSocket server that runs the Neural ACO simulation
and streams real-time data to the web frontend.

Run: python backend_server.py
Then open index.html in browser
"""

import asyncio
import json
import random
import math
import numpy as np
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from typing import List, Tuple, Dict, Optional
from threading import Thread
import time

# Flask and WebSocket imports
try:
    from flask import Flask, jsonify, send_from_directory
    from flask_cors import CORS
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'flask', 'flask-cors', 'flask-socketio', 'python-socketio', 'eventlet'])
    from flask import Flask, jsonify, send_from_directory
    from flask_cors import CORS
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True

# Configuration
ROWS = 40
COLS = 50
TOTAL_PEOPLE = 60
NUM_SENSORS = 12
TILE = 16

# Tile types
FLOOR = 0
WALL = 1
EXIT = 2
RUBBLE = 3

# Person states
STATE_WORKING = "working"
STATE_HEADPHONES = "headphones"
STATE_AWARE = "aware"
STATE_EVACUATING = "evacuating"
STATE_PANICKING = "panicking"

# ═══════════════════════════════════════════════════════════════════════════════
# NEURAL PREDICTOR (LSTM-like)
# ═══════════════════════════════════════════════════════════════════════════════

class NeuralPredictor:
    """Simplified LSTM for fire spread prediction."""

    def __init__(self):
        np.random.seed(42)
        self.hidden_size = 32
        self.hidden = np.zeros(self.hidden_size)
        self.cell = np.zeros(self.hidden_size)

        self.W_forget = np.random.randn(self.hidden_size, self.hidden_size + 4) * 0.1
        self.W_input = np.random.randn(self.hidden_size, self.hidden_size + 4) * 0.1
        self.W_output = np.random.randn(self.hidden_size, self.hidden_size + 4) * 0.1
        self.W_cell = np.random.randn(self.hidden_size, self.hidden_size + 4) * 0.1
        self.W_pred = np.random.randn(4, self.hidden_size) * 0.1

        self.history = deque(maxlen=10)
        self.confidence = 0.0

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

    def predict(self, fire_positions: List[Tuple[int, int]], maze) -> List[dict]:
        if not fire_positions:
            self.confidence = 0.0
            return []

        # Extract features
        center_r = np.mean([p[0] for p in fire_positions])
        center_c = np.mean([p[1] for p in fire_positions])

        spread_r, spread_c = 0, 0
        if len(self.history) > 0:
            prev = self.history[-1]
            spread_r = center_r - prev[0]
            spread_c = center_c - prev[1]

        features = np.array([center_r / ROWS, center_c / COLS, spread_r, spread_c])
        self.history.append((center_r, center_c))

        # Forward pass
        concat = np.concatenate([self.hidden, features])
        forget = self.sigmoid(self.W_forget @ concat)
        input_gate = self.sigmoid(self.W_input @ concat)
        output = self.sigmoid(self.W_output @ concat)
        cell_cand = np.tanh(np.clip(self.W_cell @ concat, -500, 500))

        self.cell = forget * self.cell + input_gate * cell_cand
        self.hidden = output * np.tanh(self.cell)

        direction_probs = self.sigmoid(self.W_pred @ self.hidden)
        self.confidence = float(np.max(direction_probs))

        # Generate predictions
        predictions = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for fire_pos in fire_positions:
            for i, (dr, dc) in enumerate(directions):
                prob = direction_probs[i]
                if prob > 0.3:
                    for step in range(1, 4):
                        nr = fire_pos[0] + dr * step
                        nc = fire_pos[1] + dc * step
                        if 0 < nr < ROWS - 1 and 0 < nc < COLS - 1:
                            if maze[nr][nc] != WALL:
                                decay = 0.7 ** step
                                predictions.append({
                                    'r': nr, 'c': nc,
                                    'prob': float(prob * decay)
                                })

        return predictions

    def reset(self):
        self.hidden = np.zeros(self.hidden_size)
        self.cell = np.zeros(self.hidden_size)
        self.history.clear()
        self.confidence = 0.0

# ═══════════════════════════════════════════════════════════════════════════════
# NEURAL ACO SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class NeuralACO:
    """Ant Colony Optimization enhanced with neural predictions."""

    def __init__(self, predictor: NeuralPredictor):
        self.predictor = predictor
        self.safe_pheromone = np.ones((ROWS, COLS)) * 0.1
        self.danger_pheromone = np.zeros((ROWS, COLS))
        self.predicted_danger = np.zeros((ROWS, COLS))

        self.base_evaporation = 0.02
        self.edge_usage = defaultdict(int)

    def update_predictions(self, fire_positions, maze):
        predictions = self.predictor.predict(fire_positions, maze)
        confidence = self.predictor.confidence

        self.predicted_danger *= 0.8

        for pred in predictions:
            r, c = pred['r'], pred['c']
            prob = pred['prob']
            modulated = prob * (0.5 + 0.5 * confidence)
            self.predicted_danger[r, c] = max(self.predicted_danger[r, c], modulated)
            self.danger_pheromone[r, c] += modulated * 2

        return predictions

    def deposit_safe(self, path: List[Tuple[int, int]]):
        if not path:
            return
        amount = 1.0 * (1.0 + self.predictor.confidence * 0.5)
        for i, (r, c) in enumerate(path):
            decay = 1.0 - (i / len(path)) * 0.5
            self.safe_pheromone[r, c] = min(self.safe_pheromone[r, c] + amount * decay, 10.0)

    def deposit_danger(self, r, c, severity):
        self.danger_pheromone[r, c] = min(self.danger_pheromone[r, c] + severity, 20.0)
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r + dr, c + dc
                if 0 <= nr < ROWS and 0 <= nc < COLS:
                    dist = abs(dr) + abs(dc)
                    self.danger_pheromone[nr, nc] += severity * 0.3 / (dist + 1)

    def evaporate(self):
        confidence = self.predictor.confidence
        safe_evap = self.base_evaporation * (1.0 - confidence * 0.3)
        self.safe_pheromone *= (1.0 - safe_evap)
        self.danger_pheromone *= (1.0 - self.base_evaporation * 1.2)
        self.safe_pheromone = np.clip(self.safe_pheromone, 0.1, 10.0)
        self.danger_pheromone = np.clip(self.danger_pheromone, 0, 20.0)

    def get_visualization_data(self):
        # Sample pheromone data for visualization
        safe_hot = []
        danger_hot = []

        for r in range(ROWS):
            for c in range(COLS):
                if self.safe_pheromone[r, c] > 0.5:
                    safe_hot.append({'r': r, 'c': c, 'v': float(self.safe_pheromone[r, c])})
                if self.danger_pheromone[r, c] > 0.5:
                    danger_hot.append({'r': r, 'c': c, 'v': float(self.danger_pheromone[r, c])})

        return {
            'safe': safe_hot[:100],  # Limit for performance
            'danger': danger_hot[:100],
            'confidence': self.predictor.confidence
        }

    def reset(self):
        self.safe_pheromone = np.ones((ROWS, COLS)) * 0.1
        self.danger_pheromone = np.zeros((ROWS, COLS))
        self.predicted_danger = np.zeros((ROWS, COLS))
        self.edge_usage.clear()
        self.predictor.reset()

# ═══════════════════════════════════════════════════════════════════════════════
# IOT SENSORS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class IoTSensor:
    id: int
    r: int
    c: int
    sensor_type: str
    value: float = 0.0
    threshold: float = 0.0
    triggered: bool = False
    health: float = 100.0
    battery: float = 100.0

class SensorNetwork:
    def __init__(self):
        self.sensors: Dict[int, IoTSensor] = {}
        self.alerts = []

    def add_sensor(self, sensor: IoTSensor):
        self.sensors[sensor.id] = sensor

    def update(self, dt, fire_positions, smoke_map):
        self.alerts = []

        for sensor in self.sensors.values():
            sensor.battery -= 0.001 * dt
            if sensor.battery <= 0:
                sensor.health = 0
                continue

            # Calculate reading
            raw = 0
            if sensor.sensor_type == 'temperature':
                base = 22.0
                for fr, fc in fire_positions:
                    dist = abs(sensor.r - fr) + abs(sensor.c - fc)
                    if dist < 10:
                        base += 80 / (dist + 1)
                raw = min(base, 150)
                sensor.threshold = 45.0
            elif sensor.sensor_type == 'smoke':
                raw = smoke_map.get((sensor.r, sensor.c), 0) * 10
                sensor.threshold = 3.0
            elif sensor.sensor_type == 'co':
                for fr, fc in fire_positions:
                    dist = abs(sensor.r - fr) + abs(sensor.c - fc)
                    if dist < 8:
                        raw += 40 / (dist + 1)
                sensor.threshold = 30.0

            # Add noise and smooth
            noise = random.gauss(0, 0.5)
            sensor.value = sensor.value * 0.8 + (raw + noise) * 0.2

            was_triggered = sensor.triggered
            sensor.triggered = sensor.value > sensor.threshold

            if sensor.triggered and not was_triggered:
                self.alerts.append({
                    'id': sensor.id,
                    'type': sensor.sensor_type,
                    'value': sensor.value,
                    'r': sensor.r,
                    'c': sensor.c
                })

    def get_data(self):
        return [
            {
                'id': s.id, 'r': s.r, 'c': s.c,
                'type': s.sensor_type,
                'value': round(s.value, 1),
                'triggered': s.triggered,
                'health': round(s.health, 1),
                'battery': round(s.battery, 1)
            }
            for s in self.sensors.values()
        ]

    def get_fusion(self):
        temps = [s.value for s in self.sensors.values() if s.sensor_type == 'temperature' and s.health > 0]
        smokes = [s.value for s in self.sensors.values() if s.sensor_type == 'smoke' and s.health > 0]

        return {
            'temp_avg': round(np.mean(temps), 1) if temps else 22.0,
            'temp_max': round(max(temps), 1) if temps else 22.0,
            'smoke_avg': round(np.mean(smokes), 2) if smokes else 0.0,
            'triggered_count': sum(1 for s in self.sensors.values() if s.triggered),
            'total_sensors': len(self.sensors),
            'alerts': self.alerts
        }

# ═══════════════════════════════════════════════════════════════════════════════
# RL COORDINATOR
# ═══════════════════════════════════════════════════════════════════════════════

class RLCoordinator:
    def __init__(self):
        self.q_table = defaultdict(lambda: np.zeros(4))
        self.learning_rate = 0.1
        self.discount = 0.95
        self.epsilon = 0.2
        self.decisions = 0
        self.total_reward = 0
        self.actions = ['deploy_NW', 'deploy_NE', 'deploy_SW', 'deploy_SE']

    def get_state(self, fire_positions, people):
        fire_quad = 0
        if fire_positions:
            avg_r = np.mean([f[0] for f in fire_positions])
            avg_c = np.mean([f[1] for f in fire_positions])
            if avg_r < ROWS // 2:
                fire_quad = 0 if avg_c < COLS // 2 else 1
            else:
                fire_quad = 2 if avg_c < COLS // 2 else 3

        crowd_counts = [0, 0, 0, 0]
        for p in people:
            if p['alive'] and not p['escaped']:
                q = 0
                if p['r'] < ROWS // 2:
                    q = 0 if p['c'] < COLS // 2 else 1
                else:
                    q = 2 if p['c'] < COLS // 2 else 3
                crowd_counts[q] += 1

        crowd_quad = np.argmax(crowd_counts)
        return (fire_quad, crowd_quad)

    def step(self, fire_positions, people):
        state = self.get_state(fire_positions, people)

        if random.random() < self.epsilon:
            action = random.randint(0, 3)
        else:
            action = np.argmax(self.q_table[state])

        reward = 5 if action in [0, 1, 2, 3] else 0
        self.q_table[state][action] += self.learning_rate * reward

        self.decisions += 1
        self.total_reward += reward

        return {
            'action': self.actions[action],
            'reward': reward,
            'state': state
        }

    def get_stats(self):
        return {
            'decisions': self.decisions,
            'avg_reward': round(self.total_reward / max(1, self.decisions), 2),
            'epsilon': self.epsilon
        }

# ═══════════════════════════════════════════════════════════════════════════════
# SIMULATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class SimulationEngine:
    def __init__(self):
        self.maze = []
        self.people = []
        self.hazards = {}  # (r, c) -> {'intensity': float}
        self.smoke = defaultdict(float)
        self.exits = []

        self.predictor = NeuralPredictor()
        self.neural_aco = NeuralACO(self.predictor)
        self.sensors = SensorNetwork()
        self.rl_coordinator = RLCoordinator()

        self.evac_started = False
        self.alarm_active = False
        self.stats = {'alive': 0, 'escaped': 0, 'deaths': 0}

        self.time = 0
        self.predictions = []

        self.reset()

    def reset(self):
        self.maze = self._create_maze()
        self.people = self._spawn_people()
        self.hazards = {}
        self.smoke = defaultdict(float)
        self.exits = self._find_exits()

        self.neural_aco.reset()
        self._spawn_sensors()
        self.rl_coordinator = RLCoordinator()

        self.evac_started = False
        self.alarm_active = False
        self.stats = {'alive': TOTAL_PEOPLE, 'escaped': 0, 'deaths': 0}
        self.time = 0
        self.predictions = []

    def _create_maze(self):
        m = [[FLOOR for _ in range(COLS)] for _ in range(ROWS)]

        # Walls
        for r in range(ROWS):
            m[r][0] = WALL
            m[r][COLS - 1] = WALL
        for c in range(COLS):
            m[0][c] = WALL
            m[ROWS - 1][c] = WALL

        # Obstacles
        for r in range(5, ROWS - 5, 8):
            for c in range(5, COLS - 5, 8):
                m[r][c] = WALL
                m[r + 1][c] = WALL
                m[r][c + 1] = WALL

        # Exits
        m[ROWS // 2][0] = EXIT
        m[ROWS // 2][COLS - 1] = EXIT
        m[0][COLS // 2] = EXIT
        m[ROWS - 1][COLS // 2] = EXIT

        return m

    def _find_exits(self):
        exits = []
        for r in range(ROWS):
            for c in range(COLS):
                if self.maze[r][c] == EXIT:
                    exits.append((r, c))
        return exits

    def _spawn_people(self):
        people = []
        states = [STATE_WORKING] * 35 + [STATE_HEADPHONES] * 15 + [STATE_AWARE] * 10
        random.shuffle(states)

        for i in range(TOTAL_PEOPLE):
            r = random.randint(2, ROWS - 3)
            c = random.randint(2, COLS - 3)
            while self.maze[r][c] == WALL:
                r = random.randint(2, ROWS - 3)
                c = random.randint(2, COLS - 3)

            people.append({
                'id': i,
                'r': r, 'c': c,
                'exactR': float(r), 'exactC': float(c),
                'alive': True,
                'escaped': False,
                'health': 100,
                'state': states[i % len(states)],
                'awareness': 0.0,
                'path': [],
                'pathIndex': 0,
                'color': random.choice(['#ff5a5a', '#5a9fff', '#5aff5a', '#ffe65a'])
            })

        return people

    def _spawn_sensors(self):
        self.sensors = SensorNetwork()
        types = ['temperature', 'smoke', 'co', 'temperature']

        for i in range(NUM_SENSORS):
            r = random.randint(3, ROWS - 4)
            c = random.randint(3, COLS - 4)
            sensor = IoTSensor(
                id=i, r=r, c=c,
                sensor_type=types[i % len(types)]
            )
            self.sensors.add_sensor(sensor)

    def add_fire(self, r, c):
        if 0 < r < ROWS - 1 and 0 < c < COLS - 1:
            if self.maze[r][c] != WALL:
                self.hazards[(r, c)] = {'intensity': 40}
                if not self.alarm_active:
                    self.alarm_active = True
                    self.evac_started = True

    def update(self, dt):
        self.time += dt

        # Update hazards
        self._update_hazards(dt)

        # Update neural predictions
        fire_positions = list(self.hazards.keys())
        if fire_positions:
            self.predictions = self.neural_aco.update_predictions(fire_positions, self.maze)

        # Update sensors
        self.sensors.update(dt, fire_positions, self.smoke)

        # RL step every 2 seconds
        if int(self.time) % 2 == 0 and self.alarm_active:
            people_data = [{'r': p['r'], 'c': p['c'], 'alive': p['alive'], 'escaped': p['escaped']}
                          for p in self.people]
            self.rl_coordinator.step(fire_positions, people_data)

        # Update people
        self._update_people(dt)

        # Evaporate pheromones
        self.neural_aco.evaporate()

        # Update stats
        self.stats['alive'] = sum(1 for p in self.people if p['alive'] and not p['escaped'])
        self.stats['escaped'] = sum(1 for p in self.people if p['escaped'])
        self.stats['deaths'] = sum(1 for p in self.people if not p['alive'])

    def _update_hazards(self, dt):
        to_remove = []
        new_fires = []

        for (r, c), data in list(self.hazards.items()):
            data['intensity'] -= 3 * dt

            if data['intensity'] <= 0:
                to_remove.append((r, c))
                continue

            # Generate smoke
            for dr in range(-3, 4):
                for dc in range(-3, 4):
                    sr, sc = r + dr, c + dc
                    if 0 <= sr < ROWS and 0 <= sc < COLS:
                        dist = abs(dr) + abs(dc)
                        self.smoke[(sr, sc)] += data['intensity'] * 0.02 / (dist + 1)

            # Spread fire
            if data['intensity'] > 25 and random.random() < 0.02 * dt:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 < nr < ROWS - 1 and 0 < nc < COLS - 1:
                        if self.maze[nr][nc] != WALL and (nr, nc) not in self.hazards:
                            new_fires.append((nr, nc, data['intensity'] * 0.6))
                            break

            # Deposit danger pheromone
            self.neural_aco.deposit_danger(r, c, 1.0 * dt)

        for pos in to_remove:
            del self.hazards[pos]

        for r, c, intensity in new_fires:
            self.hazards[(r, c)] = {'intensity': intensity}

        # Decay smoke
        for key in list(self.smoke.keys()):
            self.smoke[key] *= 0.97
            if self.smoke[key] < 0.05:
                del self.smoke[key]

    def _update_people(self, dt):
        for p in self.people:
            if not p['alive'] or p['escaped']:
                continue

            # Damage from fire
            if (p['r'], p['c']) in self.hazards:
                p['health'] -= 25 * dt
                p['state'] = STATE_PANICKING

            # Smoke damage
            smoke_level = self.smoke.get((p['r'], p['c']), 0)
            if smoke_level > 0.5:
                p['health'] -= smoke_level * 5 * dt

            # Death check
            if p['health'] <= 0:
                p['alive'] = False
                self.neural_aco.deposit_danger(p['r'], p['c'], 30)
                continue

            # Check escape
            if self.maze[p['r']][p['c']] == EXIT:
                p['escaped'] = True
                self.neural_aco.deposit_safe([(p['r'], p['c'])])
                continue

            # Awareness
            if p['state'] in [STATE_WORKING, STATE_HEADPHONES]:
                if self.alarm_active:
                    rate = 0.15 if p['state'] != STATE_HEADPHONES else 0.03
                    p['awareness'] += rate * dt

                for hr, hc in self.hazards:
                    dist = abs(p['r'] - hr) + abs(p['c'] - hc)
                    if dist < 6:
                        p['awareness'] += 0.3 / (dist + 1) * dt

                if p['awareness'] >= 0.7:
                    p['state'] = STATE_EVACUATING

            # Movement
            if p['state'] in [STATE_EVACUATING, STATE_PANICKING]:
                if not p['path'] or p['pathIndex'] >= len(p['path']):
                    self._find_path(p)

                if p['path'] and p['pathIndex'] < len(p['path']):
                    nr, nc = p['path'][p['pathIndex']]

                    speed = 3.5 if p['state'] == STATE_EVACUATING else 5.0

                    dr = nr - p['exactR']
                    dc = nc - p['exactC']
                    dist = math.hypot(dr, dc)

                    if dist > 0:
                        move = min(dist, speed * dt)
                        p['exactR'] += (dr / dist) * move
                        p['exactC'] += (dc / dist) * move
                        p['r'] = int(round(p['exactR']))
                        p['c'] = int(round(p['exactC']))

                        if dist < 0.15:
                            p['pathIndex'] += 1

    def _find_path(self, person):
        if not self.exits:
            return

        # Find nearest exit
        best_exit = min(self.exits, key=lambda e: abs(person['r'] - e[0]) + abs(person['c'] - e[1]))

        # Simple A* pathfinding
        from heapq import heappush, heappop

        start = (person['r'], person['c'])
        goal = best_exit

        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}

        while open_set:
            _, current = heappop(open_set)

            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                person['path'] = path
                person['pathIndex'] = 0
                return

            r, c = current
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < ROWS and 0 <= nc < COLS:
                    if self.maze[nr][nc] != WALL:
                        neighbor = (nr, nc)
                        cost = 1

                        # Add costs from ACO
                        cost += self.neural_aco.danger_pheromone[nr, nc] * 5
                        cost += self.neural_aco.predicted_danger[nr, nc] * 10
                        cost -= self.neural_aco.safe_pheromone[nr, nc] * 0.5

                        if neighbor in self.hazards:
                            cost += 100

                        tentative = g_score[current] + cost

                        if neighbor not in g_score or tentative < g_score[neighbor]:
                            came_from[neighbor] = current
                            g_score[neighbor] = tentative
                            h = abs(nr - goal[0]) + abs(nc - goal[1])
                            heappush(open_set, (tentative + h, neighbor))

        person['path'] = []

    def get_state(self):
        """Get full simulation state for frontend."""
        return {
            'time': round(self.time, 1),
            'maze': self.maze,
            'people': [
                {
                    'id': p['id'],
                    'r': p['r'], 'c': p['c'],
                    'exactR': round(p['exactR'], 2),
                    'exactC': round(p['exactC'], 2),
                    'alive': p['alive'],
                    'escaped': p['escaped'],
                    'health': round(p['health']),
                    'state': p['state'],
                    'color': p['color']
                }
                for p in self.people
            ],
            'hazards': [
                {'r': r, 'c': c, 'intensity': round(data['intensity'], 1)}
                for (r, c), data in self.hazards.items()
            ],
            'smoke': [
                {'r': r, 'c': c, 'level': round(level, 2)}
                for (r, c), level in self.smoke.items()
                if level > 0.1
            ],
            'stats': self.stats,
            'alarm': self.alarm_active,
            'neural': {
                'confidence': round(self.predictor.confidence, 2),
                'predictions': self.predictions[:20],
                'aco': self.neural_aco.get_visualization_data()
            },
            'sensors': {
                'list': self.sensors.get_data(),
                'fusion': self.sensors.get_fusion()
            },
            'rl': self.rl_coordinator.get_stats()
        }

# ═══════════════════════════════════════════════════════════════════════════════
# FLASK SERVER
# ═══════════════════════════════════════════════════════════════════════════════

app = Flask(__name__, static_folder='.')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

simulation = SimulationEngine()
running = True

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/api/state')
def get_state():
    return jsonify(simulation.get_state())

@app.route('/api/reset', methods=['POST'])
def reset():
    simulation.reset()
    return jsonify({'status': 'ok'})

@app.route('/api/fire/<int:r>/<int:c>', methods=['POST'])
def add_fire(r, c):
    simulation.add_fire(r, c)
    return jsonify({'status': 'ok'})

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('state', simulation.get_state())

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('add_fire')
def handle_add_fire(data):
    simulation.add_fire(data['r'], data['c'])

@socketio.on('reset')
def handle_reset():
    simulation.reset()
    emit('state', simulation.get_state())

@socketio.on('trigger_alarm')
def handle_alarm():
    simulation.alarm_active = True
    simulation.evac_started = True

def simulation_loop():
    """Background thread running the simulation."""
    last_time = time.time()

    while running:
        current_time = time.time()
        dt = min(current_time - last_time, 0.1)
        last_time = current_time

        simulation.update(dt)

        # Broadcast state to all clients
        socketio.emit('state', simulation.get_state())

        time.sleep(0.033)  # ~30 FPS

if __name__ == '__main__':
    print("=" * 60)
    print("DWIGHT UX - Neural ACO Backend Server")
    print("=" * 60)
    print("\nStarting simulation server...")
    print("Open http://localhost:5000 in your browser")
    print("=" * 60)

    # Start simulation in background thread
    sim_thread = Thread(target=simulation_loop, daemon=True)
    sim_thread.start()

    # Run Flask server
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
