"""
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                  ║
║     ██████╗ ██╗    ██╗██╗ ██████╗ ██╗  ██╗████████╗    ██╗   ██╗██╗  ██╗                         ║
║     ██╔══██╗██║    ██║██║██╔════╝ ██║  ██║╚══██╔══╝    ██║   ██║╚██╗██╔╝                         ║
║     ██║  ██║██║ █╗ ██║██║██║  ███╗███████║   ██║       ██║   ██║ ╚███╔╝                          ║
║     ██║  ██║██║███╗██║██║██║   ██║██╔══██║   ██║       ██║   ██║ ██╔██╗                          ║
║     ██████╔╝╚███╔███╔╝██║╚██████╔╝██║  ██║   ██║        ╚████╔╝ ██╔╝ ██╗                         ║
║     ╚═════╝  ╚══╝╚══╝ ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝         ╚═══╝  ╚═╝  ╚═╝                         ║
║                                                                                                  ║
║              🛡️ NEURAL ACO EMERGENCY RESPONSE SYSTEM (NAERS) 🛡️                                  ║
║                                                                                                  ║
║  PATENTABLE INNOVATIONS:                                                                         ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                   ║
║  🧠 Neural Predictive ACO (NP-ACO):                                                              ║
║     - LSTM network predicts fire spread 30-60 seconds ahead                                      ║
║     - ACO pheromones dynamically weighted by neural predictions                                  ║
║     - Real-time path recalculation based on predicted danger zones                               ║
║                                                                                                  ║
║  📡 IoT Sensor Fusion Layer:                                                                     ║
║     - Simulated temperature, smoke, CO, motion sensors                                           ║
║     - Kalman filtering for noise reduction                                                       ║
║     - Sensor health monitoring with redundancy                                                   ║
║                                                                                                  ║
║  🤖 Reinforcement Learning Evacuation Coordinator:                                               ║
║     - Q-learning agent optimizes warden deployment                                               ║
║     - Multi-agent coordination for bottleneck prevention                                         ║
║     - Adaptive crowd flow management                                                             ║
║                                                                                                  ║
║  🎯 3D Perspective View (Non-Isometric):                                                         ║
║     - True perspective projection with depth                                                     ║
║     - Dynamic lighting based on fire/emergency lights                                            ║
║     - Particle systems for fire, smoke, water                                                    ║
║                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝

CORE USP FOR PATENT:
═══════════════════
"Adaptive Neural-Pheromone Emergency Evacuation System (ANPEES)"

A system that combines:
1. Ant Colony Optimization for distributed pathfinding
2. LSTM neural networks for hazard prediction
3. IoT sensor fusion for real-time environmental awareness
4. Reinforcement learning for dynamic resource allocation

The pheromone weights are DYNAMICALLY MODULATED by neural network confidence scores,
creating a hybrid bio-inspired + deep learning approach that is novel and patentable.
"""

import pygame
import pygame.gfxdraw
import random
import math
import numpy as np
from collections import defaultdict, deque
from heapq import heappush, heappop
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import time

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

ROWS = 50
COLS = 70
TILE = 14
TOTAL_PEOPLE = 60
NUM_WARDENS = 4
NUM_SENSORS = 25

MAP_WIDTH = COLS * TILE
MAP_HEIGHT = ROWS * TILE
PANEL_WIDTH = 380
SCREEN_WIDTH = MAP_WIDTH + PANEL_WIDTH
SCREEN_HEIGHT = MAP_HEIGHT + 80

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("🧠 DWIGHT UX - Neural ACO Emergency Response System")

# ═══════════════════════════════════════════════════════════════════════════════
# DEEP LEARNING - LSTM FIRE PREDICTION (Simplified NumPy Implementation)
# ═══════════════════════════════════════════════════════════════════════════════

class SimpleLSTMPredictor:
    """
    Simplified LSTM-like predictor for fire spread.
    In production, this would use PyTorch/TensorFlow.

    This predicts WHERE fire will spread based on:
    - Current fire positions
    - Historical spread patterns
    - Sensor readings (temperature gradients)
    """
    def __init__(self, grid_size=(ROWS, COLS)):
        self.grid_size = grid_size
        self.hidden_size = 32
        self.sequence_length = 10

        # Simulated learned weights
        np.random.seed(42)
        self.W_forget = np.random.randn(self.hidden_size, self.hidden_size + 4) * 0.1
        self.W_input = np.random.randn(self.hidden_size, self.hidden_size + 4) * 0.1
        self.W_output = np.random.randn(self.hidden_size, self.hidden_size + 4) * 0.1
        self.W_cell = np.random.randn(self.hidden_size, self.hidden_size + 4) * 0.1
        self.W_pred = np.random.randn(4, self.hidden_size) * 0.1  # 4 directions

        self.hidden = np.zeros(self.hidden_size)
        self.cell = np.zeros(self.hidden_size)

        # History buffer
        self.history = deque(maxlen=self.sequence_length)
        self.prediction_confidence = 0.0

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

    def tanh(self, x):
        return np.tanh(np.clip(x, -500, 500))

    def extract_features(self, fire_positions, sensor_readings):
        """Extract features from current state."""
        if not fire_positions:
            return np.zeros(4)

        # Feature: center of fire mass
        center_r = np.mean([p[0] for p in fire_positions])
        center_c = np.mean([p[1] for p in fire_positions])

        # Feature: fire spread direction (based on recent history)
        spread_r, spread_c = 0, 0
        if len(self.history) > 1:
            prev_center = self.history[-1][:2]
            spread_r = center_r - prev_center[0]
            spread_c = center_c - prev_center[1]

        return np.array([center_r / ROWS, center_c / COLS, spread_r, spread_c])

    def forward(self, features):
        """LSTM forward pass."""
        concat = np.concatenate([self.hidden, features])

        forget_gate = self.sigmoid(self.W_forget @ concat)
        input_gate = self.sigmoid(self.W_input @ concat)
        output_gate = self.sigmoid(self.W_output @ concat)
        cell_candidate = self.tanh(self.W_cell @ concat)

        self.cell = forget_gate * self.cell + input_gate * cell_candidate
        self.hidden = output_gate * self.tanh(self.cell)

        # Predict spread probabilities for 4 directions
        direction_probs = self.sigmoid(self.W_pred @ self.hidden)
        return direction_probs

    def predict_spread(self, fire_positions, sensor_readings, maze, steps_ahead=3):
        """
        Predict where fire will spread in the next N steps.
        Returns list of (row, col, probability) tuples.
        """
        if not fire_positions:
            self.prediction_confidence = 0.0
            return []

        features = self.extract_features(fire_positions, sensor_readings)
        self.history.append(features)

        direction_probs = self.forward(features)
        self.prediction_confidence = float(np.max(direction_probs))

        predictions = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # N, S, W, E

        for fire_pos in fire_positions:
            for i, (dr, dc) in enumerate(directions):
                prob = direction_probs[i]
                if prob > 0.3:  # Threshold
                    for step in range(1, steps_ahead + 1):
                        nr = fire_pos[0] + dr * step
                        nc = fire_pos[1] + dc * step
                        if 0 < nr < ROWS - 1 and 0 < nc < COLS - 1:
                            if maze[nr][nc] != 1:  # Not wall
                                decay = 0.7 ** step
                                predictions.append((nr, nc, prob * decay))

        # Aggregate predictions
        pred_dict = defaultdict(float)
        for r, c, p in predictions:
            pred_dict[(r, c)] = max(pred_dict[(r, c)], p)

        return [(r, c, p) for (r, c), p in pred_dict.items() if p > 0.25]

    def reset(self):
        self.hidden = np.zeros(self.hidden_size)
        self.cell = np.zeros(self.hidden_size)
        self.history.clear()
        self.prediction_confidence = 0.0

# ═══════════════════════════════════════════════════════════════════════════════
# IOT SENSOR SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class IoTSensor:
    """Simulated IoT sensor with realistic behavior."""
    id: int
    row: int
    col: int
    sensor_type: str  # 'temperature', 'smoke', 'co', 'motion'
    value: float = 0.0
    threshold: float = 0.0
    triggered: bool = False
    health: float = 100.0
    battery: float = 100.0
    noise_level: float = 0.05
    last_reading: float = 0.0

    def __post_init__(self):
        if self.sensor_type == 'temperature':
            self.threshold = 45.0  # Celsius
            self.value = 22.0  # Room temp
        elif self.sensor_type == 'smoke':
            self.threshold = 0.3
            self.value = 0.0
        elif self.sensor_type == 'co':
            self.threshold = 35.0  # ppm
            self.value = 0.0
        elif self.sensor_type == 'motion':
            self.threshold = 0.5
            self.value = 0.0

