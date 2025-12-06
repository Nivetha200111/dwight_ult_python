# """
# ╔══════════════════════════════════════════════════════════════════════════════════════════════╗
# ║                                                                                              ║
# ║          💡 DWIGHT V13 - FIXED POV & OPTICS UPDATE 💡                                        ║
# ║                                                                                              ║
# ║  FIXES:                                                                                      ║
# ║  ✓ FIXED BLACK SCREEN: Rewrote the lighting engine to use proper RGB Multiplication masks.   ║
# ║  ✓ VISIBLE ENVIRONMENT: You can now see the floor/walls through the person's eyes.           ║
# ║  ✓ ESCAPED VIEW: Camera stays with people who escape so you can see the Safe Zone.           ║
# ║                                                                                              ║
# ║  CONTROLS:                                                                                   ║
# ║  [WASD] Pan Camera  |  [Scroll] Zoom                                                         ║
# ║  [Left Click] Follow Person (POV)  |  [Space] Release Camera                                 ║
# ║  [B] Bomb  |  [E] Quake  |  [F] Fire                                                         ║
# ║                                                                                              ║
# ╚══════════════════════════════════════════════════════════════════════════════════════════════╝
# """

# import pygame
# import random
# import math
# from heapq import heappush, heappop

# pygame.init()

# # ═══════════════════════════════════════════════════════════════════════════════
# # CONFIGURATION
# # ═══════════════════════════════════════════════════════════════════════════════

# ROWS = 40
# COLS = 50
# TOTAL_PEOPLE = 60

# BASE_TILE_W = 32
# BASE_TILE_H = 16

# SCREEN_WIDTH = 1200
# SCREEN_HEIGHT = 800

# screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
# pygame.display.set_caption("💡 DWIGHT V13 - Fixed POV Lighting")

# # ═══════════════════════════════════════════════════════════════════════════════
# # COLORS
# # ═══════════════════════════════════════════════════════════════════════════════

# class Colors:
#     FLOOR = (140, 140, 150)
#     WALL_TOP = (70, 70, 80)
#     WALL_SIDE = (50, 50, 60)
#     RUBBLE = (60, 55, 50)
#     EXIT = (50, 255, 100)
#     FIRE = (255, 120, 0)
    
#     SKINS = [(255, 220, 177), (180, 138, 120), (141, 85, 36)]
#     SHIRTS = [(100, 100, 200), (200, 100, 100), (100, 200, 100), (200, 200, 100)]

# # Tile Types
# FLOOR = 0
# WALL = 1
# EXIT = 2
# RUBBLE = 3

# # ═══════════════════════════════════════════════════════════════════════════════
# # CAMERA
# # ═══════════════════════════════════════════════════════════════════════════════

# class Camera:
#     def __init__(self):
#         self.x = 0
#         self.y = 0
#         self.zoom = 1.0
#         self.target = None 
#         self.shake = 0
        
#         self.tile_w = BASE_TILE_W
#         self.tile_h = BASE_TILE_H
#         self.center_on_map()

#     def center_on_map(self):
#         self.x = (COLS * self.tile_w) // 2 - SCREEN_WIDTH // 2
#         self.y = -100

#     def apply_zoom(self, amount):
#         old_zoom = self.zoom
#         self.zoom += amount
#         self.zoom = max(0.5, min(self.zoom, 2.5))
#         self.tile_w = int(BASE_TILE_W * self.zoom)
#         self.tile_h = int(BASE_TILE_H * self.zoom)
#         if self.zoom != old_zoom:
#             self.x = int(self.x * (self.zoom / old_zoom))
#             self.y = int(self.y * (self.zoom / old_zoom))

#     def move(self, dx, dy):
#         self.target = None 
#         self.x += dx
#         self.y += dy

#     def update(self):
#         if self.shake > 0:
#             self.x += random.randint(-self.shake, self.shake)
#             self.y += random.randint(-self.shake, self.shake)
#             self.shake = int(self.shake * 0.9)

#         if self.target:
#             tx, ty = self.get_iso_coords(self.target.exact_r, self.target.exact_c)
#             desired_x = tx - SCREEN_WIDTH // 2
#             desired_y = ty - SCREEN_HEIGHT // 2
#             self.x += (desired_x - self.x) * 0.1
#             self.y += (desired_y - self.y) * 0.1

#     def get_iso_coords(self, r, c):
#         iso_x = (c - r) * (self.tile_w // 2)
#         iso_y = (c + r) * (self.tile_h // 2)
#         return iso_x, iso_y

#     def to_screen(self, r, c, z=0):
#         iso_x, iso_y = self.get_iso_coords(r, c)
#         return int(iso_x - self.x), int(iso_y - self.y - z*self.zoom)

# camera = Camera()

# # ═══════════════════════════════════════════════════════════════════════════════
# # PATHFINDING
# # ═══════════════════════════════════════════════════════════════════════════════

# class Pathfinder:
#     def find_path(self, start, goal, maze, hazards):
#         rows, cols = len(maze), len(maze[0])
#         open_set = []
#         heappush(open_set, (0, 0, start))
#         came_from = {}
#         g_score = {start: 0}
        
#         while open_set:
#             _, _, current = heappop(open_set)
#             if current == goal:
#                 path = []
#                 while current in came_from:
#                     path.append(current)
#                     current = came_from[current]
#                 path.reverse()
#                 return path
            
#             r, c = current
#             for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
#                 nr, nc = r + dr, c + dc
#                 if 0 <= nr < rows and 0 <= nc < cols:
#                     if maze[nr][nc] != WALL:
#                         neighbor = (nr, nc)
#                         cost = 1 
#                         if maze[nr][nc] == RUBBLE: cost = 8 
#                         if neighbor in hazards: cost += 50
                        
#                         tentative = g_score[current] + cost
#                         if neighbor not in g_score or tentative < g_score[neighbor]:
#                             came_from[neighbor] = current
#                             g_score[neighbor] = tentative
#                             h = abs(nr - goal[0]) + abs(nc - goal[1])
#                             heappush(open_set, (tentative + h, tentative, neighbor))
#         return []

# pathfinder = Pathfinder()

# # ═══════════════════════════════════════════════════════════════════════════════
# # PERSON AGENT
# # ═══════════════════════════════════════════════════════════════════════════════

# class Person:
#     def __init__(self, pid, r, c):
#         self.id = pid
#         self.r, self.c = r, c
#         self.exact_r, self.exact_c = float(r), float(c)
#         self.color_skin = random.choice(Colors.SKINS)
#         self.color_shirt = random.choice(Colors.SHIRTS)
        
#         self.alive = True
#         self.escaped = False
#         self.health = 100
#         self.injured = False
#         self.stun_timer = 0
        
#         self.path = []
#         self.path_index = 0
#         self.anim_offset = random.random() * 6.28
#         self.thought = "Working..."
#         self.thought_timer = 0
#         self.state = "IDLE" 

#     def set_thought(self, text):
#         if self.thought != text:
#             self.thought = text
#             self.thought_timer = 2.0

#     def update(self, dt, maze, hazards):
#         if not self.alive: return
#         # Keep updating even if escaped so we can see them

#         self.thought_timer -= dt
        
#         # Damage
#         if not self.escaped:
#             if (self.r, self.c) in hazards:
#                 self.health -= 40 * dt
#                 self.set_thought("I'M BURNING!")
#                 self.state = "PANIC"
            
#             if self.stun_timer > 0:
#                 self.stun_timer -= dt
#                 self.set_thought("Can't hear...")
#                 return

#         if self.health < 50: 
#             self.injured = True
#             if self.state != "PANIC": self.set_thought("Hurts to walk...")

#         if self.health <= 0:
#             self.alive = False
#             self.set_thought("...")
#             return

#         if maze[self.r][self.c] == EXIT:
#             if not self.escaped:
#                 self.escaped = True
#                 self.set_thought("Made it!")
#             return

#         # Pathfinding
#         if not self.path or random.random() < 0.05:
#             self.find_exit(maze, hazards)
#             if not self.path: 
#                 self.set_thought("TRAPPED!")
#                 self.state = "PANIC"
#             else:
#                 if self.state == "IDLE": 
#                     self.set_thought("Exit found.")
#                     self.state = "MOVING"

#         # Move
#         if self.path and self.path_index < len(self.path):
#             nr, nc = self.path[self.path_index]
            
#             speed = 4.0 
#             if self.injured: speed = 1.5
#             if maze[self.r][self.c] == RUBBLE:
#                 speed *= 0.3
#                 self.set_thought("Ugh, debris...")
            
#             dr, dc = nr - self.exact_r, nc - self.exact_c
#             dist = math.hypot(dr, dc)
            
#             if dist > 0:
#                 move = min(dist, speed * dt)
#                 self.exact_r += (dr/dist) * move
#                 self.exact_c += (dc/dist) * move
                
#                 cur_r, cur_c = int(round(self.exact_r)), int(round(self.exact_c))
#                 if maze[cur_r][cur_c] == WALL:
#                     self.path = [] 
#                 else:
#                     self.r, self.c = cur_r, cur_c
#                     if dist < 0.1: self.path_index += 1

#     def find_exit(self, maze, hazards):
#         best = None
#         min_d = 999
#         for r in range(ROWS):
#             for c in range(COLS):
#                 if maze[r][c] == EXIT:
#                     d = abs(self.r - r) + abs(self.c - c)
#                     if d < min_d:
#                         min_d = d
#                         best = (r,c)
#         if best:
#             self.path = pathfinder.find_path((self.r, self.c), best, maze, hazards)
#             self.path_index = 0

# # ═══════════════════════════════════════════════════════════════════════════════
# # DRAWING
# # ═══════════════════════════════════════════════════════════════════════════════

# def draw_iso_tile(surface, r, c, tile):
#     sx, sy = camera.to_screen(r, c)
#     if sx < -100 or sx > SCREEN_WIDTH+100 or sy < -100 or sy > SCREEN_HEIGHT+100: return

#     w = camera.tile_w
#     h_tile = camera.tile_h
#     col = Colors.FLOOR
#     z = 0
    
#     if tile == WALL:
#         col = Colors.WALL_TOP
#         z = int(24 * camera.zoom)
#     elif tile == RUBBLE:
#         col = Colors.RUBBLE
#         z = int(6 * camera.zoom)
#     elif tile == EXIT:
#         col = Colors.EXIT
    
