import pygame
import math
import random
import sys
import os

# Initialize Pygame
pygame.init()
pygame.font.init()

# Setup Fullscreen Mode
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
HALF_WIDTH = WIDTH // 2
HALF_HEIGHT = HEIGHT // 2
FPS = 60

pygame.display.set_caption("cs: gu - Pigeon Offensive")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18, bold=True)
large_font = pygame.font.SysFont("Arial", 40, bold=True)

# Colors
WHITE = (240, 240, 240)
BLACK = (12, 12, 15)
DARK_GRAY = (35, 35, 40)
FLOOR_GRAY = (50, 50, 55)
GRID_LINE = (42, 42, 46)
RED = (255, 60, 60)
GREEN = (60, 255, 60)
BLUE = (50, 120, 255)
YELLOW = (255, 225, 0)

# --- TEXTURE LOADING SYSTEM (AUTO-LOCAL DETECTION) ---
# This looks in the exact same folder where your script is running
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
human_texture = None
pigeon_texture = None

try:
    human_path = os.path.join(SCRIPT_DIR, "1111.jpg")
    pigeon_path = os.path.join(SCRIPT_DIR, "2222.jpeg")
    
    if os.path.exists(human_path):
        human_texture = pygame.image.load(human_path).convert_alpha()
    if os.path.exists(pigeon_path):
        pigeon_texture = pygame.image.load(pigeon_path).convert_alpha()
except Exception as e:
    print(f"Texture load fallback active: {e}")

# PATHWAYS MAP (0 = Walkable Corridor, 1 = Human Block, 2 = Pigeon Block)
MAP = [
    [1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2],
    [1,0,0,0,0,1,0,0,0,0,2,0,0,0,0,2],
    [1,0,1,1,0,1,0,1,2,0,2,0,2,2,0,2],
    [1,0,1,0,0,0,0,1,2,0,0,0,0,2,0,2],
    [1,0,1,0,1,1,1,1,2,2,2,2,0,2,0,2],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2],
    [1,1,1,1,0,1,1,0,0,2,2,0,2,2,2,2],
    [1,0,0,0,0,1,0,0,0,0,2,0,0,0,0,2],
    [1,0,1,1,0,1,0,0,0,0,2,0,2,2,0,2],
    [1,1,1,1,0,1,1,1,2,2,2,0,2,2,2,2],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2],
    [1,0,2,0,2,2,2,2,1,1,1,1,0,1,0,2],
    [1,0,2,0,0,0,0,2,1,0,0,0,0,1,0,2],
    [1,0,2,2,0,2,0,2,1,0,1,1,0,1,0,2],
    [1,0,0,0,0,2,0,0,0,0,1,0,0,0,0,2],
    [1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2]
]
MAP_SIZE = len(MAP)
TILE_SIZE = 90  # Sky view scaling factor

PIGEON_BOTS = ["Cooer_2222", "Feather_2222", "Wing_2222", "Squab_2222"]
HUMAN_BOTS = ["Soldier_1111", "Marine_1111", "Ranger_1111", "Agent_1111"]

class KillFeed:
    def __init__(self):
        self.logs = []

    def log_kill(self, attacker, victim):
        self.logs.append({"msg": f"{attacker} eliminated {victim}", "time": pygame.time.get_ticks()})

    def draw(self, surface):
        now = pygame.time.get_ticks()
        self.logs = [log for log in self.logs if now - log["time"] < 3500]
        for i, log in enumerate(reversed(self.logs)):
            text = font.render(log["msg"], True, YELLOW)
            surface.blit(text, (WIDTH - text.get_width() - 20, 20 + i * 25))

kill_feed = KillFeed()

# --- BALLISTIC RAY INTERCEPT ENGINE ---
def check_bullet_trajectory(x1, y1, x2, y2):
    """Traces a line from start to target. Returns (hit_wall, final_x, final_y)"""
    distance = math.hypot(x2 - x1, y2 - y1)
    steps = int(distance * 30) + 1  # High precision density scan
    
    for i in range(steps):
        percent = i / steps
        curr_x = x1 + (x2 - x1) * percent
        curr_y = y1 + (y2 - y1) * percent
        
        # Check map boundaries and solid blocks
        if 0 <= curr_x < MAP_SIZE and 0 <= curr_y < MAP_SIZE:
            if MAP[int(curr_y)][int(curr_x)] > 0:
                return True, curr_x, curr_y
        else:
            return True, curr_x, curr_y
            
    return False, x2, y2

