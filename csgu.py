import pygame
import math
import random
import sys
import os

# Initialize Pygame Core Systems
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
font = pygame.font.Font(None, 24)
large_font = pygame.font.Font(None, 54)

# Core Palette
WHITE = (240, 240, 240)
BLACK = (12, 12, 15)
DARK_GRAY = (30, 30, 35)
FLOOR_GRAY = (45, 45, 50)
GRID_LINE = (38, 38, 42)
RED = (255, 60, 60)
GREEN = (60, 255, 60)
BLUE = (50, 120, 255)
YELLOW = (255, 225, 0)

# Clean, Solid Wall Colors (No image textures applied here)
WALL_HUMAN_BG = (25, 40, 70)
WALL_HUMAN_BORDER = (40, 90, 200)
WALL_PIGEON_BG = (70, 70, 75)
WALL_PIGEON_BORDER = (200, 200, 205)

# --- STRICT PLAYER IMAGE DIRECTORY LOCATOR ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

print("\n" + "="*60)
print(f"DEBUG: Checking for player textures in:\n{SCRIPT_DIR}")
print("Make sure '1111.jpg' (Humans) and '2222.jpeg' (Pigeons) are there!")
print("="*60 + "\n")

human_path = os.path.join(SCRIPT_DIR, "1111.jpg")
pigeon_path = os.path.join(SCRIPT_DIR, "2222.jpeg")