#     top = (sx, sy - z)
#     right = (sx + w//2, sy + h_tile//2 - z)
#     bottom = (sx, sy + h_tile - z)
#     left = (sx - w//2, sy + h_tile//2 - z)
    
#     pygame.draw.polygon(surface, col, [top, right, bottom, left])
#     if z > 0:
#         pygame.draw.polygon(surface, [c*0.6 for c in col], [right, bottom, (bottom[0], bottom[1]+z), (right[0], right[1]+z)])
#         pygame.draw.polygon(surface, [c*0.8 for c in col], [left, bottom, (bottom[0], bottom[1]+z), (left[0], left[1]+z)])

# def draw_person(surface, p, time_val):
#     sx, sy = camera.to_screen(p.exact_r, p.exact_c)
#     if sx < -50 or sx > SCREEN_WIDTH+50 or sy < -50 or sy > SCREEN_HEIGHT+50: return
    
#     zoom = camera.zoom
#     if not p.alive:
#         pygame.draw.rect(surface, p.color_shirt, (sx - 8*zoom, sy - 2*zoom, 16*zoom, 4*zoom))
#         return

#     bob = 0
#     if p.state == "MOVING": bob = math.sin(time_val * 10 + p.anim_offset) * 2 * zoom
    
#     h = 16 * zoom
#     w = 8 * zoom
    
#     # Legs
#     pygame.draw.line(surface, (50,50,50), (sx-2*zoom, sy), (sx-2*zoom, sy-h//2), int(2*zoom))
#     pygame.draw.line(surface, (50,50,50), (sx+2*zoom, sy), (sx+2*zoom, sy-h//2), int(2*zoom))
    
#     # Body
#     pygame.draw.rect(surface, p.color_shirt, (sx - w//2, sy - h + bob, w, h//1.5))
    
#     # Head
#     head_y = sy - h + bob - 4*zoom
#     pygame.draw.circle(surface, p.color_skin, (sx, head_y), int(4*zoom))
    
#     if p.stun_timer > 0:
#          pygame.draw.circle(surface, (255, 255, 0), (sx, head_y - 8*zoom), int(2*zoom))
    
#     if camera.target == p:
#         arrow_y = head_y - 15*zoom + math.sin(time_val*5)*5
#         pygame.draw.polygon(surface, (255, 255, 0), [(sx, arrow_y + 10*zoom), (sx - 5*zoom, arrow_y), (sx + 5*zoom, arrow_y)])

# # ═══════════════════════════════════════════════════════════════════════════════
# # MAIN LOOP
# # ═══════════════════════════════════════════════════════════════════════════════

# def main():
#     clock = pygame.time.Clock()
    
#     maze = [[FLOOR for _ in range(COLS)] for _ in range(ROWS)]
#     for r in range(ROWS): maze[r][0] = maze[r][COLS-1] = WALL
#     for c in range(COLS): maze[0][c] = maze[ROWS-1][c] = WALL
    
#     for r in range(5, ROWS-5, 8):
#         for c in range(5, COLS-5, 8):
#              maze[r][c] = WALL
#              maze[r+1][c] = WALL
#              maze[r][c+1] = WALL
            
#     maze[ROWS//2][0] = EXIT
#     maze[ROWS//2][COLS-1] = EXIT

#     people = []
#     for i in range(TOTAL_PEOPLE):
#         r, c = random.randint(2, ROWS-2), random.randint(2, COLS-2)
#         while maze[r][c] == WALL: r, c = random.randint(2, ROWS-2), random.randint(2, COLS-2)
#         people.append(Person(i, r, c))
        
#     hazards = {}
#     running = True
    
#     while running:
#         dt = clock.tick(30) / 1000.0
#         time_val = pygame.time.get_ticks() / 1000.0
        
#         for event in pygame.event.get():
#             if event.type == pygame.QUIT: running = False
#             elif event.type == pygame.MOUSEWHEEL:
#                 camera.apply_zoom(event.y * 0.1)
#             elif event.type == pygame.MOUSEBUTTONDOWN:
#                 if event.button == 1:
#                     mx, my = event.pos
#                     best_dist = 40 * camera.zoom
#                     selected = None
#                     for p in people:
#                         # Allow selecting anyone, alive or escaped
#                         px, py = camera.to_screen(p.exact_r, p.exact_c)
#                         d = math.hypot(px - mx, py - my)
#                         if d < best_dist:
#                             best_dist = d
#                             selected = p
#                     if selected: camera.target = selected
#                 elif event.button == 3:
#                     camera.target = None
            
#             elif event.type == pygame.KEYDOWN:
#                 if event.key == pygame.K_b:
#                     camera.shake = 15
#                     for _ in range(4):
#                         ir, ic = random.randint(2, ROWS-2), random.randint(2, COLS-2)
#                         maze[ir][ic] = RUBBLE
#                         for dr in range(-1, 2):
#                             for dc in range(-1, 2):
#                                 if 0<=ir+dr<ROWS and 0<=ic+dc<COLS:
#                                     if random.random() < 0.8: maze[ir+dr][ic+dc] = RUBBLE
#                         for p in people:
#                              if abs(p.r - ir) + abs(p.c - ic) < 6:
#                                  p.stun_timer = 3.0
#                                  p.set_thought("EARS RINGING!")
#                         if random.random() < 0.5: hazards[(ir, ic)] = 20.0
#                 elif event.key == pygame.K_e:
#                     camera.shake = 25
#                     for _ in range(60):
#                         rx, ry = random.randint(2, ROWS-2), random.randint(2, COLS-2)
#                         if maze[rx][ry] == FLOOR: maze[rx][ry] = RUBBLE
#                 elif event.key == pygame.K_f:
#                     for _ in range(10):
#                         fx, fy = random.randint(2, ROWS-2), random.randint(2, COLS-2)
#                         if maze[fx][fy] != WALL: hazards[(fx, fy)] = 25.0
#                 elif event.key == pygame.K_r: return main()
#                 elif event.key == pygame.K_SPACE: camera.target = None

#         keys = pygame.key.get_pressed()
#         s = 15
#         if keys[pygame.K_LEFT] or keys[pygame.K_a]: camera.move(-s, 0)
#         if keys[pygame.K_RIGHT] or keys[pygame.K_d]: camera.move(s, 0)
#         if keys[pygame.K_UP] or keys[pygame.K_w]: camera.move(0, -s)
#         if keys[pygame.K_DOWN] or keys[pygame.K_s]: camera.move(0, s)

#         camera.update()
        
#         del_list = []
#         for h in hazards:
#             hazards[h] -= dt
#             if hazards[h] <= 0: del_list.append(h)
#         for h in del_list: del hazards[h]
        
#         if random.random() < 0.1:
#             keys_list = list(hazards.keys())
#             if keys_list:
#                 src = random.choice(keys_list)
#                 nr, nc = src[0] + random.randint(-1,1), src[1] + random.randint(-1,1)
#                 if 0<=nr<ROWS and 0<=nc<COLS and maze[nr][nc] != WALL and (nr,nc) not in hazards:
#                     hazards[(nr,nc)] = 10.0

#         for p in people: p.update(dt, maze, hazards)

#         screen.fill((20, 20, 25))
        
#         for r in range(ROWS):
#             for c in range(COLS):
#                 draw_iso_tile(screen, r, c, maze[r][c])
        
#         for r, c in hazards:
#             sx, sy = camera.to_screen(r, c)
#             pygame.draw.circle(screen, Colors.FIRE, (sx, sy - int(10*camera.zoom)), int(6*camera.zoom))

#         people.sort(key=lambda p: p.exact_r + p.exact_c)
#         for p in people:
#             draw_person(screen, p, time_val)

#         # --- LIGHTING SYSTEM (THE FIX) ---
#         if camera.target:
#             # 1. Create a Light Mask (Dark Grey)
#             light_mask = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
#             light_mask.fill((30, 30, 30)) # Ambient Darkness
            
#             # 2. Draw Vision Circle (White = Visible)
#             tx, ty = camera.to_screen(camera.target.exact_r, camera.target.exact_c)
#             pygame.draw.circle(light_mask, (255, 255, 255), (tx, ty - 20), int(200 * camera.zoom))
            
#             # 3. Multiply Mask with Screen (White reveals, Grey dims)
#             screen.blit(light_mask, (0, 0), special_flags=pygame.BLEND_MULT)
            
#             # 4. Thought Bubble (On top of darkness)
#             pygame.draw.rect(screen, (255,255,255), (tx+30, ty-90, 180, 50), border_radius=8)
#             pygame.draw.polygon(screen, (255,255,255), [(tx+30, ty-50), (tx+20, ty-30), (tx+50, ty-50)])
#             font_sm = pygame.font.Font(None, 24)
#             screen.blit(font_sm.render(camera.target.thought, True, (0,0,0)), (tx+40, ty-75))

#         pygame.draw.rect(screen, (0,0,0), (0,0, SCREEN_WIDTH, 40))
#         font = pygame.font.Font(None, 28)
#         status = f"Alive: {sum(1 for p in people if p.alive)} | Escaped: {sum(1 for p in people if p.escaped)}"
#         screen.blit(font.render(status, True, (255,255,255)), (10, 10))
        
#         help_txt = "[B] Bomb  [E] Quake  [F] Fire  |  Click Person for POV"
#         screen.blit(font.render(help_txt, True, (180, 180, 180)), (SCREEN_WIDTH - 450, 10))

#         pygame.display.flip()

# if __name__ == "__main__":
#     main()
#     pygame.quit()

