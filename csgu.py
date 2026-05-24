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

pygame.display.set_caption("cs: gu - Pigeon Offensive (Top-Down)")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20, bold=True)
large_font = pygame.font.SysFont("Arial", 40, bold=True)

# Colors
WHITE = (240, 240, 240)
BLACK = (10, 10, 10)
DARK_GRAY = (35, 35, 40)
FLOOR_GRAY = (55, 55, 60)
GRID_LINE = (45, 45, 50)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 100, 255)
YELLOW = (255, 220, 0)

# --- TEXTURE LOADING SYSTEM ---
TEXTURE_DIR = r"D:\C point\projekt\csgu"
human_texture = None
pigeon_texture = None

try:
    human_path = os.path.join(TEXTURE_DIR, "1111.jpg")
    pigeon_path = os.path.join(TEXTURE_DIR, "2222.jpeg")
    
    if os.path.exists(human_path):
        human_texture = pygame.image.load(human_path).convert_with_alpha()
    if os.path.exists(pigeon_path):
        pigeon_texture = pygame.image.load(pigeon_path).convert_with_alpha()
except Exception as e:
    print(f"Texture load failed, using engine fallbacks. Error: {e}")

# PATHWAYS MAP (0 = Path, 1 = Human Block, 2 = Pigeon Block)
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
TILE_SIZE = 85  # Scale of grid segments seen from above

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
        closest_dist = 12.0

        if player.team != self.team and not player.is_dead:
            closest_dist = math.hypot(player.x - self.x, player.y - self.y)
            target = player

        for bot in bots:
            if bot != self and bot.team != self.team and not bot.is_dead:
                d = math.hypot(bot.x - self.x, bot.y - self.y)
                if d < closest_dist:
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
                self.cooldown = 35
                if random.random() < 0.25:
                    target.take_damage(12, self.name)
                    shot_tracers.append(((self.x, self.y), (target.x, target.y), pygame.time.get_ticks() + 80))
                else:
                    ex = self.x + math.cos(self.angle) * 4
                    ey = self.y + math.sin(self.angle) * 4
                    shot_tracers.append(((self.x, self.y), (ex, ey), pygame.time.get_ticks() + 80))
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

    while menu:
        screen.fill(DARK_GRAY)
        title = large_font.render("cs: gu (Pigeon Offensive - Overhead Mode)", True, WHITE)
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
    shot_tracers = [] # Holds dynamic gun rails
    
    for i, name in enumerate(PIGEON_BOTS):
        bots.append(Entity(14.5, 14.5 - i, "Pigeons", name))
    for i, name in enumerate(HUMAN_BOTS):
        bots.append(Entity(14.5 - i, 1.5, "Humans", name))

    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    
    p_cooldown = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()

        if not player.is_dead:
            # Mouse rotation changes your top-down vector angle cleanly
            mx, my = pygame.mouse.get_rel()
            player.angle += mx * 0.004

            keys = pygame.key.get_pressed()
            move_speed = 0.07
            dx, dy = 0, 0
            
            if keys[pygame.K_w]: 
                dx += math.cos(player.angle) * move_speed
                dy += math.sin(player.angle) * move_speed
            if keys[pygame.K_s]: 
                dx -= math.cos(player.angle) * move_speed
                dy -= math.sin(player.angle) * move_speed
                
            # Grid collision containment boundaries
            if MAP[int(player.y)][int(player.x + dx * 1.4)] == 0: player.x += dx
            if MAP[int(player.y + dy * 1.4)][int(player.x)] == 0: player.y += dy

            if p_cooldown > 0: p_cooldown -= 1
            if keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0]:
                if p_cooldown == 0:
                    p_cooldown = 12
                    
                    hit_target = None
                    target_dist = 15.0
                    for bot in bots:
                        if bot.team != player.team and not bot.is_dead:
                            bx, by = bot.x - player.x, bot.y - player.y
                            b_dist = math.hypot(bx, by)
                            b_ang = math.atan2(by, bx)
                            rel_ang = (b_ang - player.angle + math.pi) % (2 * math.pi) - math.pi
                            
                            if abs(rel_ang) < 0.20 and b_dist < target_dist:
                                target_dist = b_dist
                                hit_target = bot
                                
                    if hit_target:
                        hit_target.take_damage(35, player.name)
                        shot_tracers.append(((player.x, player.y), (hit_target.x, hit_target.y), pygame.time.get_ticks() + 100))
                    else:
                        # Draw missed shot tracer line out into distance
                        ex = player.x + math.cos(player.angle) * 8
                        ey = player.y + math.sin(player.angle) * 8
                        shot_tracers.append(((player.x, player.y), (ex, ey), pygame.time.get_ticks() + 100))

        # Update non-playable units
        for bot in bots: bot.update(player, bots, shot_tracers)
        if player.is_dead and pygame.time.get_ticks() - player.death_time > 4000:
            player.respawn()

        # --- TOP DOWN MATRIX SCROLLING VIEW CAMERA ---
        # The screen camera stays locked on the exact center coordinates of the player model
        cam_offset_x = HALF_WIDTH - player.x * TILE_SIZE
        cam_offset_y = HALF_HEIGHT - player.y * TILE_SIZE

        # Clean background buffer paint
        screen.fill(BLACK)

        # Draw Grid Matrix Layout from Sky Point View
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                tile_type = MAP[y][x]
                sx = x * TILE_SIZE + cam_offset_x
                sy = y * TILE_SIZE + cam_offset_y
                
                # Culling optimization (only render tiles visible on physical monitor screen)
                if -TILE_SIZE < sx < WIDTH and -TILE_SIZE < sy < HEIGHT:
                    if tile_type == 1 and human_texture:
                        tex_scaled = pygame.transform.scale(human_texture, (TILE_SIZE, TILE_SIZE))
                        screen.blit(tex_scaled, (sx, sy))
                    elif tile_type == 2 and pigeon_texture:
                        tex_scaled = pygame.transform.scale(pigeon_texture, (TILE_SIZE, TILE_SIZE))
                        screen.blit(tex_scaled, (sx, sy))
                    elif tile_type == 0:
                        pygame.draw.rect(screen, FLOOR_GRAY, (sx, sy, TILE_SIZE, TILE_SIZE))
                    else:
                        fallback_color = BLUE if tile_type == 1 else WHITE
                        pygame.draw.rect(screen, fallback_color, (sx, sy, TILE_SIZE, TILE_SIZE))
                    
                    # Tactical structural lines mapping corridors cleanly
                    pygame.draw.rect(screen, GRID_LINE, (sx, sy, TILE_SIZE, TILE_SIZE), 1)

        # Draw Active Gunfire Laser Tracers
        now = pygame.time.get_ticks()
        shot_tracers = [t for t in shot_tracers if t[2] > now]
        for start, end, _ in shot_tracers:
            line_start = (start[0] * TILE_SIZE + cam_offset_x, start[1] * TILE_SIZE + cam_offset_y)
            line_end = (end[0] * TILE_SIZE + cam_offset_x, end[1] * TILE_SIZE + cam_offset_y)
            pygame.draw.line(screen, YELLOW, line_start, line_end, 3)

        # Draw All Moving Entity Sprites Rotated Overhead
        render_entities = bots + ([player] if not player.is_dead else [])
        for ent in render_entities:
            ex = ent.x * TILE_SIZE + cam_offset_x
            ey = ent.y * TILE_SIZE + cam_offset_y
            
            ent_size = int(TILE_SIZE * 0.65)
            active_tex = human_texture if ent.team == "Humans" else pigeon_texture
            
            if active_tex:
                # Scale down cleanly, then rotate based on directional orientation vector
                tex_scaled = pygame.transform.scale(active_tex, (ent_size, ent_size))
                # Note: Pygame rotates counter-clockwise, so we negate degrees for accurate mouse sync
                deg_angle = -math.degrees(ent.angle)
                rotated_tex = pygame.transform.rotate(tex_scaled, deg_angle)
                tex_rect = rotated_tex.get_rect(center=(ex, ey))
                screen.blit(rotated_tex, tex_rect.topleft)
            else:
                fallback_color = BLUE if ent.team == "Humans" else WHITE
                pygame.draw.circle(screen, fallback_color, (int(ex), int(ey)), ent_size // 2)
                
            # Aiming Sight Vector line indicators for tactical map readability
            sight_len = ent_size // 2 + 15
            lx = ex + math.cos(ent.angle) * sight_len
            ly = ey + math.sin(ent.angle) * sight_len
            pygame.draw.line(screen, RED if ent.team != player.team else GREEN, (ex, ey), (lx, ly), 2)

            # Identification Header Labels
            tag_color = GREEN if ent.team == player.team else RED
            if ent == player:
                lbl = font.render(f"YOU [{ent.health}]", True, GREEN)
            else:
                lbl = font.render(f"{ent.name} [{ent.health}]", True, tag_color)
            screen.blit(lbl, (ex - lbl.get_width() // 2, ey - ent_size // 2 - 22))

        # HUD Layer Overlay
        # Simple laser pointer dots centered on screen overlay
        if not player.is_dead:
            pygame.draw.circle(screen, GREEN, (HALF_WIDTH, HALF_HEIGHT), 4)

        hp_color = GREEN if player.health > 40 else RED
        screen.blit(large_font.render(f"HP: {player.health}", True, hp_color), (30, HEIGHT - 70))
        screen.blit(font.render(f"TEAM: {player.team.upper()}", True, WHITE), (30, HEIGHT - 110))
        
        if player.is_dead:
            screen.blit(large_font.render("WIPED OUT! RESPAWNING...", True, RED), (HALF_WIDTH - 200, HALF_HEIGHT))

        kill_feed.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()