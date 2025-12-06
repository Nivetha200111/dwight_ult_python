"""
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                              ║
║          💡 DWIGHT V13 - FIXED POV & OPTICS UPDATE 💡                                        ║
║                                                                                              ║
║  FIXES:                                                                                      ║
║  ✓ FIXED BLACK SCREEN: Rewrote the lighting engine to use proper RGB Multiplication masks.   ║
║  ✓ VISIBLE ENVIRONMENT: You can now see the floor/walls through the person's eyes.           ║
║  ✓ ESCAPED VIEW: Camera stays with people who escape so you can see the Safe Zone.           ║
║                                                                                              ║
║  CONTROLS:                                                                                   ║
║  [WASD] Pan Camera  |  [Scroll] Zoom                                                         ║
║  [Left Click] Follow Person (POV)  |  [Space] Release Camera                                 ║
║  [B] Bomb  |  [E] Quake  |  [F] Fire                                                         ║
║                                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝
"""

import pygame
import random
import math
from heapq import heappush, heappop

pygame.init()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

ROWS = 40
COLS = 50
TOTAL_PEOPLE = 60

BASE_TILE_W = 32
BASE_TILE_H = 16

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("💡 DWIGHT V13 - Fixed POV Lighting")

# ═══════════════════════════════════════════════════════════════════════════════
# COLORS
# ═══════════════════════════════════════════════════════════════════════════════

class Colors:
    FLOOR = (140, 140, 150)
    WALL_TOP = (70, 70, 80)
    WALL_SIDE = (50, 50, 60)
    RUBBLE = (60, 55, 50)
    EXIT = (50, 255, 100)
    FIRE = (255, 120, 0)
    
    SKINS = [(255, 220, 177), (180, 138, 120), (141, 85, 36)]
    SHIRTS = [(100, 100, 200), (200, 100, 100), (100, 200, 100), (200, 200, 100)]

# Tile Types
FLOOR = 0
WALL = 1
EXIT = 2
RUBBLE = 3