"""
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                              ║
║     ██████╗ ██╗    ██╗██╗ ██████╗ ██╗  ██╗████████╗    ██╗   ██╗ █████╗                      ║
║     ██╔══██╗██║    ██║██║██╔════╝ ██║  ██║╚══██╔══╝    ██║   ██║██╔══██╗                     ║
║     ██║  ██║██║ █╗ ██║██║██║  ███╗███████║   ██║       ██║   ██║╚█████╔╝                     ║
║     ██║  ██║██║███╗██║██║██║   ██║██╔══██║   ██║       ╚██╗ ██╔╝██╔══██╗                     ║
║     ██████╔╝╚███╔███╔╝██║╚██████╔╝██║  ██║   ██║        ╚████╔╝ ╚█████╔╝                     ║
║     ╚═════╝  ╚══╝╚══╝ ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝         ╚═══╝   ╚════╝                      ║
║                                                                                              ║
║              🛡️ ZERO DEATH PREVENTION SYSTEMS 🛡️                                             ║
║                                                                                              ║
║  SAFETY SYSTEMS:                                                                             ║
║  📱 Buddy Phone System - Auto-alerts headphone users via phone vibration                    ║
║  🧯 Sprinklers - Auto-activate near fire, slow spread                                       ║
║  🚨 Smoke Detectors - Early alarm trigger                                                   ║
║  👷 Floor Wardens - Check rooms, physically alert everyone                                  ║
║  🤝 Buddy Check - Colleagues check on each other                                            ║
║  💡 Emergency Lights - Flashing path to exits                                               ║
║  🔊 Sound System - Alarm, phone alerts, sprinkler sounds                                    ║
║                                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝
"""

import pygame
import pygame.mixer
import random
import math
from collections import defaultdict
from heapq import heappush, heappop
import numpy as np

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# ═══════════════════════════════════════════════════════════════════════════════
# SOUND SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class SoundSystem:
    def __init__(self):
        self.sounds = {}
        self.alarm_playing = False
        self.generate_sounds()
    
    def generate_sounds(self):
        """Generate sound effects programmatically."""
        sample_rate = 22050
        
        # Alarm sound (alternating tones)
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        tone1 = np.sin(2 * np.pi * 800 * t) * 0.3
        tone2 = np.sin(2 * np.pi * 600 * t) * 0.3
        alarm_wave = np.concatenate([tone1, tone2, tone1, tone2])
        alarm_wave = (alarm_wave * 32767).astype(np.int16)
        alarm_stereo = np.column_stack((alarm_wave, alarm_wave))
        self.sounds['alarm'] = pygame.sndarray.make_sound(alarm_stereo)
        
        # Phone vibration/buzz
        duration = 0.2
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        buzz = np.sin(2 * np.pi * 150 * t) * np.sin(2 * np.pi * 30 * t) * 0.4
        buzz = (buzz * 32767).astype(np.int16)
        buzz_stereo = np.column_stack((buzz, buzz))
        self.sounds['phone_buzz'] = pygame.sndarray.make_sound(buzz_stereo)
        
        # Sprinkler hiss
        duration = 0.3
        noise = np.random.uniform(-0.15, 0.15, int(sample_rate * duration))
        noise = (noise * 32767).astype(np.int16)
        noise_stereo = np.column_stack((noise, noise))
        self.sounds['sprinkler'] = pygame.sndarray.make_sound(noise_stereo)
        
        # Fire crackle
        duration = 0.4
        crackle = np.random.uniform(-0.2, 0.2, int(sample_rate * duration))
        crackle = crackle * np.sin(np.linspace(0, 10, len(crackle)))
        crackle = (crackle * 32767).astype(np.int16)
        crackle_stereo = np.column_stack((crackle, crackle))
        self.sounds['fire'] = pygame.sndarray.make_sound(crackle_stereo)
        
        # Success chime
        duration = 0.3
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        chime = np.sin(2 * np.pi * 880 * t) * np.exp(-t * 5) * 0.3
        chime = (chime * 32767).astype(np.int16)
        chime_stereo = np.column_stack((chime, chime))
        self.sounds['escape'] = pygame.sndarray.make_sound(chime_stereo)
        
        # Warning beep
        duration = 0.15
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        beep = np.sin(2 * np.pi * 1000 * t) * 0.25
        beep = (beep * 32767).astype(np.int16)
        beep_stereo = np.column_stack((beep, beep))
        self.sounds['beep'] = pygame.sndarray.make_sound(beep_stereo)
        
        # Scream/panic
        duration = 0.4
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        scream = np.sin(2 * np.pi * (400 + 200 * np.sin(t * 20)) * t) * 0.2
        scream = (scream * 32767).astype(np.int16)
        scream_stereo = np.column_stack((scream, scream))
        self.sounds['panic'] = pygame.sndarray.make_sound(scream_stereo)
    
    def play(self, sound_name, volume=0.5):
        if sound_name in self.sounds:
            self.sounds[sound_name].set_volume(volume)
            self.sounds[sound_name].play()
    
    def start_alarm(self):
        if not self.alarm_playing:
            self.sounds['alarm'].play(-1)  # Loop
            self.alarm_playing = True
    
    def stop_alarm(self):
        if self.alarm_playing:
            self.sounds['alarm'].stop()
            self.alarm_playing = False

sound_system = SoundSystem()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

ROWS = 45
COLS = 70
TILE = 16
TOTAL_PEOPLE = 50
NUM_WARDENS = 3

MAP_WIDTH = COLS * TILE
MAP_HEIGHT = ROWS * TILE
PANEL_WIDTH = 320
SCREEN_WIDTH = MAP_WIDTH + PANEL_WIDTH
SCREEN_HEIGHT = MAP_HEIGHT + 60

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("🛡️ DWIGHT V8 - Zero Death Prevention Systems")

# ═══════════════════════════════════════════════════════════════════════════════
# COLORS
# ═══════════════════════════════════════════════════════════════════════════════

class Colors:
    FLOOR = (195, 190, 180)
    FLOOR_DARK = (175, 170, 160)
    WALL = (55, 55, 65)
    CORRIDOR = (165, 160, 155)
    CARPET = (105, 70, 70)
    
    EXIT = (50, 255, 50)
    DOOR = (135, 85, 45)
    
    FIRE = (255, 110, 30)
    FIRE_BRIGHT = (255, 230, 60)
    SMOKE = (75, 75, 75)
    WATER = (50, 135, 225)
    SPRINKLER_WATER = (100, 180, 255)
    
    SAFE_PATH = (0, 255, 130)
    DANGER = (255, 70, 70)
    PREDICTED = (255, 60, 200)
    
    # States
    WORKING = (100, 150, 255)
    HEADPHONES = (255, 100, 255)
    PHONE_ALERT = (255, 50, 150)
    MEETING = (255, 200, 100)
    AWARE = (255, 255, 100)
    EVACUATING = (100, 255, 100)
    PANICKING = (255, 80, 80)
    WARDEN = (255, 215, 0)
    HELPING = (255, 150, 200)
    
    PANEL_BG = (22, 24, 32)
    PANEL_BORDER = (50, 55, 70)
    ACCENT = (0, 230, 130)
    SUCCESS = (60, 255, 110)
    DANGER_TEXT = (255, 80, 80)
    WARNING = (255, 220, 60)
    TEXT_WHITE = (255, 255, 255)
    TEXT_GRAY = (175, 175, 185)
    ALARM_RED = (255, 50, 50)
    BUDDY_LINE = (150, 255, 150)

# Tile types
FLOOR = 0
WALL = 1
EXIT = 2
DOOR = 3
CORRIDOR = 4
CARPET = 5

# Person states
STATE_WORKING = "working"
STATE_HEADPHONES = "headphones"
STATE_MEETING = "meeting"
STATE_PHONE = "phone"
STATE_ZONED_OUT = "zoned_out"
STATE_AWARE = "aware"
STATE_EVACUATING = "evacuating"
STATE_PANICKING = "panicking"
STATE_WARDEN_SWEEP = "warden_sweep"
STATE_PHONE_ALERTED = "phone_alerted"
STATE_HELPING = "helping"

# ═══════════════════════════════════════════════════════════════════════════════
# BUDDY PHONE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class BuddyPhoneSystem:
    def __init__(self):
        self.buddy_pairs = {}  # person_id -> buddy_id
        self.alerted_phones = set()  # IDs that received phone alert
        self.phone_vibrating = {}  # person_id -> vibrate_timer
        self.alert_sent_time = {}
    
    def assign_buddies(self, people):
        """Assign each person a buddy (nearby colleague)."""
        self.buddy_pairs.clear()
        
        for person in people:
            if person.id in self.buddy_pairs:
                continue
            
            # Find nearest unassigned person
            best_buddy = None
            best_dist = float('inf')
            
            for other in people:
                if other.id != person.id and other.id not in self.buddy_pairs.values():
                    dist = abs(person.row - other.row) + abs(person.col - other.col)
                    if dist < best_dist and dist < 15:  # Within reasonable distance
                        best_dist = dist
                        best_buddy = other
            
            if best_buddy:
                self.buddy_pairs[person.id] = best_buddy.id
                self.buddy_pairs[best_buddy.id] = person.id
    
    def send_emergency_alert(self, from_person, people, alarm_active):
        """When someone becomes aware, alert their buddy via phone."""
        if not alarm_active:
            return
        
        buddy_id = self.buddy_pairs.get(from_person.id)
        if buddy_id and buddy_id not in self.alerted_phones:
            # Find buddy
            for person in people:
                if person.id == buddy_id and person.alive and not person.escaped:
                    # Send phone alert!
                    self.alerted_phones.add(buddy_id)
                    self.phone_vibrating[buddy_id] = 3.0  # Vibrate for 3 seconds
                    self.alert_sent_time[buddy_id] = 0
                    sound_system.play('phone_buzz', 0.3)
                    return True
        return False
    
    def update(self, dt, people):
        """Update phone vibrations."""
        for pid in list(self.phone_vibrating.keys()):
            self.phone_vibrating[pid] -= dt
            if self.phone_vibrating[pid] <= 0:
                del self.phone_vibrating[pid]
    
    def is_phone_vibrating(self, person_id):
        return person_id in self.phone_vibrating
    
    def draw_buddy_connections(self, surface, people, shake):
        """Draw lines between buddy pairs."""
        drawn = set()
        for p1_id, p2_id in self.buddy_pairs.items():
            if (p1_id, p2_id) in drawn or (p2_id, p1_id) in drawn:
                continue
            drawn.add((p1_id, p2_id))
            
            p1 = p2 = None
            for p in people:
                if p.id == p1_id:
                    p1 = p
                if p.id == p2_id:
                    p2 = p
            
            if p1 and p2 and p1.alive and p2.alive and not p1.escaped and not p2.escaped:
                x1 = int(p1.x + shake[0])
                y1 = int(p1.y + shake[1])
                x2 = int(p2.x + shake[0])
                y2 = int(p2.y + shake[1])
                
                # Green line if both safe, orange if one in danger
                if p1.state in [STATE_EVACUATING, STATE_AWARE] or p2.state in [STATE_EVACUATING, STATE_AWARE]:
                    color = (100, 255, 100, 80)
                else:
                    color = (100, 150, 100, 40)
                
                pygame.draw.line(surface, color[:3], (x1, y1), (x2, y2), 1)