# Fallback Generator ONLY for players if files aren't found yet
def create_fallback_surface(color, text):
    surf = pygame.Surface((128, 128), pygame.SRCALPHA)
    pygame.draw.circle(surf, color, (64, 64), 60)
    pygame.draw.circle(surf, DARK_GRAY, (64, 64), 45)
    txt = font.render(text, True, WHITE if color != WHITE else BLACK)
    surf.blit(txt, (64 - txt.get_width()//2, 64 - txt.get_height()//2))
    return surf

# Load your actual player images natively
try:
    if os.path.exists(human_path):
        human_player_texture = pygame.image.load(human_path).convert_alpha()
        print("-> SUCCESS: Loaded 1111.jpg for Humans")
    else:
        print("-> WARNING: 1111.jpg not found, using circular backup token.")
        human_player_texture = create_fallback_surface(BLUE, "1111")
except Exception as e:
    print(f"-> ERROR loading 1111.jpg: {e}")
    human_player_texture = create_fallback_surface(BLUE, "1111")

try:
    if os.path.exists(pigeon_path):
        pigeon_player_texture = pygame.image.load(pigeon_path).convert_alpha()
        print("-> SUCCESS: Loaded 2222.jpeg for Pigeons")
    else:
        print("-> WARNING: 2222.jpeg not found, using circular backup token.")
        pigeon_player_texture = create_fallback_surface(WHITE, "2222")
except Exception as e:
    print(f"-> ERROR loading 2222.jpeg: {e}")
    pigeon_player_texture = create_fallback_surface(WHITE, "2222")


# ARENA GAMEPLAY MAP (0 = Floor, 1 = Solid Human Wall, 2 = Solid Pigeon Wall)
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
TILE_SIZE = 95 

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

def check_bullet_trajectory(x1, y1, x2, y2):
    """Traces physics raycast line. Breaks bullet lines immediately on solid wall structures."""
    distance = math.hypot(x2 - x1, y2 - y1)
    steps = int(distance * 40) + 1  
    for i in range(steps):
        percent = i / steps
        cx = x1 + (x2 - x1) * percent
        cy = y1 + (y2 - y1) * percent
        if 0 <= cx < MAP_SIZE and 0 <= cy < MAP_SIZE:
            if MAP[int(cy)][int(cx)] > 0:
                return True, cx, cy
        else:
            return True, cx, cy
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
            if pygame.time.get_ticks() - self.death_time > 3000: self.respawn()
            return

        if self.cooldown > 0: self.cooldown -= 1
        target = None
        closest_dist = 10.0

        if player.team != self.team and not player.is_dead:
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
                self.cooldown = 45
                obstructed, fx, fy = check_bullet_trajectory(self.x, self.y, target.x, target.y)
                shot_tracers.append(((self.x, self.y), (fx, fy), pygame.time.get_ticks() + 80))
                if not obstructed: target.take_damage(10, self.name)
        else:
            if random.random() < 0.04: self.angle += random.uniform(-1, 1)
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

    pygame.mouse.set_visible(True)

    while menu:
        screen.fill(DARK_GRAY)
        title = large_font.render("cs: gu - Dynamic Player Textures Loaded", True, WHITE)
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
    
    for i, name in enumerate(PIGEON_BOTS): bots.append(Entity(14.5, 14.5 - i, "Pigeons", name))
    for i, name in enumerate(HUMAN_BOTS): bots.append(Entity(14.5 - i, 1.5, "Humans", name))

    pygame.event.set_grab(True)
    p_cooldown = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()

        # Handle mouse tracking look parameters
        mx, my = pygame.mouse.get_pos()
        player.angle = math.atan2(my - HALF_HEIGHT, mx - HALF_WIDTH)

        if not player.is_dead:
            keys = pygame.key.get_pressed()
            mouse_buttons = pygame.mouse.get_pressed()
            move_speed = 0.07
            dx, dy = 0, 0
            
            # Steering engine controls: WASD or hold down Right Mouse Button to slide towards crosshair
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

            # Shooting Engine (Left Click or Spacebar)
            if p_cooldown > 0: p_cooldown -= 1
            if keys[pygame.K_SPACE] or mouse_buttons[0]:
                if p_cooldown == 0:
                    p_cooldown = 12
                    max_range_x = player.x + math.cos(player.angle) * 15
                    max_range_y = player.y + math.sin(player.angle) * 15
                    
                    # Intercept wall checks
                    is_wall_hit, final_bullet_x, final_bullet_y = check_bullet_trajectory(player.x, player.y, max_range_x, max_range_y)
                    
                    hit_target = None
                    closest_hit_dist = math.hypot(final_bullet_x - player.x, final_bullet_y - player.y)
                    
                    for bot in bots:
                        if bot.team != player.team and not bot.is_dead:
                            bx, by = bot.x - player.x, bot.y - player.y
                            b_dist = math.hypot(bx, by)
                            if b_dist < closest_hit_dist:
                                b_ang = math.atan2(by, bx)
                                rel_ang = (b_ang - player.angle + math.pi) % (2 * math.pi) - math.pi
                                if abs(rel_ang) < 0.18:
                                    closest_hit_dist = b_dist
                                    hit_target = bot
                                    
                    if hit_target:
                        final_bullet_x, final_bullet_y = hit_target.x, hit_target.y
                        hit_target.take_damage(35, player.name)
                        
                    shot_tracers.append(((player.x, player.y), (final_bullet_x, final_bullet_y), pygame.time.get_ticks() + 100))

        for bot in bots: bot.update(player, bots, shot_tracers)
        if player.is_dead and pygame.time.get_ticks() - player.death_time > 4000: player.respawn()

        # Update Top-Down Anchor Camera offsets
        cam_offset_x = HALF_WIDTH - player.x * TILE_SIZE
        cam_offset_y = HALF_HEIGHT - player.y * TILE_SIZE

        screen.fill(BLACK)

        # Draw Clean, Highly Readable Solid Architectural Walls (No image textures applied here!)
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                tile_type = MAP[y][x]
                sx = x * TILE_SIZE + cam_offset_x
                sy = y * TILE_SIZE + cam_offset_y
                
                if -TILE_SIZE < sx < WIDTH and -TILE_SIZE < sy < HEIGHT:
                    if tile_type == 1: # Clean Solid Human Wall Block
                        pygame.draw.rect(screen, WALL_HUMAN_BG, (sx, sy, TILE_SIZE, TILE_SIZE))
                        pygame.draw.rect(screen, WALL_HUMAN_BORDER, (sx, sy, TILE_SIZE, TILE_SIZE), 4)
                    elif tile_type == 2: # Clean Solid Pigeon Wall Block
                        pygame.draw.rect(screen, WALL_PIGEON_BG, (sx, sy, TILE_SIZE, TILE_SIZE))
                        pygame.draw.rect(screen, WALL_PIGEON_BORDER, (sx, sy, TILE_SIZE, TILE_SIZE), 4)
                    elif tile_type == 0: # Walking floor corridor
                        pygame.draw.rect(screen, FLOOR_GRAY, (sx, sy, TILE_SIZE, TILE_SIZE))
                    
                    pygame.draw.rect(screen, GRID_LINE, (sx, sy, TILE_SIZE, TILE_SIZE), 1)

        # Draw Laser Gun Tracer Trails
        now = pygame.time.get_ticks()
        shot_tracers = [t for t in shot_tracers if t[2] > now]
        for start, end, _ in shot_tracers:
            line_start = (start[0] * TILE_SIZE + cam_offset_x, start[1] * TILE_SIZE + cam_offset_y)
            line_end = (end[0] * TILE_SIZE + cam_offset_x, end[1] * TILE_SIZE + cam_offset_y)
            pygame.draw.line(screen, YELLOW, line_start, line_end, 3)

        # Draw Spinning Player & Bot Tokens utilizing your actual image textures (1111.jpg / 2222.jpeg)
        render_entities = bots + ([player] if not player.is_dead else [])
        for ent in render_entities:
            ex = ent.x * TILE_SIZE + cam_offset_x
            ey = ent.y * TILE_SIZE + cam_offset_y
            
            ent_size = int(TILE_SIZE * 0.65)
            active_tex = human_player_texture if ent.team == "Humans" else pigeon_player_texture
            
            # Form circular framing clipping mask so square image assets don't have ugly block borders
            tex_scaled = pygame.transform.scale(active_tex, (ent_size, ent_size))
            rotated_tex = pygame.transform.rotate(tex_scaled, -math.degrees(ent.angle))
            tex_rect = rotated_tex.get_rect(center=(ex, ey))
            screen.blit(rotated_tex, tex_rect.topleft)
                
            # Gun laser sight guidelines
            sight_x = ex + math.cos(ent.angle) * (ent_size // 2 + 10)
            sight_y = ey + math.sin(ent.angle) * (ent_size // 2 + 10)
            pygame.draw.line(screen, GREEN if ent.team == player.team else RED, (ex, ey), (sight_x, sight_y), 2)

            # Overhead Identification Labels layer
            tag_color = GREEN if ent.team == player.team else RED
            lbl = font.render(f"YOU [{ent.health}]" if ent == player else f"{ent.name} [{ent.health}]", True, tag_color)
            screen.blit(lbl, (ex - lbl.get_width() // 2, ey - ent_size // 2 - 22))

        # HUD Overlay Panels
        hp_color = GREEN if player.health > 40 else RED
        screen.blit(large_font.render(f"HP: {player.health}", True, hp_color), (30, HEIGHT - 70))
        screen.blit(font.render(f"TEAM: {player.team.upper()} | Aim: Move Mouse | Move: WASD or Hold Right-Click", True, WHITE), (30, HEIGHT - 110))
        
        if player.is_dead:
            wiped_text = large_font.render("WIPED OUT! RESPAWNING...", True, RED)
            screen.blit(wiped_text, (HALF_WIDTH - wiped_text.get_width()//2, HALF_HEIGHT))

        kill_feed.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