class Entity:
    def __init__(self, x, y, team, name, is_bot=True):
        self.x = x
        self.y = y
        self.team = team
        self.name = name
        self.is_bot = is_bot
        self.angle = random.uniform(0, 2 * math.pi)
        self.health = 100
        self.is_dead = False
        self.death_time = 0
        self.cooldown = 0
        self.speed = 0.04

    def take_damage(self, amount, attacker):
        if self.is_dead: return
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.is_dead = True
            self.death_time = pygame.time.get_ticks()
            kill_feed.log_kill(attacker, self.name)

    def respawn(self):
        while True:
            rx, ry = random.randint(1, MAP_SIZE-2) + 0.5, random.randint(1, MAP_SIZE-2) + 0.5
            if MAP[int(ry)][int(rx)] == 0:
                self.x, self.y = rx, ry
                break
        self.health = 100
        self.is_dead = False

    def update(self, player, bots, shot_tracers):
        if self.is_dead:
            if pygame.time.get_ticks() - self.death_time > 3000:
                self.respawn()
            return

        if self.cooldown > 0: self.cooldown -= 1

        target = None
        closest_dist = 10.0

        if player.team != self.team and not player.is_dead:
            # Check if bot can actually see you through walls before targeting
            blocked, _, _ = check_bullet_trajectory(self.x, self.y, player.x, player.y)
            if not blocked:
                closest_dist = math.hypot(player.x - self.x, player.y - self.y)
                target = player

        for bot in bots:
            if bot != self and bot.team != self.team and not bot.is_dead:
                d = math.hypot(bot.x - self.x, bot.y - self.y)
                if d < closest_dist:
                    blocked, _, _ = check_bullet_trajectory(self.x, self.y, bot.x, bot.y)
                    if not blocked:
                        closest_dist = d
                        target = bot

        if target:
            self.angle = math.atan2(target.y - self.y, target.x - self.x)
            if closest_dist > 1.2:
                nx = self.x + math.cos(self.angle) * self.speed
                ny = self.y + math.sin(self.angle) * self.speed
                if MAP[int(self.y)][int(nx)] == 0: self.x = nx
                if MAP[int(ny)][int(self.x)] == 0: self.y = ny
            
            if self.cooldown == 0 and random.random() < 0.05:
                self.cooldown = 40
                # Double verification check for projectile impact lines
                is_obstructed, fx, fy = check_bullet_trajectory(self.x, self.y, target.x, target.y)
                shot_tracers.append(((self.x, self.y), (fx, fy), pygame.time.get_ticks() + 80))
                if not is_obstructed:
                    target.take_damage(12, self.name)
        else:
            if random.random() < 0.04:
                self.angle += random.uniform(-1, 1)
            nx = self.x + math.cos(self.angle) * self.speed
            ny = self.y + math.sin(self.angle) * self.speed
            if MAP[int(self.y)][int(nx)] == 0: self.x = nx
            if MAP[int(ny)][int(self.x)] == 0: self.y = ny