buddy_system = BuddyPhoneSystem()

# ═══════════════════════════════════════════════════════════════════════════════
# SAFETY SYSTEMS (Sprinklers, Detectors, Emergency Lights)
# ═══════════════════════════════════════════════════════════════════════════════

class SafetySystems:
    def __init__(self):
        self.sprinklers = {}
        self.smoke_detectors = {}
        self.emergency_lights = {}
        self.sprinklers_active = False
        self.detector_triggered = False
        self.water_particles = []
        self.sprinkler_sound_timer = 0
    
    def add_sprinkler(self, row, col):
        self.sprinklers[(row, col)] = False
    
    def add_smoke_detector(self, row, col):
        self.smoke_detectors[(row, col)] = False
    
    def add_emergency_light(self, row, col, direction):
        self.emergency_lights[(row, col)] = {'dir': direction, 'active': False}
    
    def check_detectors(self, smoke_map, hazards):
        for (r, c) in self.smoke_detectors:
            if self.smoke_detectors[(r, c)]:
                continue
            for dr in range(-4, 5):
                for dc in range(-4, 5):
                    check = (r + dr, c + dc)
                    if smoke_map.get(check, 0) > 0.25 or check in hazards:
                        self.smoke_detectors[(r, c)] = True
                        self.detector_triggered = True
                        sound_system.play('beep', 0.4)
                        return True
        return False
    
    def activate_sprinklers(self, hazards):
        activated = False
        for (sr, sc) in self.sprinklers:
            if self.sprinklers[(sr, sc)]:
                continue
            for (hr, hc), info in hazards.items():
                if info['type'] == 'fire':
                    if abs(sr - hr) <= 5 and abs(sc - hc) <= 5:
                        self.sprinklers[(sr, sc)] = True
                        self.sprinklers_active = True
                        activated = True
        return activated
    
    def activate_emergency_lights(self):
        for pos in self.emergency_lights:
            self.emergency_lights[pos]['active'] = True
    
    def apply_sprinkler_effect(self, hazards, smoke_map, dt):
        fires_to_remove = []
        
        for (sr, sc), active in self.sprinklers.items():
            if active:
                # Water particles
                if random.random() < 0.4:
                    for _ in range(2):
                        self.water_particles.append({
                            'x': sc * TILE + random.randint(2, TILE - 2),
                            'y': sr * TILE + 4,
                            'vx': random.uniform(-15, 15),
                            'vy': random.uniform(50, 90),
                            'life': random.uniform(0.4, 0.8)
                        })
                
                # Sprinkler sound
                self.sprinkler_sound_timer -= dt
                if self.sprinkler_sound_timer <= 0:
                    sound_system.play('sprinkler', 0.15)
                    self.sprinkler_sound_timer = 0.5
                
                # Reduce fire and smoke in range
                for dr in range(-4, 5):
                    for dc in range(-4, 5):
                        pos = (sr + dr, sc + dc)
                        dist = abs(dr) + abs(dc)
                        
                        if pos in hazards and hazards[pos]['type'] == 'fire':
                            # Faster extinguish for closer fires
                            hazards[pos]['age'] += (5 - min(dist, 4)) * 0.3
                            if hazards[pos]['age'] > 25:
                                fires_to_remove.append(pos)
                        
                        if pos in smoke_map:
                            smoke_map[pos] *= 0.85
        
        for pos in fires_to_remove:
            if pos in hazards:
                del hazards[pos]
        
        # Update particles
        for p in self.water_particles[:]:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['life'] -= dt
            if p['life'] <= 0:
                self.water_particles.remove(p)
    
    def draw(self, surface, shake, time_val, alarm_active):
        # Sprinklers
        for (r, c), active in self.sprinklers.items():
            x = int(c * TILE + shake[0])
            y = int(r * TILE + shake[1])
            
            pygame.draw.rect(surface, (120, 120, 130), (x + TILE//2 - 2, y, 4, 4))
            
            if active:
                for i in range(4):
                    angle = math.pi/4 + i * math.pi/6 + math.sin(time_val * 8) * 0.3
                    length = 10 + math.sin(time_val * 12 + i) * 3
                    ex = x + TILE//2 + math.cos(angle) * length
                    ey = y + 4 + math.sin(angle) * length
                    pygame.draw.line(surface, Colors.SPRINKLER_WATER,
                                   (x + TILE//2, y + 4), (int(ex), int(ey)), 1)
        
        # Water particles
        for p in self.water_particles:
            pygame.draw.circle(surface, Colors.SPRINKLER_WATER,
                             (int(p['x']), int(p['y'])), 2)
        
        # Smoke detectors
        for (r, c), triggered in self.smoke_detectors.items():
            x = int(c * TILE + shake[0])
            y = int(r * TILE + shake[1])
            
            color = (255, 60, 60) if triggered else (180, 180, 180)
            pygame.draw.circle(surface, color, (x + TILE//2, y + TILE//2), 4)
            pygame.draw.circle(surface, (50, 50, 50), (x + TILE//2, y + TILE//2), 4, 1)
            
            if triggered and int(time_val * 5) % 2 == 0:
                pygame.draw.circle(surface, (255, 0, 0), (x + TILE//2, y + TILE//2), 2)
        
        # Emergency lights
        if alarm_active:
            for (r, c), info in self.emergency_lights.items():
                x = int(c * TILE + shake[0])
                y = int(r * TILE + shake[1])
                
                # Flashing arrow toward exit
                if int(time_val * 3) % 2 == 0:
                    color = (100, 255, 100)
                    dr, dc = info['dir']
                    cx, cy = x + TILE//2, y + TILE//2
                    pygame.draw.polygon(surface, color, [
                        (cx + dc * 5, cy + dr * 5),
                        (cx - dc * 3 - dr * 3, cy - dr * 3 + dc * 3),
                        (cx - dc * 3 + dr * 3, cy - dr * 3 - dc * 3)
                    ])

safety = SafetySystems()

# ═══════════════════════════════════════════════════════════════════════════════
# ALARM SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class AlarmSystem:
    def __init__(self):
        self.active = False
        self.triggered_time = 0
        self.flash_state = False
        self.flash_timer = 0
        self.auto_triggered = False
    
    def trigger(self, auto=False):
        if not self.active:
            self.active = True
            self.auto_triggered = auto
            sound_system.start_alarm()
            safety.activate_emergency_lights()
    
    def update(self, dt):
        if self.active:
            self.triggered_time += dt
            self.flash_timer += dt
            if self.flash_timer > 0.25:
                self.flash_state = not self.flash_state
                self.flash_timer = 0
    
    def reset(self):
        self.active = False
        self.triggered_time = 0
        self.auto_triggered = False
        sound_system.stop_alarm()

alarm = AlarmSystem()

# ═══════════════════════════════════════════════════════════════════════════════
# PATHFINDING
# ═══════════════════════════════════════════════════════════════════════════════

class Pathfinder:
    def __init__(self):
        self.cache = {}
    
    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def find_path(self, start, goal, maze, hazards, smoke, predicted):
        cache_key = (start, goal, len(hazards))
        if cache_key in self.cache:
            return self.cache[cache_key]
        
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
                        
                        cost = 1
                        if neighbor in hazards:
                            cost += 500
                        if neighbor in predicted:
                            cost += 80
                        for (hr, hc) in hazards:
                            dist = abs(nr - hr) + abs(nc - hc)
                            if dist <= 4:
                                cost += (5 - dist) * 40
                        if neighbor in smoke:
                            cost += smoke[neighbor] * 25
                        
                        tentative_g = g_score[current] + cost
                        
                        if neighbor not in g_score or tentative_g < g_score[neighbor]:
                            came_from[neighbor] = current
                            g_score[neighbor] = tentative_g
                            f = tentative_g + self.heuristic(neighbor, goal)
                            heappush(open_set, (f, tentative_g, neighbor))
        
        return []
    
    def clear_cache(self):
        self.cache.clear()

pathfinder = Pathfinder()

# ═══════════════════════════════════════════════════════════════════════════════
# PHEROMONE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class Pheromones:
    def __init__(self):
        self.safe = defaultdict(float)
        self.danger = defaultdict(float)
    
    def add_safe(self, r1, c1, r2, c2, amt):
        key = (min(r1,r2), min(c1,c2), max(r1,r2), max(c1,c2))
        self.safe[key] = min(self.safe[key] + amt, 12.0)
    
    def add_danger(self, row, col, amt):
        self.danger[(row, col)] = min(self.danger[(row, col)] + amt, 25.0)
    
    def evaporate(self):
        for key in list(self.safe.keys()):
            self.safe[key] *= 0.99
            if self.safe[key] < 0.1: del self.safe[key]
        for key in list(self.danger.keys()):
            self.danger[key] *= 0.995
            if self.danger[key] < 0.1: del self.danger[key]
    
    def draw(self, surface, shake):
        for key, level in self.safe.items():
            if level > 0.5:
                r1, c1, r2, c2 = key
                x1 = int((c1 + 0.5) * TILE + shake[0])
                y1 = int((r1 + 0.5) * TILE + shake[1])
                x2 = int((c2 + 0.5) * TILE + shake[0])
                y2 = int((r2 + 0.5) * TILE + shake[1])
                intensity = min(level / 4.0, 1.0)
                width = max(2, int(intensity * 4))
                color = (0, int(180 + 75 * intensity), int(100 + 30 * intensity))
                pygame.draw.line(surface, color, (x1, y1), (x2, y2), width)

pheromones = Pheromones()

# ═══════════════════════════════════════════════════════════════════════════════
# DISASTER SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class Disasters:
    def __init__(self):
        self.hazards = {}
        self.smoke = defaultdict(float)
        self.predicted = set()
        self.shake = 0.0
        self.shake_offset = (0, 0)
        self.particles = []
        self.random_enabled = True
        self.timer = 0
        self.next_event = random.uniform(10, 20)
        self.fire_sound_timer = 0
    
    def add(self, row, col, h_type):
        if (row, col) not in self.hazards:
            self.hazards[(row, col)] = {'type': h_type, 'age': 0}
            pheromones.add_danger(row, col, 15)
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    pheromones.add_danger(row + dr, col + dc, 5)
            pathfinder.clear_cache()
            
            if h_type == 'fire':
                sound_system.play('fire', 0.3)
            if h_type == 'earthquake':
                self.shake = 0.7
                alarm.trigger(auto=True)
    
    def is_dangerous(self, row, col):
        if (row, col) in self.hazards:
            return True
        if (row, col) in self.predicted:
            return True
        if self.smoke.get((row, col), 0) > 0.6:
            return True
        for (hr, hc) in self.hazards:
            if abs(row - hr) + abs(col - hc) <= 2:
                return True
        return False
    
    def update(self, dt, maze):
        self.shake *= 0.9
        if self.shake > 0.01:
            self.shake_offset = (
                random.uniform(-1, 1) * self.shake * 6,
                random.uniform(-1, 1) * self.shake * 6
            )
        else:
            self.shake_offset = (0, 0)
        
        # Fire sound
        if any(h['type'] == 'fire' for h in self.hazards.values()):
            self.fire_sound_timer -= dt
            if self.fire_sound_timer <= 0:
                sound_system.play('fire', 0.15)
                self.fire_sound_timer = 1.5
        
        new_hazards = {}
        to_remove = []
        
        for (row, col), info in list(self.hazards.items()):
            info['age'] += dt
            h_type = info['type']
            
            if h_type == 'fire':
                # Smoke
                for dr in range(-3, 4):
                    for dc in range(-3, 4):
                        sr, sc = row + dr, col + dc
                        if 0 <= sr < ROWS and 0 <= sc < COLS:
                            dist = abs(dr) + abs(dc)
                            self.smoke[(sr, sc)] = min(self.smoke[(sr, sc)] + 0.04 / (dist + 1), 1.5)
                
                # Particles
                if random.random() < 0.35:
                    self.particles.append({
                        'x': col * TILE + random.randint(3, TILE - 3),
                        'y': row * TILE + TILE,
                        'vy': -random.uniform(30, 55),
                        'life': random.uniform(0.3, 0.6),
                    })
                
                # Spread (slowed by sprinklers)
                if info['age'] > 6.0 and random.random() < 0.012:
                    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                    random.shuffle(dirs)
                    for dr, dc in dirs:
                        nr, nc = row + dr, col + dc
                        if 0 < nr < ROWS - 1 and 0 < nc < COLS - 1:
                            if maze[nr][nc] not in [WALL, EXIT] and (nr, nc) not in self.hazards:
                                new_hazards[(nr, nc)] = {'type': 'fire', 'age': 0}
                                pheromones.add_danger(nr, nc, 20)
                                pathfinder.clear_cache()
                                break
                
                if info['age'] > 100:
                    to_remove.append((row, col))
            
            elif h_type == 'flood':
                if info['age'] > 4.0 and random.random() < 0.015:
                    for dr, dc in [(1, 0), (0, -1), (0, 1)]:
                        nr, nc = row + dr, col + dc
                        if 0 < nr < ROWS - 1 and 0 < nc < COLS - 1:
                            if maze[nr][nc] != WALL and (nr, nc) not in self.hazards:
                                new_hazards[(nr, nc)] = {'type': 'flood', 'age': 0}
                                break
            
            elif h_type == 'earthquake':
                if info['age'] > 2:
                    to_remove.append((row, col))
        
        for pos in to_remove:
            if pos in self.hazards:
                del self.hazards[pos]
        self.hazards.update(new_hazards)
        
        # Smoke decay
        for key in list(self.smoke.keys()):
            self.smoke[key] *= 0.96
            if self.smoke[key] < 0.03:
                del self.smoke[key]
        
        # Particles
        for p in self.particles[:]:
            p['y'] += p['vy'] * dt
            p['life'] -= dt
            if p['life'] <= 0:
                self.particles.remove(p)
        
        # Predict spread
        self.predicted.clear()
        for (row, col), info in self.hazards.items():
            if info['type'] == 'fire' and info['age'] > 3:
                for dr in range(-3, 4):
                    for dc in range(-3, 4):
                        nr, nc = row + dr, col + dc
                        if 0 < nr < ROWS - 1 and 0 < nc < COLS - 1:
                            if (nr, nc) not in self.hazards and maze[nr][nc] != WALL:
                                self.predicted.add((nr, nc))
        
        # Random disasters
        if self.random_enabled:
            self.timer += dt
            if self.timer >= self.next_event:
                self._spawn_random(maze)
                self.timer = 0
                self.next_event = random.uniform(25, 45)
    
    def _spawn_random(self, maze):
        h_type = random.choices(['fire', 'flood'], weights=[75, 25])[0]
        for _ in range(30):
            r = random.randint(5, ROWS - 5)
            c = random.randint(5, COLS - 5)
            if maze[r][c] not in [WALL, EXIT] and (r, c) not in self.hazards:
                self.add(r, c, h_type)
                break
    
    def draw_particles(self, surface):
        for p in self.particles:
            alpha = p['life'] / 0.6
            size = int(5 * alpha)
            if size > 0:
                color = (255, int(180 * alpha), 0)
                pygame.draw.circle(surface, color, (int(p['x']), int(p['y'])), size)
    
    def draw_predicted(self, surface, shake, time_val):
        for (r, c) in self.predicted:
            if (r, c) not in self.hazards:
                x = int(c * TILE + shake[0])
                y = int(r * TILE + shake[1])
                pulse = abs(math.sin(time_val * 4)) * 0.4 + 0.6
                alpha = int(40 * pulse)
                overlay = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                overlay.fill((255, 60, 200, alpha))
                surface.blit(overlay, (x, y))

disasters = Disasters()

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
        
        # Add sprinkler and smoke detector in room
        mid_r, mid_c = (r1 + r2) // 2, (c1 + c2) // 2
        safety.add_sprinkler(mid_r, mid_c)
        safety.add_smoke_detector(r1 + 1, c1 + 1)
    
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
    
    # Sprinklers in corridors
    for hr in h_corr:
        for c in range(5, COLS - 5, 10):
            safety.add_sprinkler(hr, c)
    
    # Emergency lights along corridors pointing to exits
    for hr in h_corr:
        for c in range(3, COLS - 3, 6):
            if c < COLS // 2:
                safety.add_emergency_light(hr, c, (0, -1))  # Point left
            else:
                safety.add_emergency_light(hr, c, (0, 1))   # Point right
    
    for vc in v_corr:
        for r in range(3, ROWS - 3, 6):
            if r < ROWS // 2:
                safety.add_emergency_light(r, vc, (-1, 0))  # Point up
            else:
                safety.add_emergency_light(r, vc, (1, 0))   # Point down
    
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

maze, exits = generate_building()

# ═══════════════════════════════════════════════════════════════════════════════
# PERSON CLASS
# ═══════════════════════════════════════════════════════════════════════════════

PERSON_COLORS = [
    (255, 90, 90), (90, 160, 255), (90, 255, 90), (255, 230, 90),
    (255, 90, 255), (90, 255, 255), (255, 160, 90), (210, 90, 255),
    (255, 255, 255), (160, 255, 160), (255, 190, 190), (190, 190, 255),
]

class Person:
    def __init__(self, pid, row, col, initial_state, is_warden=False):
        self.id = pid
        self.color = Colors.WARDEN if is_warden else PERSON_COLORS[pid % len(PERSON_COLORS)]
        self.start_row = row
        self.start_col = col
        self.initial_state = initial_state
        self.is_warden = is_warden
        
        self.awareness_threshold = random.uniform(0.3, 0.8)
        self.panic_tendency = random.uniform(0.1, 0.4)
        self.speed_base = random.uniform(85, 125)
        if is_warden:
            self.speed_base *= 1.2  # Wardens are faster
            self.awareness_threshold = 0.2  # Wardens notice quickly
        
        self.reset()
    
    def reset(self):
        self.row = self.start_row
        self.col = self.start_col
        self.x = self.col * TILE + TILE // 2
        self.y = self.row * TILE + TILE // 2
        self.tx = self.x
        self.ty = self.y
        self.moving = False
        self.alive = True
        self.escaped = False
        self.health = 100
        self.path = [(self.row, self.col)]
        self.walk_frame = 0
        
        self.state = STATE_WARDEN_SWEEP if self.is_warden else self.initial_state
        self.awareness = 1.0 if self.is_warden else 0.0
        self.reaction_delay = 0.0
        self.state_timer = 0.0
        self.phone_alert_received = False
        
        self.target_exit = None
        self.path_to_exit = []
        self.path_index = 0
        self.repath_timer = 0
        
        # Warden specific
        self.people_to_alert = []
        self.current_alert_target = None
    
    def get_reaction_delay(self):
        delays = {
            STATE_WORKING: random.uniform(1.5, 4),
            STATE_HEADPHONES: random.uniform(3, 8),
            STATE_MEETING: random.uniform(1, 2.5),
            STATE_PHONE: random.uniform(2, 4),
            STATE_ZONED_OUT: random.uniform(4, 8),
        }
        return delays.get(self.state, 0.5)
    
    def check_awareness(self, people):
        if self.state in [STATE_AWARE, STATE_EVACUATING, STATE_PANICKING, 
                          STATE_WARDEN_SWEEP, STATE_PHONE_ALERTED]:
            return
        
        awareness_gain = 0
        
        # Phone vibration alert (HIGHEST PRIORITY for headphone users!)
        if buddy_system.is_phone_vibrating(self.id):
            if self.state == STATE_HEADPHONES:
                awareness_gain += 0.8  # Phone vibration breaks through headphones!
                self.phone_alert_received = True
            else:
                awareness_gain += 0.5
        
        # Alarm
        if alarm.active:
            if self.state == STATE_HEADPHONES and not self.phone_alert_received:
                awareness_gain += 0.02  # Might see flashing lights
            else:
                awareness_gain += 0.2
        
        # See fire
        if disasters.hazards:
            for (hr, hc), info in disasters.hazards.items():
                if info['type'] == 'fire':
                    dist = abs(self.row - hr) + abs(self.col - hc)
                    if dist <= 8:
                        awareness_gain += 0.6 / (dist + 1)
        
        # Smell smoke
        smoke = disasters.smoke.get((self.row, self.col), 0)
        if smoke > 0.3:
            awareness_gain += smoke * 0.3
        
        # See others evacuating
        for other in people:
            if other.id != self.id and other.alive and not other.escaped:
                dist = abs(self.row - other.row) + abs(self.col - other.col)
                if dist <= 4:
                    if other.state == STATE_EVACUATING:
                        awareness_gain += 0.15
                        # Alert buddy
                        buddy_system.send_emergency_alert(other, people, alarm.active)
                    elif other.state == STATE_PANICKING:
                        awareness_gain += 0.25
                    elif other.is_warden and other.state == STATE_WARDEN_SWEEP:
                        # Warden physically alerts
                        awareness_gain += 0.9
                        self.phone_alert_received = True  # Treated like direct alert
        
        # Warden taps headphone user
        if self.state == STATE_HEADPHONES:
            for other in people:
                if other.is_warden and other.alive:
                    dist = abs(self.row - other.row) + abs(self.col - other.col)
                    if dist <= 2:
                        awareness_gain += 1.0  # Warden tap always works!
        
        # Earthquake
        if disasters.shake > 0.2:
            awareness_gain += 1.0
        
        # Direct danger
        if disasters.is_dangerous(self.row, self.col):
            awareness_gain += 1.5
        
        self.awareness = min(1.0, self.awareness + awareness_gain * 0.02)
        
        if self.awareness >= self.awareness_threshold:
            if self.reaction_delay <= 0:
                self.reaction_delay = self.get_reaction_delay()
                # Phone alert speeds up reaction
                if self.phone_alert_received:
                    self.reaction_delay *= 0.3
    
    def find_safest_exit(self):
        if not exits:
            return
        
        best_exit = None
        best_score = float('inf')
        
        for exit_pos in exits:
            er, ec = exit_pos
            dist = abs(self.row - er) + abs(self.col - ec)
            
            exit_danger = 0
            for dr in range(-3, 4):
                for dc in range(-3, 4):
                    check = (er + dr, ec + dc)
                    if check in disasters.hazards:
                        exit_danger += 100
                    if check in disasters.predicted:
                        exit_danger += 40
            
            score = dist + exit_danger
            if score < best_score:
                best_score = score
                best_exit = exit_pos
        
        if best_exit:
            self.target_exit = best_exit
            self.path_to_exit = pathfinder.find_path(
                (self.row, self.col),
                best_exit,
                maze,
                disasters.hazards,
                disasters.smoke,
                disasters.predicted
            )
            self.path_index = 0
    
    def flee_from_danger(self):
        best_move = None
        best_safety = -float('inf')
        
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = self.row + dr, self.col + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                if maze[nr][nc] in [FLOOR, CORRIDOR, CARPET, EXIT, DOOR]:
                    if (nr, nc) not in disasters.hazards:
                        min_hazard_dist = float('inf')
                        for (hr, hc) in disasters.hazards:
                            d = abs(nr - hr) + abs(nc - hc)
                            min_hazard_dist = min(min_hazard_dist, d)
                        
                        safety = min_hazard_dist
                        if self.target_exit:
                            er, ec = self.target_exit
                            exit_dist = abs(nr - er) + abs(nc - ec)
                            safety = min_hazard_dist * 2 - exit_dist * 0.5
                        
                        if safety > best_safety:
                            best_safety = safety
                            best_move = (nr, nc)
        
        return best_move
    
    def update_warden(self, dt, people):
        """Special update for floor wardens."""
        if not alarm.active:
            # Normal behavior until alarm
            self.state = self.initial_state
            self.check_awareness(people)
            return False  # Use normal update
        
        self.state = STATE_WARDEN_SWEEP
        
        # Find unaware people to alert
        if not self.current_alert_target:
            best_target = None
            best_dist = float('inf')
            
            for other in people:
                if other.id != self.id and other.alive and not other.escaped:
                    if other.state in [STATE_WORKING, STATE_HEADPHONES, STATE_MEETING, 
                                       STATE_PHONE, STATE_ZONED_OUT]:
                        dist = abs(self.row - other.row) + abs(self.col - other.col)
                        if dist < best_dist:
                            best_dist = dist
                            best_target = other
            
            self.current_alert_target = best_target
        
        if self.current_alert_target:
            target = self.current_alert_target
            if not target.alive or target.escaped or target.state in [STATE_EVACUATING, STATE_AWARE]:
                self.current_alert_target = None
                return True
            
            # Move toward target
            if not self.moving:
                tr, tc = target.row, target.col
                
                # Adjacent? Alert them!
                if abs(self.row - tr) + abs(self.col - tc) <= 2:
                    target.awareness = 1.0
                    target.reaction_delay = 0.2
                    target.phone_alert_received = True
                    self.current_alert_target = None
                    return True
                
                # Move toward target
                best_move = None
                best_dist = float('inf')
                
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = self.row + dr, self.col + dc
                    if 0 <= nr < ROWS and 0 <= nc < COLS:
                        if maze[nr][nc] in [FLOOR, CORRIDOR, CARPET, EXIT, DOOR]:
                            if not disasters.is_dangerous(nr, nc):
                                dist = abs(nr - tr) + abs(nc - tc)
                                if dist < best_dist:
                                    best_dist = dist
                                    best_move = (nr, nc)
                
                if best_move:
                    nr, nc = best_move
                    self.tx = nc * TILE + TILE // 2
                    self.ty = nr * TILE + TILE // 2
                    self.row, self.col = nr, nc
                    self.path.append((nr, nc))
                    self.moving = True
            
            return True
        else:
            # No one to alert, evacuate self
            return False
    
    def update(self, dt, people):
        if not self.alive or self.escaped:
            return
        
        self.state_timer += dt
        
        # Warden behavior
        if self.is_warden:
            if self.update_warden(dt, people):
                # Warden is alerting, handle movement
                if self.moving:
                    self.walk_frame += dt * 14
                    speed = self.speed_base * 1.3
                    dx = self.tx - self.x
                    dy = self.ty - self.y
                    dist = math.hypot(dx, dy)
                    if dist < 2:
                        self.x, self.y = self.tx, self.ty
                        self.moving = False
                    else:
                        self.x += (dx / dist) * speed * dt
                        self.y += (dy / dist) * speed * dt
                return
        
        # Damage check
        current_danger = False
        
        if (self.row, self.col) in disasters.hazards:
            h_type = disasters.hazards[(self.row, self.col)]['type']
            if h_type == 'fire':
                self.health -= 35 * dt
                current_danger = True
                self.state = STATE_PANICKING
                if random.random() < 0.01:
                    sound_system.play('panic', 0.2)
            elif h_type == 'flood':
                self.health -= 18 * dt
                current_danger = True
        
        smoke = disasters.smoke.get((self.row, self.col), 0)
        if smoke > 0.5:
            self.health -= smoke * 12 * dt
            current_danger = True
        
        # Health regen when safe
        if not current_danger and self.health < 100:
            self.health = min(100, self.health + 12 * dt)
        
        # Death
        if self.health <= 0:
            self.alive = False
            stats['deaths'] += 1
            pheromones.add_danger(self.row, self.col, 50)
            sound_system.play('panic', 0.3)
            return
        
        # Awareness check
        self.check_awareness(people)
        
        # State machine
        if self.state in [STATE_WORKING, STATE_HEADPHONES, STATE_MEETING,
                          STATE_PHONE, STATE_ZONED_OUT]:
            if self.awareness >= self.awareness_threshold:
                self.reaction_delay -= dt
                if self.reaction_delay <= 0:
                    if random.random() < self.panic_tendency:
                        self.state = STATE_PANICKING
                    else:
                        self.state = STATE_AWARE
                    # Alert buddy when becoming aware
                    buddy_system.send_emergency_alert(self, people, alarm.active)
            return
        
        if self.state == STATE_AWARE:
            self.state_timer += dt
            if self.state_timer > 0.4:
                self.state = STATE_EVACUATING
                self.state_timer = 0
            return
        
        # Evacuating or panicking
        if self.moving:
            self.walk_frame += dt * 12
        
        if not self.moving:
            if maze[self.row][self.col] == EXIT:
                self.escaped = True
                stats['escaped'] += 1
                sound_system.play('escape', 0.2)
                
                for i in range(len(self.path) - 1):
                    r1, c1 = self.path[i]
                    r2, c2 = self.path[i + 1]
                    pheromones.add_safe(r1, c1, r2, c2, 6.0 / len(self.path))
                return
            
            if self.state == STATE_PANICKING:
                if current_danger:
                    flee_pos = self.flee_from_danger()
                    if flee_pos:
                        nr, nc = flee_pos
                        self.tx = nc * TILE + TILE // 2
                        self.ty = nr * TILE + TILE // 2
                        self.row, self.col = nr, nc
                        self.path.append((nr, nc))
                        self.moving = True
                        return
                
                if not current_danger and random.random() < 0.03:
                    self.state = STATE_EVACUATING
            
            self.repath_timer += dt
            if not self.path_to_exit or self.repath_timer > 1.5:
                self.find_safest_exit()
                self.repath_timer = 0
            
            if self.path_to_exit and self.path_index < len(self.path_to_exit):
                next_pos = self.path_to_exit[self.path_index]
                nr, nc = next_pos
                
                if disasters.is_dangerous(nr, nc):
                    self.find_safest_exit()
                    return
                
                self.tx = nc * TILE + TILE // 2
                self.ty = nr * TILE + TILE // 2
                self.row, self.col = nr, nc
                self.path.append((nr, nc))
                self.path_index += 1
                self.moving = True
            else:
                if self.target_exit:
                    er, ec = self.target_exit
                    best_move = None
                    best_dist = float('inf')
                    
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = self.row + dr, self.col + dc
                        if 0 <= nr < ROWS and 0 <= nc < COLS:
                            if maze[nr][nc] in [FLOOR, CORRIDOR, CARPET, EXIT, DOOR]:
                                if not disasters.is_dangerous(nr, nc):
                                    dist = abs(nr - er) + abs(nc - ec)
                                    if dist < best_dist:
                                        best_dist = dist
                                        best_move = (nr, nc)
                    
                    if best_move:
                        nr, nc = best_move
                        self.tx = nc * TILE + TILE // 2
                        self.ty = nr * TILE + TILE // 2
                        self.row, self.col = nr, nc
                        self.path.append((nr, nc))
                        self.moving = True
        
        if self.moving:
            speed = self.speed_base
            if self.state == STATE_PANICKING:
                speed *= 1.4
            elif self.state == STATE_EVACUATING:
                speed *= 1.15
            
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.hypot(dx, dy)
            
            if dist < 2:
                self.x, self.y = self.tx, self.ty
                self.moving = False
            else:
                self.x += (dx / dist) * speed * dt
                self.y += (dy / dist) * speed * dt
    
    def draw(self, surface, shake, show_lines, time_val):
        if not self.alive or self.escaped:
            return
        
        x = int(self.x + shake[0])
        y = int(self.y + shake[1])
        
        # Line to exit
        if show_lines and self.target_exit and self.state in [STATE_EVACUATING, STATE_PANICKING]:
            er, ec = self.target_exit
            ex = int((ec + 0.5) * TILE + shake[0])
            ey = int((er + 0.5) * TILE + shake[1])
            line_color = Colors.DANGER if self.state == STATE_PANICKING else self.color
            pygame.draw.line(surface, (*line_color[:3], 100), (x, y), (ex, ey), 1)
        
        # Shadow
        pygame.draw.ellipse(surface, (35, 35, 35), (x - 5, y + 5, 10, 5))
        
        # Legs
        leg_color = (45, 45, 55)
        if self.moving:
            leg_offset = math.sin(self.walk_frame) * 2
            pygame.draw.rect(surface, leg_color, (x - 4 + int(leg_offset), y + 1, 3, 6))
            pygame.draw.rect(surface, leg_color, (x + 1 - int(leg_offset), y + 1, 3, 6))
        else:
            pygame.draw.rect(surface, leg_color, (x - 4, y + 1, 3, 6))
            pygame.draw.rect(surface, leg_color, (x + 1, y + 1, 3, 6))
        
        # Body outline
        if self.is_warden:
            outline = Colors.WARDEN
        elif self.state == STATE_PANICKING:
            outline = Colors.DANGER
        elif self.state == STATE_EVACUATING:
            outline = Colors.EVACUATING
        elif self.state == STATE_AWARE or self.state == STATE_PHONE_ALERTED:
            outline = Colors.AWARE
        elif self.state == STATE_HEADPHONES:
            outline = Colors.HEADPHONES
        elif buddy_system.is_phone_vibrating(self.id):
            outline = Colors.PHONE_ALERT if int(time_val * 8) % 2 == 0 else Colors.HEADPHONES
        else:
            outline = (0, 0, 0)
        
        # Body
        pygame.draw.rect(surface, outline, (x - 6, y - 8, 12, 10))
        pygame.draw.rect(surface, self.color, (x - 5, y - 7, 10, 8))
        
        # Head
        pygame.draw.rect(surface, outline, (x - 5, y - 15, 10, 8))
        pygame.draw.rect(surface, (240, 200, 170), (x - 4, y - 14, 8, 6))
        
        # Warden hat
        if self.is_warden:
            pygame.draw.rect(surface, Colors.WARDEN, (x - 5, y - 17, 10, 3))
            pygame.draw.rect(surface, (200, 170, 0), (x - 3, y - 19, 6, 2))
        
        # State label
        font = pygame.font.Font(None, 12)
        state_short = {
            STATE_WORKING: "W",
            STATE_HEADPHONES: "🎧",
            STATE_MEETING: "M",
            STATE_PHONE: "📱",
            STATE_ZONED_OUT: "Z",
            STATE_AWARE: "!",
            STATE_EVACUATING: ">",
            STATE_PANICKING: "!!",
            STATE_WARDEN_SWEEP: "👷",
        }
        label_text = state_short.get(self.state, "?")
        if buddy_system.is_phone_vibrating(self.id):
            label_text = "📳"
        
        # Phone vibration effect
        if buddy_system.is_phone_vibrating(self.id):
            vib_offset = math.sin(time_val * 30) * 2
            pygame.draw.circle(surface, Colors.PHONE_ALERT, (x + int(vib_offset), y - 20), 4)
        
        # Health bar
        if self.health < 95:
            bar_w = int(10 * self.health / 100)
            pygame.draw.rect(surface, (180, 0, 0), (x - 5, y - 23, 10, 3))
            pygame.draw.rect(surface, (0, 220, 0), (x - 5, y - 23, bar_w, 3))

# ═══════════════════════════════════════════════════════════════════════════════
# SPAWN PEOPLE
# ═══════════════════════════════════════════════════════════════════════════════

def spawn_people(count=TOTAL_PEOPLE):
    ppl = []
    spawns = []
    
    for r in range(2, ROWS - 2):
        for c in range(2, COLS - 2):
            if maze[r][c] in [CARPET, FLOOR, CORRIDOR]:
                spawns.append((r, c))
    
    random.shuffle(spawns)
    
    states = (
        [STATE_WORKING] * 18 +
        [STATE_HEADPHONES] * 10 +
        [STATE_MEETING] * 8 +
        [STATE_PHONE] * 6 +
        [STATE_ZONED_OUT] * 4
    )
    random.shuffle(states)
    
    # Spawn wardens first (in corridors)
    corridor_spawns = [(r, c) for r, c in spawns if maze[r][c] == CORRIDOR]
    for i in range(min(NUM_WARDENS, len(corridor_spawns))):
        r, c = corridor_spawns[i]
        ppl.append(Person(i, r, c, STATE_WORKING, is_warden=True))
    
    # Spawn regular people
    for i in range(NUM_WARDENS, min(count, len(spawns))):
        r, c = spawns[i]
        state = states[(i - NUM_WARDENS) % len(states)]
        ppl.append(Person(i, r, c, state, is_warden=False))
    
    # Assign buddies
    buddy_system.assign_buddies(ppl)
    
    return ppl

people = spawn_people(TOTAL_PEOPLE)

# ═══════════════════════════════════════════════════════════════════════════════
# STATS
# ═══════════════════════════════════════════════════════════════════════════════

stats = {
    'escaped': 0,
    'deaths': 0,
}

# ═══════════════════════════════════════════════════════════════════════════════
# DRAWING
# ═══════════════════════════════════════════════════════════════════════════════

def draw_tile(surface, row, col, time_val, shake):
    x = int(col * TILE + shake[0])
    y = int(row * TILE + shake[1])
    tile = maze[row][col]
    
    flash = alarm.active and alarm.flash_state
    
    if (row, col) in disasters.hazards:
        h = disasters.hazards[(row, col)]
        h_type = h['type']
        
        if h_type == 'fire':
            pygame.draw.rect(surface, (65, 35, 20), (x, y, TILE, TILE))
            for i in range(3):
                fx = x + 3 + i * 5
                fh = 9 + math.sin(time_val * 10 + i + col) * 4
                colors = [Colors.FIRE_BRIGHT, Colors.FIRE, (200, 60, 10)]
                pygame.draw.polygon(surface, colors[i % 3], [
                    (fx, y + TILE), (fx + 3, y + TILE), (fx + 1, y + TILE - fh)
                ])
            return
        
        elif h_type == 'flood':
            pygame.draw.rect(surface, Colors.FLOOR_DARK, (x, y, TILE, TILE))
            wave = math.sin(time_val * 3 + col * 0.3) * 2
            pygame.draw.rect(surface, Colors.WATER, (x, y + TILE//2 + int(wave), TILE, TILE//2))
            return
    
    if tile == FLOOR:
        color = Colors.FLOOR if (row + col) % 2 == 0 else Colors.FLOOR_DARK
        pygame.draw.rect(surface, color, (x, y, TILE, TILE))
    elif tile == WALL:
        pygame.draw.rect(surface, Colors.WALL, (x, y, TILE, TILE))
    elif tile == CORRIDOR:
        pygame.draw.rect(surface, Colors.CORRIDOR, (x, y, TILE, TILE))
    elif tile == CARPET:
        pygame.draw.rect(surface, Colors.CARPET, (x, y, TILE, TILE))
    elif tile == EXIT:
        glow = int(abs(math.sin(time_val * 4)) * 50)
        color = (50 + glow, 255, 50 + glow)
        pygame.draw.rect(surface, color, (x, y, TILE, TILE))
        pygame.draw.rect(surface, (255, 255, 255), (x + 2, y + 2, TILE - 4, TILE - 4), 2)
    elif tile == DOOR:
        pygame.draw.rect(surface, Colors.DOOR, (x, y, TILE, TILE))
    
    if flash and tile != WALL:
        overlay = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        overlay.fill((255, 0, 0, 25))
        surface.blit(overlay, (x, y))

def draw_smoke(surface, shake):
    for (r, c), level in disasters.smoke.items():
        if level > 0.12:
            x = int(c * TILE + shake[0])
            y = int(r * TILE + shake[1])
            alpha = min(int(level * 100), 180)
            overlay = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
            overlay.fill((70, 70, 70, alpha))
            surface.blit(overlay, (x, y))

def draw_panel(surface, time_val, show_lines, show_buddies):
    px = MAP_WIDTH
    pygame.draw.rect(surface, Colors.PANEL_BG, (px, 0, PANEL_WIDTH, SCREEN_HEIGHT))
    pygame.draw.line(surface, Colors.PANEL_BORDER, (px, 0), (px, SCREEN_HEIGHT), 2)
    
    font_big = pygame.font.Font(None, 24)
    font_med = pygame.font.Font(None, 18)
    font_small = pygame.font.Font(None, 15)
    
    y = 8
    
    title = font_big.render("🛡️ ZERO DEATH SYSTEMS", True, Colors.ACCENT)
    surface.blit(title, (px + 10, y))
    y += 26
    
    # Escape counter
    pygame.draw.rect(surface, Colors.PANEL_BORDER, (px + 10, y, PANEL_WIDTH - 20, 42), 2)
    escaped_text = font_big.render(f"ESCAPED: {stats['escaped']}/{TOTAL_PEOPLE}", True, Colors.SUCCESS)
    surface.blit(escaped_text, (px + 18, y + 5))
    progress = stats['escaped'] / TOTAL_PEOPLE
    pygame.draw.rect(surface, (40, 80, 40), (px + 15, y + 28, PANEL_WIDTH - 30, 8))
    pygame.draw.rect(surface, Colors.SUCCESS, (px + 15, y + 28, int((PANEL_WIDTH - 30) * progress), 8))
    y += 48
    
    # Death status
    if stats['deaths'] == 0:
        surface.blit(font_med.render("✓ ZERO DEATHS!", True, Colors.SUCCESS), (px + 10, y))
    else:
        surface.blit(font_med.render(f"✗ {stats['deaths']} DEATH(S)", True, Colors.DANGER_TEXT), (px + 10, y))
    y += 20
    
    pygame.draw.line(surface, Colors.PANEL_BORDER, (px + 10, y), (px + PANEL_WIDTH - 10, y), 1)
    y += 6
    
    # Safety systems status
    surface.blit(font_med.render("SAFETY SYSTEMS", True, Colors.TEXT_WHITE), (px + 10, y))
    y += 18
    
    systems = [
        ("🚨 Alarm", "ACTIVE" if alarm.active else "Ready", Colors.ALARM_RED if alarm.active else Colors.TEXT_GRAY),
        ("🔥 Detectors", f"{sum(safety.smoke_detectors.values())}/{len(safety.smoke_detectors)} triggered", 
         Colors.ALARM_RED if safety.detector_triggered else Colors.TEXT_GRAY),
        ("🧯 Sprinklers", f"{sum(safety.sprinklers.values())}/{len(safety.sprinklers)} active",
         Colors.SPRINKLER_WATER if safety.sprinklers_active else Colors.TEXT_GRAY),
        ("👷 Wardens", f"{NUM_WARDENS} on duty", Colors.WARDEN),
        ("📱 Buddy Alerts", f"{len(buddy_system.alerted_phones)} sent", Colors.PHONE_ALERT),
    ]
    
    for icon_name, status, color in systems:
        surface.blit(font_small.render(f"{icon_name}: {status}", True, color), (px + 12, y))
        y += 14
    
    y += 6
    pygame.draw.line(surface, Colors.PANEL_BORDER, (px + 10, y), (px + PANEL_WIDTH - 10, y), 1)
    y += 6
    
    # People status
    surface.blit(font_med.render("PEOPLE STATUS", True, Colors.TEXT_WHITE), (px + 10, y))
    y += 16
    
    state_counts = defaultdict(int)
    for p in people:
        if p.alive and not p.escaped:
            state_counts[p.state] += 1
    
    headphone_count = state_counts.get(STATE_HEADPHONES, 0)
    if headphone_count > 0:
        surface.blit(font_small.render(f"🎧 Headphones: {headphone_count} ⚠️", True, Colors.HEADPHONES), (px + 12, y))
        y += 14
    
    unaware = sum(state_counts.get(s, 0) for s in [STATE_WORKING, STATE_MEETING, STATE_PHONE, STATE_ZONED_OUT])
    surface.blit(font_small.render(f"😐 Unaware: {unaware}", True, Colors.TEXT_GRAY), (px + 12, y))
    y += 14
    surface.blit(font_small.render(f"❗ Aware: {state_counts.get(STATE_AWARE, 0)}", True, Colors.AWARE), (px + 12, y))
    y += 14
    surface.blit(font_small.render(f"🏃 Evacuating: {state_counts.get(STATE_EVACUATING, 0)}", True, Colors.EVACUATING), (px + 12, y))
    y += 14
    surface.blit(font_small.render(f"😱 Panicking: {state_counts.get(STATE_PANICKING, 0)}", True, Colors.PANICKING), (px + 12, y))
    y += 14
    
    y += 6
    pygame.draw.line(surface, Colors.PANEL_BORDER, (px + 10, y), (px + PANEL_WIDTH - 10, y), 1)
    y += 6
    
    # Controls
    surface.blit(font_med.render("CONTROLS", True, Colors.TEXT_WHITE), (px + 10, y))
    y += 16
    
    controls = [
        "Click: Add fire",
        "A: Trigger ALARM 🚨",
        "B: Show buddy connections",
        "M: Mute sounds",
        "1/2/3: Fire/Quake/Flood",
        "Space: Pause | R: Reset",
    ]
    
    for ctrl in controls:
        surface.blit(font_small.render(ctrl, True, Colors.TEXT_GRAY), (px + 12, y))
        y += 13

def draw_bottom(surface, paused, speed, time_val):
    by = MAP_HEIGHT
    
    if alarm.active and alarm.flash_state:
        pygame.draw.rect(surface, (50, 20, 20), (0, by, MAP_WIDTH, 60))
    else:
        pygame.draw.rect(surface, Colors.PANEL_BG, (0, by, MAP_WIDTH, 60))
    
    pygame.draw.line(surface, Colors.PANEL_BORDER, (0, by), (MAP_WIDTH, by), 2)
    
    font = pygame.font.Font(None, 22)
    font_small = pygame.font.Font(None, 17)
    
    alive = sum(1 for p in people if p.alive and not p.escaped)
    headphones = sum(1 for p in people if p.alive and not p.escaped and p.state == STATE_HEADPHONES)
    
    color = Colors.SUCCESS if stats['deaths'] == 0 else Colors.DANGER_TEXT
    surface.blit(font.render(f"ESCAPED: {stats['escaped']}/{TOTAL_PEOPLE} | Deaths: {stats['deaths']}", True, color), (15, by + 8))
    
    status = f"Inside: {alive} | 🎧 Headphones: {headphones} | Speed: {speed:.1f}x"
    if paused:
        status = "⏸ PAUSED | " + status
    surface.blit(font_small.render(status, True, Colors.TEXT_GRAY), (15, by + 32))
    
    if alarm.active:
        alarm_text = "🚨 ALARM ACTIVE - EVACUATE!"
        alarm_color = Colors.ALARM_RED if alarm.flash_state else Colors.WARNING
        surface.blit(font_small.render(alarm_text, True, alarm_color), (MAP_WIDTH - 200, by + 10))

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════════

clock = pygame.time.Clock()
running = True
paused = False
speed = 1.0
frame = 0
hazard_type = 'fire'
show_lines = True
show_buddies = False
muted = False

print("=" * 65)
print("🛡️ DWIGHT V8 - Zero Death Prevention Systems")
print("=" * 65)
print("")
print("SAFETY SYSTEMS:")
print("  📱 Buddy Phone System - Alerts headphone users via phone vibration")
print("  🧯 Sprinklers - Auto-activate near fire")
print("  🚨 Smoke Detectors - Early alarm trigger")
print("  👷 Floor Wardens - Check rooms, physically alert everyone")
print("  💡 Emergency Lights - Flash path to exits")
print("  🔊 Sound Effects - Alarm, fire, alerts")
print("")
print("Press A to trigger alarm, B to show buddy connections")
print("=" * 65)

while running:
    dt = clock.tick(60) / 1000.0
    dt *= speed
    frame += 1
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
                        disasters.add(row, col, hazard_type)
                    elif event.button == 3:
                        if (row, col) in disasters.hazards:
                            del disasters.hazards[(row, col)]
                            pathfinder.clear_cache()
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
            elif event.key == pygame.K_a:
                alarm.trigger()
            elif event.key == pygame.K_b:
                show_buddies = not show_buddies
            elif event.key == pygame.K_m:
                muted = not muted
                if muted:
                    pygame.mixer.pause()
                else:
                    pygame.mixer.unpause()
            elif event.key == pygame.K_r:
                sound_system.stop_alarm()
                disasters = Disasters()
                pheromones = Pheromones()
                pathfinder = Pathfinder()
                alarm = AlarmSystem()
                safety = SafetySystems()
                buddy_system = BuddyPhoneSystem()
                maze, exits = generate_building()
                people = spawn_people(TOTAL_PEOPLE)
                stats = {'escaped': 0, 'deaths': 0}
            elif event.key == pygame.K_l:
                show_lines = not show_lines
            elif event.key == pygame.K_d:
                disasters.random_enabled = not disasters.random_enabled
            elif event.key == pygame.K_1:
                hazard_type = 'fire'
            elif event.key == pygame.K_2:
                hazard_type = 'earthquake'
            elif event.key == pygame.K_3:
                hazard_type = 'flood'
            elif event.key in [pygame.K_EQUALS, pygame.K_PLUS]:
                speed = min(speed + 0.5, 5.0)
            elif event.key == pygame.K_MINUS:
                speed = max(speed - 0.5, 0.5)
    
    if not paused:
        disasters.update(dt, maze)
        alarm.update(dt)
        buddy_system.update(dt, people)
        
        # Safety systems
        if safety.check_detectors(disasters.smoke, disasters.hazards):
            alarm.trigger(auto=True)
        
        if alarm.active:
            safety.activate_sprinklers(disasters.hazards)
        
        safety.apply_sprinkler_effect(disasters.hazards, disasters.smoke, dt)
        safety.update_particles = lambda dt: None  # Handled in apply_sprinkler_effect
        
        if frame % 10 == 0:
            pheromones.evaporate()
        
        for p in people:
            p.update(dt, people)
    
    # RENDER
    screen.fill((35, 35, 40))
    shake = disasters.shake_offset
    
    for r in range(ROWS):
        for c in range(COLS):
            draw_tile(screen, r, c, time_val, shake)
    
    draw_smoke(screen, shake)
    disasters.draw_predicted(screen, shake, time_val)
    pheromones.draw(screen, shake)
    safety.draw(screen, shake, time_val, alarm.active)
    disasters.draw_particles(screen)
    
    if show_buddies:
        buddy_system.draw_buddy_connections(screen, people, shake)
    
    for p in sorted(people, key=lambda x: x.y):
        p.draw(screen, shake, show_lines, time_val)
    
    draw_panel(screen, time_val, show_lines, show_buddies)
    draw_bottom(screen, paused, speed, time_val)
    
    pygame.display.flip()

pygame.quit()
sound_system.stop_alarm()
print(f"\n{'='*50}")
print(f"FINAL RESULTS: Escaped {stats['escaped']}/{TOTAL_PEOPLE}, Deaths: {stats['deaths']}")
if stats['deaths'] == 0:
    print("🎉 PERFECT! ZERO DEATHS ACHIEVED!")
print(f"{'='*50}")