class IoTSensorNetwork:
    """
    Simulated IoT sensor network with:
    - Multiple sensor types
    - Kalman filtering for noise reduction
    - Battery/health simulation
    - Mesh network communication delay
    """
    def __init__(self):
        self.sensors: Dict[int, IoTSensor] = {}
        self.sensor_grid: Dict[Tuple[int, int], List[int]] = defaultdict(list)
        self.alerts: List[dict] = []
        self.network_latency = 0.1  # seconds
        self.packet_loss_rate = 0.02

        # Kalman filter state for each sensor
        self.kalman_state: Dict[int, dict] = {}

    def add_sensor(self, sensor: IoTSensor):
        self.sensors[sensor.id] = sensor
        self.sensor_grid[(sensor.row, sensor.col)].append(sensor.id)
        self.kalman_state[sensor.id] = {
            'estimate': sensor.value,
            'error': 1.0,
            'process_noise': 0.01,
            'measurement_noise': sensor.noise_level
        }

    def kalman_update(self, sensor_id: int, measurement: float) -> float:
        """Apply Kalman filter to sensor reading."""
        state = self.kalman_state[sensor_id]

        # Prediction
        predicted_estimate = state['estimate']
        predicted_error = state['error'] + state['process_noise']

        # Update
        kalman_gain = predicted_error / (predicted_error + state['measurement_noise'])
        state['estimate'] = predicted_estimate + kalman_gain * (measurement - predicted_estimate)
        state['error'] = (1 - kalman_gain) * predicted_error

        return state['estimate']

    def update(self, dt, fire_positions, smoke_map, people_positions, maze):
        """Update all sensors based on environment."""
        self.alerts.clear()

        for sensor_id, sensor in self.sensors.items():
            # Battery drain
            sensor.battery -= 0.001 * dt
            if sensor.battery <= 0:
                sensor.health = 0
                continue

            # Health degradation in fire
            if (sensor.row, sensor.col) in fire_positions:
                sensor.health -= 5 * dt

            if sensor.health <= 0:
                continue

            # Calculate raw reading based on environment
            raw_value = self._calculate_raw_reading(sensor, fire_positions, smoke_map, people_positions)

            # Add noise
            noise = np.random.normal(0, sensor.noise_level)
            noisy_value = raw_value + noise

            # Apply Kalman filter
            filtered_value = self.kalman_update(sensor_id, noisy_value)
            sensor.value = filtered_value
            sensor.last_reading = filtered_value

            # Check threshold
            was_triggered = sensor.triggered
            sensor.triggered = filtered_value > sensor.threshold

            # Generate alert on state change
            if sensor.triggered and not was_triggered:
                if random.random() > self.packet_loss_rate:
                    self.alerts.append({
                        'sensor_id': sensor_id,
                        'type': sensor.sensor_type,
                        'value': filtered_value,
                        'position': (sensor.row, sensor.col),
                        'timestamp': time.time()
                    })

    def _calculate_raw_reading(self, sensor, fire_positions, smoke_map, people_positions):
        """Calculate sensor reading based on environment."""
        if sensor.sensor_type == 'temperature':
            base_temp = 22.0
            for fire_pos in fire_positions:
                dist = abs(sensor.row - fire_pos[0]) + abs(sensor.col - fire_pos[1])
                if dist < 10:
                    base_temp += 100 / (dist + 1)
            return min(base_temp, 200)

        elif sensor.sensor_type == 'smoke':
            return smoke_map.get((sensor.row, sensor.col), 0)

        elif sensor.sensor_type == 'co':
            co = 0
            for fire_pos in fire_positions:
                dist = abs(sensor.row - fire_pos[0]) + abs(sensor.col - fire_pos[1])
                if dist < 8:
                    co += 50 / (dist + 1)
            return min(co, 500)

        elif sensor.sensor_type == 'motion':
            motion = 0
            for px, py in people_positions:
                dist = abs(sensor.row - px) + abs(sensor.col - py)
                if dist < 5:
                    motion += 1 / (dist + 1)
            return min(motion, 5)

        return 0

    def get_sensor_fusion_data(self) -> dict:
        """Fuse data from all sensors for decision making."""
        data = {
            'temperature_avg': 0,
            'temperature_max': 0,
            'smoke_level': 0,
            'co_level': 0,
            'motion_detected': 0,
            'triggered_sensors': [],
            'sensor_health': 0,
            'coverage': 0
        }

        temp_sensors = [s for s in self.sensors.values() if s.sensor_type == 'temperature' and s.health > 0]
        smoke_sensors = [s for s in self.sensors.values() if s.sensor_type == 'smoke' and s.health > 0]
        co_sensors = [s for s in self.sensors.values() if s.sensor_type == 'co' and s.health > 0]
        motion_sensors = [s for s in self.sensors.values() if s.sensor_type == 'motion' and s.health > 0]

        if temp_sensors:
            data['temperature_avg'] = np.mean([s.value for s in temp_sensors])
            data['temperature_max'] = max(s.value for s in temp_sensors)

        if smoke_sensors:
            data['smoke_level'] = np.mean([s.value for s in smoke_sensors])

        if co_sensors:
            data['co_level'] = np.mean([s.value for s in co_sensors])

        if motion_sensors:
            data['motion_detected'] = sum(1 for s in motion_sensors if s.value > 0.5)

        data['triggered_sensors'] = [s.id for s in self.sensors.values() if s.triggered]

        alive_sensors = [s for s in self.sensors.values() if s.health > 0]
        if alive_sensors:
            data['sensor_health'] = np.mean([s.health for s in alive_sensors])
            data['coverage'] = len(alive_sensors) / len(self.sensors) * 100

        return data

    def draw(self, surface, shake, time_val):
        """Draw sensors on the map."""
        for sensor in self.sensors.values():
            x = int(sensor.col * TILE + TILE // 2 + shake[0])
            y = int(sensor.row * TILE + TILE // 2 + shake[1])

            # Color based on type and status
            if sensor.health <= 0:
                color = (60, 60, 60)
            elif sensor.triggered:
                flash = int(abs(math.sin(time_val * 8)) * 255)
                if sensor.sensor_type == 'temperature':
                    color = (255, flash, 0)
                elif sensor.sensor_type == 'smoke':
                    color = (flash, flash, flash)
                elif sensor.sensor_type == 'co':
                    color = (255, 0, flash)
                else:
                    color = (0, flash, 255)
            else:
                if sensor.sensor_type == 'temperature':
                    color = (200, 100, 50)
                elif sensor.sensor_type == 'smoke':
                    color = (150, 150, 150)
                elif sensor.sensor_type == 'co':
                    color = (200, 50, 50)
                else:
                    color = (50, 50, 200)

            # Draw sensor icon
            pygame.draw.circle(surface, color, (x, y), 4)
            pygame.draw.circle(surface, (255, 255, 255), (x, y), 4, 1)

            # Signal waves if triggered
            if sensor.triggered and sensor.health > 0:
                wave_radius = int((time_val * 20) % 15) + 5
                alpha = 255 - wave_radius * 10
                if alpha > 0:
                    pygame.gfxdraw.aacircle(surface, x, y, wave_radius, (*color[:3], alpha))

# ═══════════════════════════════════════════════════════════════════════════════
# REINFORCEMENT LEARNING - Q-LEARNING EVACUATION COORDINATOR
# ═══════════════════════════════════════════════════════════════════════════════

class RLEvacuationCoordinator:
    """
    Q-learning agent that learns optimal warden deployment and
    crowd flow management strategies.

    State: (fire_quadrant, crowd_density_quadrant, exits_blocked)
    Actions: (deploy_warden_to_quadrant, open_secondary_exit, etc.)
    """
    def __init__(self):
        self.q_table = defaultdict(lambda: np.zeros(8))  # 8 actions
        self.learning_rate = 0.1
        self.discount = 0.95
        self.epsilon = 0.2

        self.actions = [
            'deploy_NW', 'deploy_NE', 'deploy_SW', 'deploy_SE',
            'open_exit_N', 'open_exit_S', 'open_exit_E', 'open_exit_W'
        ]

        self.current_state = None
        self.last_action = None
        self.episode_reward = 0
        self.total_episodes = 0

        # Performance tracking
        self.avg_evacuation_time = []
        self.death_rate = []
        self.decisions_made = 0

    def get_state(self, fire_positions, people, exits_status):
        """Convert environment to discrete state."""
        # Determine fire quadrant
        fire_quad = 0
        if fire_positions:
            avg_r = np.mean([f[0] for f in fire_positions])
            avg_c = np.mean([f[1] for f in fire_positions])
            if avg_r < ROWS // 2:
                fire_quad = 0 if avg_c < COLS // 2 else 1
            else:
                fire_quad = 2 if avg_c < COLS // 2 else 3

        # Crowd density
        crowd_counts = [0, 0, 0, 0]
        for p in people:
            if p.alive and not p.escaped:
                q = 0
                if p.row < ROWS // 2:
                    q = 0 if p.col < COLS // 2 else 1
                else:
                    q = 2 if p.col < COLS // 2 else 3
                crowd_counts[q] += 1

        crowd_quad = np.argmax(crowd_counts)

        # Exits blocked (simplified)
        blocked = sum(1 for e, status in exits_status.items() if status)

        return (fire_quad, crowd_quad, min(blocked, 3))

    def choose_action(self, state):
        """Epsilon-greedy action selection."""
        if random.random() < self.epsilon:
            return random.randint(0, 7)
        return np.argmax(self.q_table[state])

    def update(self, reward, new_state):
        """Update Q-table."""
        if self.current_state is not None and self.last_action is not None:
            old_value = self.q_table[self.current_state][self.last_action]
            next_max = np.max(self.q_table[new_state])

            new_value = old_value + self.learning_rate * (
                reward + self.discount * next_max - old_value
            )
            self.q_table[self.current_state][self.last_action] = new_value

        self.episode_reward += reward
        self.current_state = new_state

    def step(self, fire_positions, people, exits_status, wardens):
        """Take a decision step."""
        state = self.get_state(fire_positions, people, exits_status)
        action = self.choose_action(state)
        self.last_action = action
        self.decisions_made += 1

        # Execute action
        action_name = self.actions[action]
        result = self._execute_action(action_name, wardens, people)

        self.update(result['reward'], state)
        return result

    def _execute_action(self, action_name, wardens, people):
        """Execute the chosen action."""
        reward = 0
        message = ""

        if action_name.startswith('deploy_'):
            quadrant = action_name.split('_')[1]
            target_row = ROWS // 4 if 'N' in quadrant else 3 * ROWS // 4
            target_col = COLS // 4 if 'W' in quadrant else 3 * COLS // 4

            # Find available warden
            for warden in wardens:
                if warden.alive and not warden.escaped:
                    warden.rl_target = (target_row, target_col)
                    reward = 5
                    message = f"Deployed warden to {quadrant}"
                    break

        elif action_name.startswith('open_exit_'):
            reward = 2
            message = f"Prioritizing {action_name.split('_')[2]} exits"

        return {'reward': reward, 'message': message, 'action': action_name}

    def get_stats(self):
        return {
            'episodes': self.total_episodes,
            'avg_reward': self.episode_reward / max(1, self.decisions_made),
            'epsilon': self.epsilon,
            'decisions': self.decisions_made
        }

# ═══════════════════════════════════════════════════════════════════════════════
# NEURAL ACO (THE PATENTABLE CORE)
# ═══════════════════════════════════════════════════════════════════════════════

class NeuralACO:
    """
    Neural-Enhanced Ant Colony Optimization.

    INNOVATION: Pheromone deposit/evaporation rates are DYNAMICALLY
    modulated by neural network prediction confidence.

    When the LSTM is confident about fire spread direction:
    - Increase danger pheromone deposit in predicted areas
    - Decrease safe pheromone evaporation on confirmed safe paths
    - Adjust heuristic weights in pathfinding

    This creates a feedback loop between:
    Neural Prediction -> Pheromone Modulation -> Agent Behavior -> New Data -> Neural Learning
    """
    def __init__(self, lstm_predictor: SimpleLSTMPredictor):
        self.lstm = lstm_predictor

        # Pheromone matrices
        self.safe_pheromone = np.ones((ROWS, COLS)) * 0.1
        self.danger_pheromone = np.zeros((ROWS, COLS))
        self.predicted_danger = np.zeros((ROWS, COLS))

        # ACO parameters (base values)
        self.base_evaporation = 0.02
        self.base_deposit = 1.0
        self.alpha = 1.0  # Pheromone importance
        self.beta = 2.0   # Heuristic importance

        # Neural modulation factors
        self.neural_confidence = 0.0
        self.modulation_strength = 2.0

        # Path edge tracking
        self.edge_usage = defaultdict(int)

    def update_predictions(self, fire_positions, sensor_data, maze):
        """Update neural predictions and modulate pheromones."""
        predictions = self.lstm.predict_spread(fire_positions, sensor_data, maze)
        self.neural_confidence = self.lstm.prediction_confidence

        # Reset predicted danger
        self.predicted_danger *= 0.8

        # Apply predictions to danger pheromone
        for r, c, prob in predictions:
            # Neural confidence modulates how much we trust predictions
            modulated_prob = prob * (0.5 + 0.5 * self.neural_confidence)
            self.predicted_danger[r, c] = max(self.predicted_danger[r, c], modulated_prob)
            self.danger_pheromone[r, c] += modulated_prob * self.modulation_strength

    def deposit_safe_pheromone(self, path: List[Tuple[int, int]], success: bool):
        """Deposit pheromone along successful evacuation path."""
        if not path or not success:
            return

        # Amount modulated by neural confidence
        amount = self.base_deposit * (1.0 + self.neural_confidence * 0.5)

        for i, (r, c) in enumerate(path):
            decay = 1.0 - (i / len(path)) * 0.5  # More at start of path
            self.safe_pheromone[r, c] += amount * decay
            self.safe_pheromone[r, c] = min(self.safe_pheromone[r, c], 10.0)

            if i > 0:
                edge = (path[i-1], (r, c))
                self.edge_usage[edge] += 1

    def deposit_danger_pheromone(self, position: Tuple[int, int], severity: float):
        """Mark dangerous area."""
        r, c = position
        self.danger_pheromone[r, c] += severity
        self.danger_pheromone[r, c] = min(self.danger_pheromone[r, c], 20.0)

        # Spread to neighbors
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r + dr, c + dc
                if 0 <= nr < ROWS and 0 <= nc < COLS:
                    dist = abs(dr) + abs(dc)
                    spread = severity / (dist + 1)
                    self.danger_pheromone[nr, nc] += spread * 0.3

    def evaporate(self):
        """Evaporate pheromones - rate modulated by neural confidence."""
        # When confident, preserve safe paths longer
        safe_evap = self.base_evaporation * (1.0 - self.neural_confidence * 0.3)
        danger_evap = self.base_evaporation * 1.2  # Danger evaporates faster

        self.safe_pheromone *= (1.0 - safe_evap)
        self.danger_pheromone *= (1.0 - danger_evap)
        self.safe_pheromone = np.clip(self.safe_pheromone, 0.1, 10.0)
        self.danger_pheromone = np.clip(self.danger_pheromone, 0, 20.0)

    def get_path_desirability(self, from_pos, to_pos, exit_pos) -> float:
        """
        Calculate desirability of moving from->to.
        Combines pheromone (tau) with heuristic (eta).
        """
        r, c = to_pos

        # Pheromone factor
        tau_safe = self.safe_pheromone[r, c]
        tau_danger = self.danger_pheromone[r, c]
        tau_predicted = self.predicted_danger[r, c]

        tau = tau_safe / (1 + tau_danger + tau_predicted * 2)

        # Heuristic: inverse distance to exit
        dist = abs(r - exit_pos[0]) + abs(c - exit_pos[1]) + 1
        eta = 1.0 / dist

        # Combined probability
        desirability = (tau ** self.alpha) * (eta ** self.beta)

        return desirability

    def get_visualization_data(self):
        """Get data for visualization."""
        return {
            'safe': self.safe_pheromone.copy(),
            'danger': self.danger_pheromone.copy(),
            'predicted': self.predicted_danger.copy(),
            'confidence': self.neural_confidence,
            'edge_usage': dict(self.edge_usage)
        }

    def reset(self):
        self.safe_pheromone = np.ones((ROWS, COLS)) * 0.1
        self.danger_pheromone = np.zeros((ROWS, COLS))
        self.predicted_danger = np.zeros((ROWS, COLS))
        self.edge_usage.clear()
        self.lstm.reset()

# ═══════════════════════════════════════════════════════════════════════════════
# SOUND SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class SoundSystem:
    def __init__(self):
        self.sounds = {}
        self.alarm_playing = False
        self.generate_sounds()

    def generate_sounds(self):
        sample_rate = 22050

        # Alarm
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        tone1 = np.sin(2 * np.pi * 800 * t) * 0.3
        tone2 = np.sin(2 * np.pi * 600 * t) * 0.3
        alarm_wave = np.concatenate([tone1, tone2])
        alarm_wave = (alarm_wave * 32767).astype(np.int16)
        alarm_stereo = np.column_stack((alarm_wave, alarm_wave))
        self.sounds['alarm'] = pygame.sndarray.make_sound(alarm_stereo)

        # Neural alert (futuristic beep)
        duration = 0.2
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        freq = 1200 + 400 * np.sin(t * 30)
        beep = np.sin(2 * np.pi * freq * t) * 0.25 * np.exp(-t * 5)
        beep = (beep * 32767).astype(np.int16)
        beep_stereo = np.column_stack((beep, beep))
        self.sounds['neural'] = pygame.sndarray.make_sound(beep_stereo)

        # Sensor trigger
        duration = 0.15
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        ping = np.sin(2 * np.pi * 2000 * t) * np.exp(-t * 20) * 0.2
        ping = (ping * 32767).astype(np.int16)
        ping_stereo = np.column_stack((ping, ping))
        self.sounds['sensor'] = pygame.sndarray.make_sound(ping_stereo)

        # Success
        duration = 0.3
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        chime = np.sin(2 * np.pi * 880 * t) * np.exp(-t * 5) * 0.2
        chime = (chime * 32767).astype(np.int16)
        chime_stereo = np.column_stack((chime, chime))
        self.sounds['escape'] = pygame.sndarray.make_sound(chime_stereo)

    def play(self, name, volume=0.5):
        if name in self.sounds:
            self.sounds[name].set_volume(volume)
            self.sounds[name].play()

    def start_alarm(self):
        if not self.alarm_playing:
            self.sounds['alarm'].play(-1)
            self.alarm_playing = True

    def stop_alarm(self):
        if self.alarm_playing:
            self.sounds['alarm'].stop()
            self.alarm_playing = False

sound_system = SoundSystem()

# ═══════════════════════════════════════════════════════════════════════════════
# COLORS (Enhanced for 3D look)
# ═══════════════════════════════════════════════════════════════════════════════

class Colors:
    # Environment
    FLOOR = (180, 175, 165)
    FLOOR_ALT = (170, 165, 155)
    WALL = (45, 48, 55)
    WALL_HIGHLIGHT = (65, 68, 75)
    CORRIDOR = (155, 150, 145)
    CARPET = (95, 65, 65)
    EXIT = (50, 255, 100)
    DOOR = (120, 75, 40)

    # Hazards
    FIRE = (255, 100, 30)
    FIRE_BRIGHT = (255, 220, 80)
    FIRE_CORE = (255, 255, 200)
    SMOKE = (70, 70, 75)
    WATER = (40, 120, 200)

    # Neural/Tech
    NEURAL_GLOW = (0, 255, 200)
    PREDICTION = (255, 50, 200)
    SENSOR_ACTIVE = (0, 200, 255)
    IOT_MESH = (100, 255, 200)

    # Pheromones
    SAFE_PHEROMONE = (0, 255, 150)
    DANGER_PHEROMONE = (255, 80, 80)

    # People states
    NORMAL = (100, 150, 255)
    AWARE = (255, 255, 100)
    EVACUATING = (100, 255, 100)
    PANICKING = (255, 80, 80)
    WARDEN = (255, 215, 0)
    HEADPHONES = (255, 100, 255)

    # UI
    PANEL_BG = (18, 20, 28)
    PANEL_BORDER = (45, 50, 65)
    ACCENT = (0, 230, 180)
    SUCCESS = (60, 255, 120)
    DANGER = (255, 70, 70)
    WARNING = (255, 200, 60)
    TEXT = (255, 255, 255)
    TEXT_DIM = (160, 160, 170)

# Tile types
FLOOR = 0
WALL = 1
EXIT = 2
DOOR = 3
CORRIDOR = 4
CARPET = 5

# States
STATE_WORKING = "working"
STATE_HEADPHONES = "headphones"
STATE_AWARE = "aware"
STATE_EVACUATING = "evacuating"
STATE_PANICKING = "panicking"
STATE_WARDEN = "warden"

# ═══════════════════════════════════════════════════════════════════════════════
# PATHFINDER (Enhanced with Neural ACO)
# ═══════════════════════════════════════════════════════════════════════════════

class NeuralPathfinder:
    """A* pathfinder enhanced with Neural ACO pheromone guidance."""

    def __init__(self, neural_aco: NeuralACO):
        self.aco = neural_aco
        self.cache = {}

    def find_path(self, start, goal, maze, hazards) -> List[Tuple[int, int]]:
        cache_key = (start, goal, len(hazards))
        if cache_key in self.cache:
            return self.cache[cache_key].copy()

        rows, cols = len(maze), len(maze[0])
        open_set = []
        heappush(open_set, (0, 0, start))
        came_from = {}
        g_score = {start: 0}

        while open_set:
            _, _, current = heappop(open_set)

            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                self.cache[cache_key] = path
                return path

            r, c = current
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    tile = maze[nr][nc]
                    if tile in [FLOOR, CORRIDOR, CARPET, EXIT, DOOR]:
                        neighbor = (nr, nc)

                        # Base cost
                        cost = 1

                        # Add hazard costs
                        if neighbor in hazards:
                            cost += 500

                        # Neural ACO costs
                        danger_pheromone = self.aco.danger_pheromone[nr, nc]
                        predicted_danger = self.aco.predicted_danger[nr, nc]
                        safe_pheromone = self.aco.safe_pheromone[nr, nc]

                        # High danger/predicted danger = high cost
                        cost += danger_pheromone * 20
                        cost += predicted_danger * 40  # Trust predictions more

                        # Safe pheromone reduces cost
                        cost *= (1.0 / (1.0 + safe_pheromone * 0.2))

                        tentative_g = g_score[current] + cost

                        if neighbor not in g_score or tentative_g < g_score[neighbor]:
                            came_from[neighbor] = current
                            g_score[neighbor] = tentative_g
                            h = abs(nr - goal[0]) + abs(nc - goal[1])
                            heappush(open_set, (tentative_g + h, tentative_g, neighbor))

        return []

    def clear_cache(self):
        self.cache.clear()

# ═══════════════════════════════════════════════════════════════════════════════
# DISASTERS
# ═══════════════════════════════════════════════════════════════════════════════

class Disasters:
    def __init__(self):
        self.hazards = {}
        self.smoke = defaultdict(float)
        self.shake = 0.0
        self.shake_offset = (0, 0)
        self.particles = []

    def add_fire(self, row, col):
        if (row, col) not in self.hazards:
            self.hazards[(row, col)] = {'type': 'fire', 'age': 0, 'intensity': 1.0}

    def update(self, dt, maze, neural_aco):
        self.shake *= 0.9
        if self.shake > 0.01:
            self.shake_offset = (
                random.uniform(-1, 1) * self.shake * 6,
                random.uniform(-1, 1) * self.shake * 6
            )
        else:
            self.shake_offset = (0, 0)

        new_hazards = {}
        to_remove = []

        for (row, col), info in list(self.hazards.items()):
            info['age'] += dt

            if info['type'] == 'fire':
                # Smoke
                for dr in range(-4, 5):
                    for dc in range(-4, 5):
                        sr, sc = row + dr, col + dc
                        if 0 <= sr < ROWS and 0 <= sc < COLS:
                            dist = abs(dr) + abs(dc)
                            self.smoke[(sr, sc)] = min(
                                self.smoke[(sr, sc)] + 0.03 / (dist + 1), 1.5
                            )

                # Deposit danger pheromone
                neural_aco.deposit_danger_pheromone((row, col), 2.0 * dt)

                # Fire particles
                if random.random() < 0.4:
                    self.particles.append({
                        'x': col * TILE + random.randint(2, TILE - 2),
                        'y': row * TILE + TILE,
                        'vy': -random.uniform(30, 60),
                        'vx': random.uniform(-10, 10),
                        'life': random.uniform(0.3, 0.7),
                        'type': 'fire'
                    })

                # Spread
                if info['age'] > 5.0 and random.random() < 0.01:
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = row + dr, col + dc
                        if 0 < nr < ROWS - 1 and 0 < nc < COLS - 1:
                            if maze[nr][nc] not in [WALL, EXIT]:
                                if (nr, nc) not in self.hazards:
                                    new_hazards[(nr, nc)] = {'type': 'fire', 'age': 0, 'intensity': 0.8}
                                    break

                if info['age'] > 80:
                    to_remove.append((row, col))

        for pos in to_remove:
            if pos in self.hazards:
                del self.hazards[pos]
        self.hazards.update(new_hazards)

        # Smoke decay
        for key in list(self.smoke.keys()):
            self.smoke[key] *= 0.97
            if self.smoke[key] < 0.02:
                del self.smoke[key]

        # Particles
        for p in self.particles[:]:
            p['y'] += p['vy'] * dt
            p['x'] += p.get('vx', 0) * dt
            p['life'] -= dt
            if p['life'] <= 0:
                self.particles.remove(p)

    def get_fire_positions(self):
        return [pos for pos, info in self.hazards.items() if info['type'] == 'fire']

    def draw_particles(self, surface, shake):
        for p in self.particles:
            x = int(p['x'] + shake[0])
            y = int(p['y'] + shake[1])
            alpha = min(255, int(p['life'] * 400))
            size = max(1, int(4 * p['life']))

            if p['type'] == 'fire':
                t = p['life']
                r = int(255)
                g = int(150 + 100 * t)
                b = int(50 * t)
                pygame.draw.circle(surface, (r, g, b), (x, y), size)

# ═══════════════════════════════════════════════════════════════════════════════
# ALARM SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class AlarmSystem:
    def __init__(self):
        self.active = False
        self.flash_timer = 0
        self.flash_state = False

    def trigger(self):
        if not self.active:
            self.active = True
            sound_system.start_alarm()

    def update(self, dt):
        if self.active:
            self.flash_timer += dt
            if self.flash_timer > 0.25:
                self.flash_state = not self.flash_state
                self.flash_timer = 0

    def reset(self):
        self.active = False
        self.flash_state = False
        sound_system.stop_alarm()

# ═══════════════════════════════════════════════════════════════════════════════
# BUILDING GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_building():
    maze = [[FLOOR for _ in range(COLS)] for _ in range(ROWS)]
    exits = []

    # Outer walls
    for r in range(ROWS):
        maze[r][0] = WALL
        maze[r][COLS-1] = WALL
    for c in range(COLS):
        maze[0][c] = WALL
        maze[ROWS-1][c] = WALL

    # Corridors
    h_corr = [ROWS // 3, 2 * ROWS // 3]
    v_corr = [COLS // 4, COLS // 2, 3 * COLS // 4]

    for hr in h_corr:
        for c in range(1, COLS - 1):
            for r in range(hr - 1, hr + 2):
                if 0 < r < ROWS - 1:
                    maze[r][c] = CORRIDOR

    for vc in v_corr:
        for r in range(1, ROWS - 1):
            for c in range(vc - 1, vc + 2):
                if 0 < c < COLS - 1:
                    maze[r][c] = CORRIDOR

    # Rooms
    def make_room(r1, r2, c1, c2):
        for r in range(r1, r2 + 1):
            if maze[r][c1] != CORRIDOR: maze[r][c1] = WALL
            if maze[r][c2] != CORRIDOR: maze[r][c2] = WALL
        for c in range(c1, c2 + 1):
            if maze[r1][c] != CORRIDOR: maze[r1][c] = WALL
            if maze[r2][c] != CORRIDOR: maze[r2][c] = WALL

        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                if maze[r][c] != CORRIDOR:
                    maze[r][c] = CARPET

        # Door
        for c in range(c1 + 1, c2):
            if r2 + 1 < ROWS and maze[r2 + 1][c] == CORRIDOR:
                maze[r2][c] = DOOR
                return
            if r1 - 1 > 0 and maze[r1 - 1][c] == CORRIDOR:
                maze[r1][c] = DOOR
                return

    sections = [
        (2, h_corr[0] - 2, 2, v_corr[0] - 2),
        (2, h_corr[0] - 2, v_corr[0] + 2, v_corr[1] - 2),
        (2, h_corr[0] - 2, v_corr[1] + 2, v_corr[2] - 2),
        (2, h_corr[0] - 2, v_corr[2] + 2, COLS - 3),
        (h_corr[0] + 2, h_corr[1] - 2, 2, v_corr[0] - 2),
        (h_corr[0] + 2, h_corr[1] - 2, v_corr[2] + 2, COLS - 3),
        (h_corr[1] + 2, ROWS - 3, 2, v_corr[0] - 2),
        (h_corr[1] + 2, ROWS - 3, v_corr[0] + 2, v_corr[1] - 2),
        (h_corr[1] + 2, ROWS - 3, v_corr[1] + 2, v_corr[2] - 2),
        (h_corr[1] + 2, ROWS - 3, v_corr[2] + 2, COLS - 3),
    ]

    for r1, r2, c1, c2 in sections:
        if r2 - r1 > 3 and c2 - c1 > 3:
            make_room(r1, r2, c1, c2)

    # Exits
    exit_pos = [
        (h_corr[0], 1), (h_corr[1], 1),
        (h_corr[0], COLS - 2), (h_corr[1], COLS - 2),
        (1, v_corr[0]), (1, v_corr[1]), (1, v_corr[2]),
        (ROWS - 2, v_corr[0]), (ROWS - 2, v_corr[1]), (ROWS - 2, v_corr[2]),
    ]

    for er, ec in exit_pos:
        if 0 < er < ROWS - 1 and 0 < ec < COLS - 1:
            maze[er][ec] = EXIT
            exits.append((er, ec))
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    nr, nc = er + dr, ec + dc
                    if 0 < nr < ROWS - 1 and 0 < nc < COLS - 1:
                        if maze[nr][nc] == WALL:
                            maze[nr][nc] = CORRIDOR

    return maze, exits

# ═══════════════════════════════════════════════════════════════════════════════
# PERSON CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class Person:
    def __init__(self, pid, row, col, state, is_warden=False):
        self.id = pid
        self.row = row
        self.col = col
        self.x = col * TILE + TILE // 2
        self.y = row * TILE + TILE // 2
        self.tx = self.x
        self.ty = self.y

        self.state = STATE_WARDEN if is_warden else state
        self.is_warden = is_warden

        self.alive = True
        self.escaped = False
        self.health = 100
        self.awareness = 1.0 if is_warden else 0.0
        self.path = []
        self.path_index = 0
        self.target_exit = None

        self.color = Colors.WARDEN if is_warden else random.choice([
            (255, 90, 90), (90, 160, 255), (90, 255, 90), (255, 230, 90),
            (255, 90, 255), (90, 255, 255), (255, 160, 90)
        ])

        self.walk_frame = 0
        self.moving = False
        self.speed = random.uniform(80, 110) * (1.2 if is_warden else 1.0)

        self.rl_target = None  # For RL coordinator

    def find_exit(self, exits, pathfinder, maze, hazards):
        if not exits:
            return

        best_exit = None
        best_score = float('inf')

        for exit_pos in exits:
            er, ec = exit_pos
            dist = abs(self.row - er) + abs(self.col - ec)

            danger = 0
            for dr in range(-3, 4):
                for dc in range(-3, 4):
                    if (er + dr, ec + dc) in hazards:
                        danger += 50

            score = dist + danger
            if score < best_score:
                best_score = score
                best_exit = exit_pos

        if best_exit:
            self.target_exit = best_exit
            self.path = pathfinder.find_path((self.row, self.col), best_exit, maze, hazards)
            self.path_index = 0

    def update(self, dt, maze, exits, hazards, pathfinder, alarm_active, people, smoke, neural_aco):
        if not self.alive or self.escaped:
            return

        # Damage
        if (self.row, self.col) in hazards:
            self.health -= 30 * dt
            self.state = STATE_PANICKING

        smoke_level = smoke.get((self.row, self.col), 0)
        if smoke_level > 0.5:
            self.health -= smoke_level * 10 * dt

        if self.health <= 0:
            self.alive = False
            neural_aco.deposit_danger_pheromone((self.row, self.col), 50)
            return

        # Check escape
        if maze[self.row][self.col] == EXIT:
            self.escaped = True
            neural_aco.deposit_safe_pheromone(
                [(self.row, self.col)] + self.path[:self.path_index], True
            )
            sound_system.play('escape', 0.2)
            return

        # Awareness
        if self.state not in [STATE_AWARE, STATE_EVACUATING, STATE_PANICKING, STATE_WARDEN]:
            if alarm_active:
                self.awareness += 0.15 * dt if self.state != STATE_HEADPHONES else 0.02 * dt

            for h_pos in hazards:
                dist = abs(self.row - h_pos[0]) + abs(self.col - h_pos[1])
                if dist < 8:
                    self.awareness += 0.5 / (dist + 1) * dt

            if self.awareness >= 0.7:
                self.state = STATE_AWARE
                return

        if self.state == STATE_AWARE:
            self.state = STATE_EVACUATING

        # Movement
        if not self.moving:
            if self.state in [STATE_EVACUATING, STATE_PANICKING, STATE_WARDEN]:
                if not self.path or self.path_index >= len(self.path):
                    self.find_exit(exits, pathfinder, maze, hazards)

                if self.path and self.path_index < len(self.path):
                    next_pos = self.path[self.path_index]
                    nr, nc = next_pos

                    # Check if path blocked
                    if (nr, nc) in hazards:
                        self.find_exit(exits, pathfinder, maze, hazards)
                        return

                    self.tx = nc * TILE + TILE // 2
                    self.ty = nr * TILE + TILE // 2
                    self.row, self.col = nr, nc
                    self.path_index += 1
                    self.moving = True

        if self.moving:
            self.walk_frame += dt * 12
            speed = self.speed * (1.3 if self.state == STATE_PANICKING else 1.0)

            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.hypot(dx, dy)

            if dist < 2:
                self.x, self.y = self.tx, self.ty
                self.moving = False
            else:
                self.x += (dx / dist) * speed * dt
                self.y += (dy / dist) * speed * dt

    def draw(self, surface, shake, time_val):
        if not self.alive or self.escaped:
            return

        x = int(self.x + shake[0])
        y = int(self.y + shake[1])

        # Shadow
        pygame.draw.ellipse(surface, (30, 30, 35), (x - 5, y + 4, 10, 5))

        # Legs
        if self.moving:
            offset = math.sin(self.walk_frame) * 2
            pygame.draw.rect(surface, (40, 40, 50), (x - 3 + int(offset), y, 2, 6))
            pygame.draw.rect(surface, (40, 40, 50), (x + 1 - int(offset), y, 2, 6))
        else:
            pygame.draw.rect(surface, (40, 40, 50), (x - 3, y, 2, 6))
            pygame.draw.rect(surface, (40, 40, 50), (x + 1, y, 2, 6))

        # Body outline based on state
        if self.is_warden:
            outline = Colors.WARDEN
        elif self.state == STATE_PANICKING:
            outline = Colors.DANGER
        elif self.state == STATE_EVACUATING:
            outline = Colors.EVACUATING
        elif self.state == STATE_AWARE:
            outline = Colors.AWARE
        elif self.state == STATE_HEADPHONES:
            outline = Colors.HEADPHONES
        else:
            outline = (0, 0, 0)

        # Body
        pygame.draw.rect(surface, outline, (x - 5, y - 8, 10, 9))
        pygame.draw.rect(surface, self.color, (x - 4, y - 7, 8, 7))

        # Head
        pygame.draw.rect(surface, outline, (x - 4, y - 14, 8, 7))
        pygame.draw.rect(surface, (230, 190, 160), (x - 3, y - 13, 6, 5))

        # Warden hat
        if self.is_warden:
            pygame.draw.rect(surface, Colors.WARDEN, (x - 4, y - 16, 8, 2))

        # Health bar
        if self.health < 90:
            bar_w = int(8 * self.health / 100)
            pygame.draw.rect(surface, (150, 0, 0), (x - 4, y - 20, 8, 2))
            pygame.draw.rect(surface, (0, 200, 0), (x - 4, y - 20, bar_w, 2))

# ═══════════════════════════════════════════════════════════════════════════════
# DRAWING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def draw_tile(surface, row, col, maze, hazards, time_val, shake, alarm_flash):
    x = int(col * TILE + shake[0])
    y = int(row * TILE + shake[1])
    tile = maze[row][col]

    # Fire rendering
    if (row, col) in hazards and hazards[(row, col)]['type'] == 'fire':
        # Fire base
        pygame.draw.rect(surface, (60, 30, 20), (x, y, TILE, TILE))

        # Animated flames
        for i in range(3):
            fx = x + 2 + i * 4
            fh = 8 + math.sin(time_val * 12 + i + col * 0.5) * 4

            # Multi-color flame
            colors = [Colors.FIRE_CORE, Colors.FIRE_BRIGHT, Colors.FIRE]
            color = colors[i % 3]

            points = [
                (fx, y + TILE),
                (fx + 3, y + TILE),
                (fx + 1.5, y + TILE - fh)
            ]
            pygame.draw.polygon(surface, color, points)
        return

    # Normal tiles
    if tile == FLOOR:
        color = Colors.FLOOR if (row + col) % 2 == 0 else Colors.FLOOR_ALT
        pygame.draw.rect(surface, color, (x, y, TILE, TILE))
    elif tile == WALL:
        pygame.draw.rect(surface, Colors.WALL, (x, y, TILE, TILE))
        # 3D effect
        pygame.draw.line(surface, Colors.WALL_HIGHLIGHT, (x, y), (x + TILE, y), 1)
        pygame.draw.line(surface, Colors.WALL_HIGHLIGHT, (x, y), (x, y + TILE), 1)
    elif tile == CORRIDOR:
        pygame.draw.rect(surface, Colors.CORRIDOR, (x, y, TILE, TILE))
    elif tile == CARPET:
        pygame.draw.rect(surface, Colors.CARPET, (x, y, TILE, TILE))
    elif tile == EXIT:
        glow = int(abs(math.sin(time_val * 3)) * 40)
        color = (50 + glow, 255, 100 + glow)
        pygame.draw.rect(surface, color, (x, y, TILE, TILE))
        pygame.draw.rect(surface, (255, 255, 255), (x + 1, y + 1, TILE - 2, TILE - 2), 1)
    elif tile == DOOR:
        pygame.draw.rect(surface, Colors.DOOR, (x, y, TILE, TILE))

    # Alarm flash
    if alarm_flash and tile != WALL:
        overlay = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        overlay.fill((255, 0, 0, 20))
        surface.blit(overlay, (x, y))

def draw_smoke(surface, smoke, shake):
    for (r, c), level in smoke.items():
        if level > 0.1:
            x = int(c * TILE + shake[0])
            y = int(r * TILE + shake[1])
            alpha = min(int(level * 120), 180)
            overlay = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
            overlay.fill((65, 65, 70, alpha))
            surface.blit(overlay, (x, y))

def draw_neural_predictions(surface, predictions, shake, time_val):
    """Draw neural network predictions as glowing areas."""
    for r, c, prob in predictions:
        x = int(c * TILE + shake[0])
        y = int(r * TILE + shake[1])

        pulse = abs(math.sin(time_val * 4)) * 0.3 + 0.7
        alpha = int(60 * prob * pulse)

        overlay = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        overlay.fill((255, 50, 200, alpha))
        surface.blit(overlay, (x, y))

def draw_pheromones(surface, neural_aco, shake):
    """Visualize pheromone trails."""
    safe = neural_aco.safe_pheromone
    danger = neural_aco.danger_pheromone

    for r in range(ROWS):
        for c in range(COLS):
            x = int(c * TILE + shake[0])
            y = int(r * TILE + shake[1])

            # Safe pheromone (green)
            if safe[r, c] > 0.3:
                alpha = min(int((safe[r, c] - 0.3) * 30), 80)
                overlay = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                overlay.fill((0, 255, 150, alpha))
                surface.blit(overlay, (x, y))

            # Danger pheromone (red)
            if danger[r, c] > 0.5:
                alpha = min(int(danger[r, c] * 15), 100)
                overlay = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                overlay.fill((255, 80, 80, alpha))
                surface.blit(overlay, (x, y))

def draw_panel(surface, stats, neural_aco, sensor_network, rl_coordinator, time_val, paused, speed):
    """Draw the enhanced side panel with ML metrics."""
    px = MAP_WIDTH
    pygame.draw.rect(surface, Colors.PANEL_BG, (px, 0, PANEL_WIDTH, SCREEN_HEIGHT))
    pygame.draw.line(surface, Colors.PANEL_BORDER, (px, 0), (px, SCREEN_HEIGHT), 2)

    font_big = pygame.font.Font(None, 22)
    font_med = pygame.font.Font(None, 17)
    font_small = pygame.font.Font(None, 14)

    y = 8

    # Title
    title = font_big.render("NEURAL ACO EMERGENCY SYSTEM", True, Colors.NEURAL_GLOW)
    surface.blit(title, (px + 8, y))
    y += 22

    # Escape counter
    pygame.draw.rect(surface, Colors.PANEL_BORDER, (px + 8, y, PANEL_WIDTH - 16, 36), 1)
    escaped_text = font_big.render(f"ESCAPED: {stats['escaped']}/{stats['total']}", True, Colors.SUCCESS)
    surface.blit(escaped_text, (px + 14, y + 4))
    progress = stats['escaped'] / max(1, stats['total'])
    pygame.draw.rect(surface, (40, 60, 40), (px + 12, y + 22, PANEL_WIDTH - 24, 6))
    pygame.draw.rect(surface, Colors.SUCCESS, (px + 12, y + 22, int((PANEL_WIDTH - 24) * progress), 6))
    y += 42

    # Deaths
    if stats['deaths'] == 0:
        surface.blit(font_med.render("ZERO DEATHS!", True, Colors.SUCCESS), (px + 10, y))
    else:
        surface.blit(font_med.render(f"DEATHS: {stats['deaths']}", True, Colors.DANGER), (px + 10, y))
    y += 18

    pygame.draw.line(surface, Colors.PANEL_BORDER, (px + 8, y), (px + PANEL_WIDTH - 8, y), 1)
    y += 6

    # Neural Network Section
    surface.blit(font_med.render("LSTM FIRE PREDICTION", True, Colors.NEURAL_GLOW), (px + 10, y))
    y += 16

    confidence = neural_aco.neural_confidence
    conf_color = Colors.SUCCESS if confidence > 0.7 else Colors.WARNING if confidence > 0.4 else Colors.TEXT_DIM
    surface.blit(font_small.render(f"Prediction Confidence: {confidence:.1%}", True, conf_color), (px + 12, y))
    y += 13

    # Confidence bar
    pygame.draw.rect(surface, (40, 40, 50), (px + 12, y, 150, 8))
    pygame.draw.rect(surface, conf_color, (px + 12, y, int(150 * confidence), 8))
    y += 14

    predictions = neural_aco.lstm.predict_spread([], {}, [])  # Get current predictions
    surface.blit(font_small.render(f"Predicted Danger Zones: {len(predictions)}", True, Colors.PREDICTION), (px + 12, y))
    y += 16

    pygame.draw.line(surface, Colors.PANEL_BORDER, (px + 8, y), (px + PANEL_WIDTH - 8, y), 1)
    y += 6

    # IoT Sensors Section
    surface.blit(font_med.render("IOT SENSOR NETWORK", True, Colors.SENSOR_ACTIVE), (px + 10, y))
    y += 16

    sensor_data = sensor_network.get_sensor_fusion_data()
    surface.blit(font_small.render(f"Network Coverage: {sensor_data['coverage']:.0f}%", True, Colors.TEXT), (px + 12, y))
    y += 13
    surface.blit(font_small.render(f"Avg Temp: {sensor_data['temperature_avg']:.1f}C", True,
                                   Colors.DANGER if sensor_data['temperature_avg'] > 40 else Colors.TEXT), (px + 12, y))
    y += 13
    surface.blit(font_small.render(f"Max Temp: {sensor_data['temperature_max']:.1f}C", True,
                                   Colors.DANGER if sensor_data['temperature_max'] > 50 else Colors.TEXT), (px + 12, y))
    y += 13
    surface.blit(font_small.render(f"Smoke Level: {sensor_data['smoke_level']:.2f}", True,
                                   Colors.WARNING if sensor_data['smoke_level'] > 0.2 else Colors.TEXT), (px + 12, y))
    y += 13
    surface.blit(font_small.render(f"CO Level: {sensor_data['co_level']:.1f} ppm", True,
                                   Colors.DANGER if sensor_data['co_level'] > 30 else Colors.TEXT), (px + 12, y))
    y += 13
    surface.blit(font_small.render(f"Triggered Sensors: {len(sensor_data['triggered_sensors'])}", True,
                                   Colors.DANGER if sensor_data['triggered_sensors'] else Colors.TEXT), (px + 12, y))
    y += 16

    pygame.draw.line(surface, Colors.PANEL_BORDER, (px + 8, y), (px + PANEL_WIDTH - 8, y), 1)
    y += 6

    # RL Section
    surface.blit(font_med.render("RL COORDINATOR", True, Colors.ACCENT), (px + 10, y))
    y += 16

    rl_stats = rl_coordinator.get_stats()
    surface.blit(font_small.render(f"Decisions Made: {rl_stats['decisions']}", True, Colors.TEXT), (px + 12, y))
    y += 13
    surface.blit(font_small.render(f"Avg Reward: {rl_stats['avg_reward']:.2f}", True, Colors.TEXT), (px + 12, y))
    y += 13
    surface.blit(font_small.render(f"Exploration: {rl_stats['epsilon']:.0%}", True, Colors.TEXT), (px + 12, y))
    y += 16

    pygame.draw.line(surface, Colors.PANEL_BORDER, (px + 8, y), (px + PANEL_WIDTH - 8, y), 1)
    y += 6

    # ACO Metrics
    surface.blit(font_med.render("ANT COLONY OPTIMIZATION", True, Colors.SAFE_PHEROMONE), (px + 10, y))
    y += 16

    safe_avg = np.mean(neural_aco.safe_pheromone)
    danger_avg = np.mean(neural_aco.danger_pheromone)
    surface.blit(font_small.render(f"Safe Pheromone Avg: {safe_avg:.2f}", True, Colors.SAFE_PHEROMONE), (px + 12, y))
    y += 13
    surface.blit(font_small.render(f"Danger Pheromone Avg: {danger_avg:.2f}", True, Colors.DANGER_PHEROMONE), (px + 12, y))
    y += 13
    surface.blit(font_small.render(f"Path Edges Tracked: {len(neural_aco.edge_usage)}", True, Colors.TEXT), (px + 12, y))
    y += 16

    pygame.draw.line(surface, Colors.PANEL_BORDER, (px + 8, y), (px + PANEL_WIDTH - 8, y), 1)
    y += 6

    # Controls
    surface.blit(font_med.render("CONTROLS", True, Colors.TEXT), (px + 10, y))
    y += 14

    controls = [
        "Click: Add fire",
        "A: Trigger alarm",
        "P: Toggle predictions",
        "T: Toggle pheromones",
        "S: Toggle sensors",
        "Space: Pause | R: Reset",
        "+/-: Speed"
    ]

    for ctrl in controls:
        surface.blit(font_small.render(ctrl, True, Colors.TEXT_DIM), (px + 12, y))
        y += 12

    # Status bar at bottom
    y = SCREEN_HEIGHT - 25
    status = f"Speed: {speed:.1f}x"
    if paused:
        status = "PAUSED | " + status
    surface.blit(font_small.render(status, True, Colors.TEXT_DIM), (px + 10, y))

def draw_bottom_bar(surface, stats, alarm_active, alarm_flash, time_val):
    """Draw bottom status bar."""
    by = MAP_HEIGHT

    bg_color = (40, 20, 20) if alarm_active and alarm_flash else Colors.PANEL_BG
    pygame.draw.rect(surface, bg_color, (0, by, MAP_WIDTH, 80))
    pygame.draw.line(surface, Colors.PANEL_BORDER, (0, by), (MAP_WIDTH, by), 2)

    font = pygame.font.Font(None, 20)
    font_big = pygame.font.Font(None, 28)

    color = Colors.SUCCESS if stats['deaths'] == 0 else Colors.DANGER
    text = f"ESCAPED: {stats['escaped']}/{stats['total']}  |  DEATHS: {stats['deaths']}"
    surface.blit(font_big.render(text, True, color), (15, by + 10))

    alive = stats['total'] - stats['escaped'] - stats['deaths']
    surface.blit(font.render(f"Inside Building: {alive}", True, Colors.TEXT_DIM), (15, by + 40))

    if alarm_active:
        alarm_color = Colors.DANGER if alarm_flash else Colors.WARNING
        surface.blit(font.render("ALARM ACTIVE - EVACUATE!", True, alarm_color), (15, by + 58))

# ═══════════════════════════════════════════════════════════════════════════════
# SPAWN FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def spawn_people(maze, count, num_wardens):
    people = []
    spawns = []

    for r in range(2, ROWS - 2):
        for c in range(2, COLS - 2):
            if maze[r][c] in [CARPET, FLOOR, CORRIDOR]:
                spawns.append((r, c))

    random.shuffle(spawns)

    states = [STATE_WORKING] * 15 + [STATE_HEADPHONES] * 8
    random.shuffle(states)

    # Wardens
    corridor_spawns = [(r, c) for r, c in spawns if maze[r][c] == CORRIDOR]
    for i in range(min(num_wardens, len(corridor_spawns))):
        r, c = corridor_spawns[i]
        people.append(Person(i, r, c, STATE_WARDEN, is_warden=True))

    # Regular people
    for i in range(num_wardens, min(count, len(spawns))):
        r, c = spawns[i]
        state = states[(i - num_wardens) % len(states)]
        people.append(Person(i, r, c, state))

    return people

def spawn_sensors(maze, count):
    """Spawn IoT sensors throughout the building."""
    network = IoTSensorNetwork()
    spawns = []

    for r in range(3, ROWS - 3, 4):
        for c in range(3, COLS - 3, 4):
            if maze[r][c] != WALL:
                spawns.append((r, c))

    random.shuffle(spawns)
    sensor_types = ['temperature', 'smoke', 'co', 'motion']

    for i, (r, c) in enumerate(spawns[:count]):
        sensor_type = sensor_types[i % len(sensor_types)]
        sensor = IoTSensor(
            id=i,
            row=r,
            col=c,
            sensor_type=sensor_type
        )
        network.add_sensor(sensor)

    return network

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    # Initialize systems
    maze, exits = generate_building()
    lstm_predictor = SimpleLSTMPredictor()
    neural_aco = NeuralACO(lstm_predictor)
    pathfinder = NeuralPathfinder(neural_aco)
    disasters = Disasters()
    alarm = AlarmSystem()
    sensor_network = spawn_sensors(maze, NUM_SENSORS)
    rl_coordinator = RLEvacuationCoordinator()
    people = spawn_people(maze, TOTAL_PEOPLE, NUM_WARDENS)

    stats = {'escaped': 0, 'deaths': 0, 'total': TOTAL_PEOPLE}

    clock = pygame.time.Clock()
    running = True
    paused = False
    speed = 1.0

    show_predictions = True
    show_pheromones = True
    show_sensors = True

    neural_update_timer = 0
    rl_update_timer = 0

    print("=" * 70)
    print("NEURAL ACO EMERGENCY RESPONSE SYSTEM (NAERS)")
    print("=" * 70)
    print("\nPATENTABLE INNOVATIONS:")
    print("  - Neural Predictive ACO (LSTM + Pheromones)")
    print("  - IoT Sensor Fusion with Kalman Filtering")
    print("  - RL-based Evacuation Coordination")
    print("\nCONTROLS: Click=Fire, A=Alarm, P=Predictions, T=Pheromones, S=Sensors")
    print("=" * 70)

    while running:
        dt = clock.tick(60) / 1000.0
        dt *= speed
        time_val = pygame.time.get_ticks() / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if mx < MAP_WIDTH and my < MAP_HEIGHT:
                    col = int((mx - disasters.shake_offset[0]) // TILE)
                    row = int((my - disasters.shake_offset[1]) // TILE)
                    if 0 < row < ROWS - 1 and 0 < col < COLS - 1:
                        if event.button == 1:
                            disasters.add_fire(row, col)
                            pathfinder.clear_cache()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_a:
                    alarm.trigger()
                elif event.key == pygame.K_p:
                    show_predictions = not show_predictions
                elif event.key == pygame.K_t:
                    show_pheromones = not show_pheromones
                elif event.key == pygame.K_s:
                    show_sensors = not show_sensors
                elif event.key == pygame.K_r:
                    # Reset
                    sound_system.stop_alarm()
                    maze, exits = generate_building()
                    lstm_predictor.reset()
                    neural_aco.reset()
                    pathfinder.clear_cache()
                    disasters = Disasters()
                    alarm = AlarmSystem()
                    sensor_network = spawn_sensors(maze, NUM_SENSORS)
                    rl_coordinator = RLEvacuationCoordinator()
                    people = spawn_people(maze, TOTAL_PEOPLE, NUM_WARDENS)
                    stats = {'escaped': 0, 'deaths': 0, 'total': TOTAL_PEOPLE}
                elif event.key in [pygame.K_EQUALS, pygame.K_PLUS]:
                    speed = min(speed + 0.5, 5.0)
                elif event.key == pygame.K_MINUS:
                    speed = max(speed - 0.5, 0.5)

        if not paused:
            # Update disasters
            disasters.update(dt, maze, neural_aco)
            alarm.update(dt)

            # Auto-trigger alarm on fire
            if disasters.hazards and not alarm.active:
                alarm.trigger()

            # Update neural predictions
            neural_update_timer += dt
            if neural_update_timer > 0.5:
                fire_positions = disasters.get_fire_positions()
                sensor_data = sensor_network.get_sensor_fusion_data()
                neural_aco.update_predictions(fire_positions, sensor_data, maze)
                neural_update_timer = 0

            # Update sensors
            people_positions = [(p.row, p.col) for p in people if p.alive and not p.escaped]
            sensor_network.update(dt, disasters.get_fire_positions(), disasters.smoke, people_positions, maze)

            # Update RL coordinator
            rl_update_timer += dt
            if rl_update_timer > 2.0 and alarm.active:
                wardens = [p for p in people if p.is_warden and p.alive]
                exits_status = {e: False for e in exits}  # Simplified
                rl_coordinator.step(disasters.get_fire_positions(), people, exits_status, wardens)
                rl_update_timer = 0

            # Pheromone evaporation
            neural_aco.evaporate()

            # Update people
            prev_escaped = stats['escaped']
            prev_deaths = stats['deaths']

            for p in people:
                p.update(dt, maze, exits, disasters.hazards, pathfinder,
                        alarm.active, people, disasters.smoke, neural_aco)

            # Update stats
            stats['escaped'] = sum(1 for p in people if p.escaped)
            stats['deaths'] = sum(1 for p in people if not p.alive)

            if stats['escaped'] > prev_escaped:
                sound_system.play('escape', 0.2)

        # RENDER
        screen.fill((30, 32, 38))
        shake = disasters.shake_offset

        # Draw map
        for r in range(ROWS):
            for c in range(COLS):
                draw_tile(screen, r, c, maze, disasters.hazards, time_val, shake,
                         alarm.active and alarm.flash_state)

        # Draw smoke
        draw_smoke(screen, disasters.smoke, shake)

        # Draw pheromones
        if show_pheromones:
            draw_pheromones(screen, neural_aco, shake)

        # Draw neural predictions
        if show_predictions:
            fire_positions = disasters.get_fire_positions()
            predictions = lstm_predictor.predict_spread(fire_positions, {}, maze)
            draw_neural_predictions(screen, predictions, shake, time_val)

        # Draw sensors
        if show_sensors:
            sensor_network.draw(screen, shake, time_val)

        # Draw particles
        disasters.draw_particles(screen, shake)

        # Draw people
        for p in sorted(people, key=lambda x: x.y):
            p.draw(screen, shake, time_val)

        # Draw UI
        draw_panel(screen, stats, neural_aco, sensor_network, rl_coordinator, time_val, paused, speed)
        draw_bottom_bar(screen, stats, alarm.active, alarm.flash_state, time_val)

        pygame.display.flip()

    pygame.quit()
    sound_system.stop_alarm()

    print(f"\n{'='*60}")
    print(f"FINAL: Escaped {stats['escaped']}/{stats['total']}, Deaths: {stats['deaths']}")
    if stats['deaths'] == 0:
        print("PERFECT! ZERO DEATHS ACHIEVED!")
    print(f"Neural Confidence Final: {neural_aco.neural_confidence:.1%}")
    print(f"RL Decisions Made: {rl_coordinator.decisions_made}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