def main():
    username = "Player"
    selected_team = "Pigeons"
    menu = True
    input_focus = False
    box_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 50, 200, 36)

    # Make mouse cursor normal and visible for aiming
    pygame.mouse.set_visible(True)

    while menu:
        screen.fill(DARK_GRAY)
        title = large_font.render("cs: gu (Pigeon Offensive - Tactical Overhead)", True, WHITE)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//5))

        pygame.draw.rect(screen, WHITE if input_focus else BLACK, box_rect, 2)
        name_txt = font.render(username, True, WHITE)
        screen.blit(name_txt, (box_rect.x + 10, box_rect.y + 6))
        
        lbl = font.render("Click box to type Username:", True, WHITE)
        screen.blit(lbl, (box_rect.x, box_rect.y - 25))

        p_btn = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 + 30, 100, 40)
        h_btn = pygame.Rect(WIDTH//2 + 20, HEIGHT//2 + 30, 100, 40)
        pygame.draw.rect(screen, WHITE if selected_team == "Pigeons" else BLACK, p_btn)
        pygame.draw.rect(screen, BLUE if selected_team == "Humans" else BLACK, h_btn)
        
        screen.blit(font.render("Pigeons", True, BLACK if selected_team == "Pigeons" else WHITE), (p_btn.x + 15, p_btn.y + 8))
        screen.blit(font.render("Humans", True, WHITE if selected_team == "Pigeons" else BLACK), (h_btn.x + 20, h_btn.y + 8))

        screen.blit(font.render("Press ENTER to Join Battle", True, GREEN), (WIDTH//2 - 110, HEIGHT//2 + 110))

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                input_focus = box_rect.collidepoint(event.pos)
                if p_btn.collidepoint(event.pos): selected_team = "Pigeons"
                if h_btn.collidepoint(event.pos): selected_team = "Humans"
            if event.type == pygame.KEYDOWN:
                if input_focus:
                    if event.key == pygame.K_BACKSPACE: username = username[:-1]
                    elif event.key == pygame.K_RETURN: input_focus = False
                    elif len(username) < 12: username += event.unicode
                else:
                    if event.key == pygame.K_RETURN: menu = False

        pygame.display.flip()
        clock.tick(FPS)

    player = Entity(1.5, 1.5, selected_team, username, is_bot=False)
    bots = []
    shot_tracers = []
    
    for i, name in enumerate(PIGEON_BOTS):
        bots.append(Entity(14.5, 14.5 - i, "Pigeons", name))
    for i, name in enumerate(HUMAN_BOTS):
        bots.append(Entity(14.5 - i, 1.5, "Humans", name))

    pygame.event.set_grab(True)
    p_cooldown = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()

        # --- ADVANCED MOUSE-AIM SECTOR ---
        mx, my = pygame.mouse.get_pos()
        # Direct angular tracking relative to screen center point where player is anchored
        player.angle = math.atan2(my - HALF_HEIGHT, mx - HALF_WIDTH)

        if not player.is_dead:
            keys = pygame.key.get_pressed()
            mouse_buttons = pygame.mouse.get_pressed()
            move_speed = 0.07
            dx, dy = 0, 0
            
            # Move with W/S or Hold RIGHT MOUSE BUTTON to drive toward cursor position
            if keys[pygame.K_w] or mouse_buttons[2]: 
                dx += math.cos(player.angle) * move_speed
                dy += math.sin(player.angle) * move_speed
            if keys[pygame.K_s]: 
                dx -= math.cos(player.angle) * move_speed
                dy -= math.sin(player.angle) * move_speed
            if keys[pygame.K_a]: 
                dx += math.cos(player.angle - math.pi/2) * move_speed
                dy += math.sin(player.angle - math.pi/2) * move_speed
            if keys[pygame.K_d]: 
                dx += math.cos(player.angle + math.pi/2) * move_speed
                dy += math.sin(player.angle + math.pi/2) * move_speed
                
            if MAP[int(player.y)][int(player.x + dx * 1.4)] == 0: player.x += dx
            if MAP[int(player.y + dy * 1.4)][int(player.x)] == 0: player.y += dy

            # Shooting Engine (Spacebar or LEFT CLICK)
            if p_cooldown > 0: p_cooldown -= 1
            if keys[pygame.K_SPACE] or mouse_buttons[0]:
                if p_cooldown == 0:
                    p_cooldown = 12
                    
                    # Calculate terminal line range distance vector
                    max_range_x = player.x + math.cos(player.angle) * 15
                    max_range_y = player.y + math.sin(player.angle) * 15
                    
                    # Intercept geometry layer boundaries first
                    is_wall_hit, final_bullet_x, final_bullet_y = check_bullet_trajectory(player.x, player.y, max_range_x, max_range_y)
                    
                    hit_target = None
                    closest_hit_dist = math.hypot(final_bullet_x - player.x, final_bullet_y - player.y)
                    
                    for bot in bots:
                        if bot.team != player.team and not bot.is_dead:
                            # Verify if target lies within narrow ray radius line segment path
                            bx, by = bot.x - player.x, bot.y - player.y
                            b_dist = math.hypot(bx, by)
                            
                            if b_dist < closest_hit_dist:
                                b_ang = math.atan2(by, bx)
                                rel_ang = (b_ang - player.angle + math.pi) % (2 * math.pi) - math.pi
                                
                                # Target intercept width bounding verification
                                if abs(rel_ang) < 0.18:
                                    closest_hit_dist = b_dist
                                    hit_target = bot
                                    
                    if hit_target:
                        # Recalculate precision impact coordinates on target structure
                        final_bullet_x, final_bullet_y = hit_target.x, hit_target.y
                        hit_target.take_damage(35, player.name)
                        
                    shot_tracers.append(((player.x, player.y), (final_bullet_x, final_bullet_y), pygame.time.get_ticks() + 100))

        for bot in bots: bot.update(player, bots, shot_tracers)
        if player.is_dead and pygame.time.get_ticks() - player.death_time > 4000:
            player.respawn()

        # Camera frame adjustment matrices relative to player coordinates
        cam_offset_x = HALF_WIDTH - player.x * TILE_SIZE
        cam_offset_y = HALF_HEIGHT - player.y * TILE_SIZE

        screen.fill(BLACK)

        # Draw Grid Corridors
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                tile_type = MAP[y][x]
                sx = x * TILE_SIZE + cam_offset_x
                sy = y * TILE_SIZE + cam_offset_y
                
                if -TILE_SIZE < sx < WIDTH and -TILE_SIZE < sy < HEIGHT:
                    if tile_type == 1 and human_texture:
                        screen.blit(pygame.transform.scale(human_texture, (TILE_SIZE, TILE_SIZE)), (sx, sy))
                    elif tile_type == 2 and pigeon_texture:
                        screen.blit(pygame.transform.scale(pigeon_texture, (TILE_SIZE, TILE_SIZE)), (sx, sy))
                    elif tile_type == 0:
                        pygame.draw.rect(screen, FLOOR_GRAY, (sx, sy, TILE_SIZE, TILE_SIZE))
                    else:
                        fallback_color = BLUE if tile_type == 1 else WHITE
                        pygame.draw.rect(screen, fallback_color, (sx, sy, TILE_SIZE, TILE_SIZE))
                    
                    pygame.draw.rect(screen, GRID_LINE, (sx, sy, TILE_SIZE, TILE_SIZE), 1)

        # Draw Clean Bullet Tracers (Blocked instantly by structural wall nodes)
        now = pygame.time.get_ticks()
        shot_tracers = [t for t in shot_tracers if t[2] > now]
        for start, end, _ in shot_tracers:
            line_start = (start[0] * TILE_SIZE + cam_offset_x, start[1] * TILE_SIZE + cam_offset_y)
            line_end = (end[0] * TILE_SIZE + cam_offset_x, end[1] * TILE_SIZE + cam_offset_y)
            pygame.draw.line(screen, YELLOW, line_start, line_end, 3)

        # Draw Models (Dynamic Procedural Rendering System if JPEG files are absent)
        render_entities = bots + ([player] if not player.is_dead else [])
        for ent in render_entities:
            ex = ent.x * TILE_SIZE + cam_offset_x
            ey = ent.y * TILE_SIZE + cam_offset_y
            
            ent_size = int(TILE_SIZE * 0.55)
            radius = ent_size // 2
            base_color = BLUE if ent.team == "Humans" else WHITE
            active_tex = human_texture if ent.team == "Humans" else pigeon_texture
            
            if active_tex:
                tex_scaled = pygame.transform.scale(active_tex, (ent_size, ent_size))
                rotated_tex = pygame.transform.rotate(tex_scaled, -math.degrees(ent.angle))
                tex_rect = rotated_tex.get_rect(center=(ex, ey))
                screen.blit(rotated_tex, tex_rect.topleft)
            else:
                # ADVANCED PROCEDURAL 3D TOKEN MODEL FALLBACK
                # Draw main structural model body base
                pygame.draw.circle(screen, base_color, (int(ex), int(ey)), radius)
                # Draw head layer structure node
                pygame.draw.circle(screen, DARK_GRAY, (int(ex), int(ey)), int(radius * 0.6))
                # Draw tactical front weapon barrel component showing angle explicitly
                barrel_x = ex + math.cos(ent.angle) * radius
                barrel_y = ey + math.sin(ent.angle) * radius
                pygame.draw.line(screen, YELLOW if ent == player else BLACK, (ex, ey), (barrel_x, barrel_y), 5)
                
            # Laser Target Sights Pointer lines
            sight_x = ex + math.cos(ent.angle) * (radius + 15)
            sight_y = ey + math.sin(ent.angle) * (radius + 15)
            pygame.draw.line(screen, GREEN if ent.team == player.team else RED, (ex, ey), (sight_x, sight_y), 2)

            # Health Header Tags
            tag_color = GREEN if ent.team == player.team else RED
            lbl = font.render(f"YOU [{ent.health}]" if ent == player else f"{ent.name} [{ent.health}]", True, tag_color)
            screen.blit(lbl, (ex - lbl.get_width() // 2, ey - radius - 22))

        # Core Interface Overlays
        hp_color = GREEN if player.health > 40 else RED
        screen.blit(large_font.render(f"HP: {player.health}", True, hp_color), (30, HEIGHT - 70))
        screen.blit(font.render(f"TEAM: {player.team.upper()} (Aim: Mouse | Drive: Right-Click or W)", True, WHITE), (30, HEIGHT - 110))
        
        if player.is_dead:
            screen.blit(large_font.render("WIPED OUT! RESPAWNING...", True, RED), (HALF_WIDTH - 200, HALF_HEIGHT))

        kill_feed.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()