# ═══════════════════════════════════════════════════════════════════════════════
# CAMERA
# ═══════════════════════════════════════════════════════════════════════════════

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.zoom = 1.0
        self.target = None 
        self.shake = 0
        
        self.tile_w = BASE_TILE_W
        self.tile_h = BASE_TILE_H
        self.center_on_map()

    def center_on_map(self):
        self.x = (COLS * self.tile_w) // 2 - SCREEN_WIDTH // 2
        self.y = -100

    def apply_zoom(self, amount):
        old_zoom = self.zoom
        self.zoom += amount
        self.zoom = max(0.5, min(self.zoom, 2.5))
        self.tile_w = int(BASE_TILE_W * self.zoom)
        self.tile_h = int(BASE_TILE_H * self.zoom)
        if self.zoom != old_zoom:
            self.x = int(self.x * (self.zoom / old_zoom))
            self.y = int(self.y * (self.zoom / old_zoom))

    def move(self, dx, dy):
        self.target = None 
        self.x += dx
        self.y += dy

    def update(self):
        if self.shake > 0:
            self.x += random.randint(-self.shake, self.shake)
            self.y += random.randint(-self.shake, self.shake)
            self.shake = int(self.shake * 0.9)

        if self.target:
            tx, ty = self.get_iso_coords(self.target.exact_r, self.target.exact_c)
            desired_x = tx - SCREEN_WIDTH // 2
            desired_y = ty - SCREEN_HEIGHT // 2
            self.x += (desired_x - self.x) * 0.1
            self.y += (desired_y - self.y) * 0.1

    def get_iso_coords(self, r, c):
        iso_x = (c - r) * (self.tile_w // 2)
        iso_y = (c + r) * (self.tile_h // 2)
        return iso_x, iso_y

    def to_screen(self, r, c, z=0):
        iso_x, iso_y = self.get_iso_coords(r, c)
        return int(iso_x - self.x), int(iso_y - self.y - z*self.zoom)

camera = Camera()

# ═══════════════════════════════════════════════════════════════════════════════
# PATHFINDING
# ═══════════════════════════════════════════════════════════════════════════════

class Pathfinder:
    def find_path(self, start, goal, maze, hazards):
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
                return path
            
            r, c = current
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    if maze[nr][nc] != WALL:
                        neighbor = (nr, nc)
                        cost = 1 
                        if maze[nr][nc] == RUBBLE: cost = 8 
                        if neighbor in hazards: cost += 50
                        
                        tentative = g_score[current] + cost
                        if neighbor not in g_score or tentative < g_score[neighbor]:
                            came_from[neighbor] = current
                            g_score[neighbor] = tentative
                            h = abs(nr - goal[0]) + abs(nc - goal[1])
                            heappush(open_set, (tentative + h, tentative, neighbor))
        return []

pathfinder = Pathfinder()

# ═══════════════════════════════════════════════════════════════════════════════
# PERSON AGENT
# ═══════════════════════════════════════════════════════════════════════════════

class Person:
    def __init__(self, pid, r, c):
        self.id = pid
        self.r, self.c = r, c
        self.exact_r, self.exact_c = float(r), float(c)
        self.color_skin = random.choice(Colors.SKINS)
        self.color_shirt = random.choice(Colors.SHIRTS)
        
        self.alive = True
        self.escaped = False
        self.health = 100
        self.injured = False
        self.stun_timer = 0
        
        self.path = []
        self.path_index = 0
        self.anim_offset = random.random() * 6.28
        self.thought = "Working..."
        self.thought_timer = 0
        self.state = "IDLE" 

    def set_thought(self, text):
        if self.thought != text:
            self.thought = text
            self.thought_timer = 2.0

    def update(self, dt, maze, hazards):
        if not self.alive: return
        # Keep updating even if escaped so we can see them

        self.thought_timer -= dt
        
        # Damage
        if not self.escaped:
            if (self.r, self.c) in hazards:
                self.health -= 40 * dt
                self.set_thought("I'M BURNING!")
                self.state = "PANIC"
            
            if self.stun_timer > 0:
                self.stun_timer -= dt
                self.set_thought("Can't hear...")
                return

        if self.health < 50: 
            self.injured = True
            if self.state != "PANIC": self.set_thought("Hurts to walk...")

        if self.health <= 0:
            self.alive = False
            self.set_thought("...")
            return

        if maze[self.r][self.c] == EXIT:
            if not self.escaped:
                self.escaped = True
                self.set_thought("Made it!")
            return

        # Pathfinding
        if not self.path or random.random() < 0.05:
            self.find_exit(maze, hazards)
            if not self.path: 
                self.set_thought("TRAPPED!")
                self.state = "PANIC"
            else:
                if self.state == "IDLE": 
                    self.set_thought("Exit found.")
                    self.state = "MOVING"

        # Move
        if self.path and self.path_index < len(self.path):
            nr, nc = self.path[self.path_index]
            
            speed = 4.0 
            if self.injured: speed = 1.5
            if maze[self.r][self.c] == RUBBLE:
                speed *= 0.3
                self.set_thought("Ugh, debris...")
            
            dr, dc = nr - self.exact_r, nc - self.exact_c
            dist = math.hypot(dr, dc)
            
            if dist > 0:
                move = min(dist, speed * dt)
                self.exact_r += (dr/dist) * move
                self.exact_c += (dc/dist) * move
                
                cur_r, cur_c = int(round(self.exact_r)), int(round(self.exact_c))
                if maze[cur_r][cur_c] == WALL:
                    self.path = [] 
                else:
                    self.r, self.c = cur_r, cur_c
                    if dist < 0.1: self.path_index += 1

    def find_exit(self, maze, hazards):
        best = None
        min_d = 999
        for r in range(ROWS):
            for c in range(COLS):
                if maze[r][c] == EXIT:
                    d = abs(self.r - r) + abs(self.c - c)
                    if d < min_d:
                        min_d = d
                        best = (r,c)
        if best:
            self.path = pathfinder.find_path((self.r, self.c), best, maze, hazards)
            self.path_index = 0

# ═══════════════════════════════════════════════════════════════════════════════
# DRAWING
# ═══════════════════════════════════════════════════════════════════════════════

def draw_iso_tile(surface, r, c, tile):
    sx, sy = camera.to_screen(r, c)
    if sx < -100 or sx > SCREEN_WIDTH+100 or sy < -100 or sy > SCREEN_HEIGHT+100: return

    w = camera.tile_w
    h_tile = camera.tile_h
    col = Colors.FLOOR
    z = 0
    
    if tile == WALL:
        col = Colors.WALL_TOP
        z = int(24 * camera.zoom)
    elif tile == RUBBLE:
        col = Colors.RUBBLE
        z = int(6 * camera.zoom)
    elif tile == EXIT:
        col = Colors.EXIT
    
    top = (sx, sy - z)
    right = (sx + w//2, sy + h_tile//2 - z)
    bottom = (sx, sy + h_tile - z)
    left = (sx - w//2, sy + h_tile//2 - z)
    
    pygame.draw.polygon(surface, col, [top, right, bottom, left])
    if z > 0:
        pygame.draw.polygon(surface, [c*0.6 for c in col], [right, bottom, (bottom[0], bottom[1]+z), (right[0], right[1]+z)])
        pygame.draw.polygon(surface, [c*0.8 for c in col], [left, bottom, (bottom[0], bottom[1]+z), (left[0], left[1]+z)])

def draw_person(surface, p, time_val):
    sx, sy = camera.to_screen(p.exact_r, p.exact_c)
    if sx < -50 or sx > SCREEN_WIDTH+50 or sy < -50 or sy > SCREEN_HEIGHT+50: return
    
    zoom = camera.zoom
    if not p.alive:
        pygame.draw.rect(surface, p.color_shirt, (sx - 8*zoom, sy - 2*zoom, 16*zoom, 4*zoom))
        return

    bob = 0
    if p.state == "MOVING": bob = math.sin(time_val * 10 + p.anim_offset) * 2 * zoom
    
    h = 16 * zoom
    w = 8 * zoom
    
    # Legs
    pygame.draw.line(surface, (50,50,50), (sx-2*zoom, sy), (sx-2*zoom, sy-h//2), int(2*zoom))
    pygame.draw.line(surface, (50,50,50), (sx+2*zoom, sy), (sx+2*zoom, sy-h//2), int(2*zoom))
    
    # Body
    pygame.draw.rect(surface, p.color_shirt, (sx - w//2, sy - h + bob, w, h//1.5))
    
    # Head
    head_y = sy - h + bob - 4*zoom
    pygame.draw.circle(surface, p.color_skin, (sx, head_y), int(4*zoom))
    
    if p.stun_timer > 0:
         pygame.draw.circle(surface, (255, 255, 0), (sx, head_y - 8*zoom), int(2*zoom))
    
    if camera.target == p:
        arrow_y = head_y - 15*zoom + math.sin(time_val*5)*5
        pygame.draw.polygon(surface, (255, 255, 0), [(sx, arrow_y + 10*zoom), (sx - 5*zoom, arrow_y), (sx + 5*zoom, arrow_y)])

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    clock = pygame.time.Clock()
    
    maze = [[FLOOR for _ in range(COLS)] for _ in range(ROWS)]
    for r in range(ROWS): maze[r][0] = maze[r][COLS-1] = WALL
    for c in range(COLS): maze[0][c] = maze[ROWS-1][c] = WALL
    
    for r in range(5, ROWS-5, 8):
        for c in range(5, COLS-5, 8):
             maze[r][c] = WALL
             maze[r+1][c] = WALL
             maze[r][c+1] = WALL
            
    maze[ROWS//2][0] = EXIT
    maze[ROWS//2][COLS-1] = EXIT

    people = []
    for i in range(TOTAL_PEOPLE):
        r, c = random.randint(2, ROWS-2), random.randint(2, COLS-2)
        while maze[r][c] == WALL: r, c = random.randint(2, ROWS-2), random.randint(2, COLS-2)
        people.append(Person(i, r, c))
        
    hazards = {}
    running = True
    
    while running:
        dt = clock.tick(30) / 1000.0
        time_val = pygame.time.get_ticks() / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.MOUSEWHEEL:
                camera.apply_zoom(event.y * 0.1)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    best_dist = 40 * camera.zoom
                    selected = None
                    for p in people:
                        # Allow selecting anyone, alive or escaped
                        px, py = camera.to_screen(p.exact_r, p.exact_c)
                        d = math.hypot(px - mx, py - my)
                        if d < best_dist:
                            best_dist = d
                            selected = p
                    if selected: camera.target = selected
                elif event.button == 3:
                    camera.target = None
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b:
                    camera.shake = 15
                    for _ in range(4):
                        ir, ic = random.randint(2, ROWS-2), random.randint(2, COLS-2)
                        maze[ir][ic] = RUBBLE
                        for dr in range(-1, 2):
                            for dc in range(-1, 2):
                                if 0<=ir+dr<ROWS and 0<=ic+dc<COLS:
                                    if random.random() < 0.8: maze[ir+dr][ic+dc] = RUBBLE
                        for p in people:
                             if abs(p.r - ir) + abs(p.c - ic) < 6:
                                 p.stun_timer = 3.0
                                 p.set_thought("EARS RINGING!")
                        if random.random() < 0.5: hazards[(ir, ic)] = 20.0
                elif event.key == pygame.K_e:
                    camera.shake = 25
                    for _ in range(60):
                        rx, ry = random.randint(2, ROWS-2), random.randint(2, COLS-2)
                        if maze[rx][ry] == FLOOR: maze[rx][ry] = RUBBLE
                elif event.key == pygame.K_f:
                    for _ in range(10):
                        fx, fy = random.randint(2, ROWS-2), random.randint(2, COLS-2)
                        if maze[fx][fy] != WALL: hazards[(fx, fy)] = 25.0
                elif event.key == pygame.K_r: return main()
                elif event.key == pygame.K_SPACE: camera.target = None

        keys = pygame.key.get_pressed()
        s = 15
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: camera.move(-s, 0)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: camera.move(s, 0)
        if keys[pygame.K_UP] or keys[pygame.K_w]: camera.move(0, -s)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: camera.move(0, s)

        camera.update()
        
        del_list = []
        for h in hazards:
            hazards[h] -= dt
            if hazards[h] <= 0: del_list.append(h)
        for h in del_list: del hazards[h]
        
        if random.random() < 0.1:
            keys_list = list(hazards.keys())
            if keys_list:
                src = random.choice(keys_list)
                nr, nc = src[0] + random.randint(-1,1), src[1] + random.randint(-1,1)
                if 0<=nr<ROWS and 0<=nc<COLS and maze[nr][nc] != WALL and (nr,nc) not in hazards:
                    hazards[(nr,nc)] = 10.0

        for p in people: p.update(dt, maze, hazards)

        screen.fill((20, 20, 25))
        
        for r in range(ROWS):
            for c in range(COLS):
                draw_iso_tile(screen, r, c, maze[r][c])
        
        for r, c in hazards:
            sx, sy = camera.to_screen(r, c)
            pygame.draw.circle(screen, Colors.FIRE, (sx, sy - int(10*camera.zoom)), int(6*camera.zoom))

        people.sort(key=lambda p: p.exact_r + p.exact_c)
        for p in people:
            draw_person(screen, p, time_val)

        # --- LIGHTING SYSTEM (THE FIX) ---
        if camera.target:
            # 1. Create a Light Mask (Dark Grey)
            light_mask = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            light_mask.fill((30, 30, 30)) # Ambient Darkness
            
            # 2. Draw Vision Circle (White = Visible)
            tx, ty = camera.to_screen(camera.target.exact_r, camera.target.exact_c)
            pygame.draw.circle(light_mask, (255, 255, 255), (tx, ty - 20), int(200 * camera.zoom))
            
            # 3. Multiply Mask with Screen (White reveals, Grey dims)
            screen.blit(light_mask, (0, 0), special_flags=pygame.BLEND_MULT)
            
            # 4. Thought Bubble (On top of darkness)
            pygame.draw.rect(screen, (255,255,255), (tx+30, ty-90, 180, 50), border_radius=8)
            pygame.draw.polygon(screen, (255,255,255), [(tx+30, ty-50), (tx+20, ty-30), (tx+50, ty-50)])
            font_sm = pygame.font.Font(None, 24)
            screen.blit(font_sm.render(camera.target.thought, True, (0,0,0)), (tx+40, ty-75))

        pygame.draw.rect(screen, (0,0,0), (0,0, SCREEN_WIDTH, 40))
        font = pygame.font.Font(None, 28)
        status = f"Alive: {sum(1 for p in people if p.alive)} | Escaped: {sum(1 for p in people if p.escaped)}"
        screen.blit(font.render(status, True, (255,255,255)), (10, 10))
        
        help_txt = "[B] Bomb  [E] Quake  [F] Fire  |  Click Person for POV"
        screen.blit(font.render(help_txt, True, (180, 180, 180)), (SCREEN_WIDTH - 450, 10))

        pygame.display.flip()

if __name__ == "__main__":
    main()
    pygame.quit()