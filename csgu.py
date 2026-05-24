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
font = pygame.font.SysFont("Arial", 20, bold=True)
large_font = pygame.font.SysFont("Arial", 40, bold=True)

# Colors (Used for HUD and fallbacks)
WHITE = (240, 240, 240)
BLACK = (10, 10, 10)
DARK_GRAY = (40, 40, 45)
SKY_BLUE = (135, 206, 235)
FLOOR_BROWN = (80, 70, 60)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 100, 255)
YELLOW = (255, 215, 0)

# --- TEXTURE LOADING SYSTEM ---
TEXTURE_DIR = r"D:\C point\projekt\csgu"
human_texture = None
pigeon_texture = None

try:
    human_path = os.path.join(TEXTURE_DIR, "1111.jpg") # Updated to .jpg
    pigeon_path = os.path.join(TEXTURE_DIR, "2222.jpeg") # Kept as .jpeg
    
    if os.path.exists(human_path):
        human_texture = pygame.image.load(human_path).convert()
    if os.path.exists(pigeon_path):
        pigeon_texture = pygame.image.load(pigeon_path).convert()
except Exception as e:
    print(f"Texture load failed, using engine fallbacks. Error: {e}")

# STRUCTURED PATHWAYS MAP (0 = Walkable Path, 1 = Human Block, 2 = Pigeon Block)
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

FOV = math.pi / 2  # 90 Degree wide field of view
HALF_FOV = FOV / 2

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

    def update(self, player, bots):
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
            
            if self.cooldown == 0 and random.random() < 0.06:
                self.cooldown = 30
                if random.random() < 0.30:
                    target.take_damage(15, self.name)
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
        title = large_font.render("cs: gu (Pigeon Offensive)", True, WHITE)
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

    # Balanced spawning inside open pathways
    player = Entity(1.5, 1.5, selected_team, username, is_bot=False)
    bots = []
    
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
            # Smooth Mouse Aiming
            mx, my = pygame.mouse.get_rel()
            player.angle += mx * 0.003

            keys = pygame.key.get_pressed()
            move_speed = 0.06
            dx, dy = 0, 0
            
            if keys[pygame.K_w]: 
                dx += math.cos(player.angle) * move_speed
                dy += math.sin(player.angle) * move_speed
            if keys[pygame.K_s]: 
                dx -= math.cos(player.angle) * move_speed
                dy -= math.sin(player.angle) * move_speed
                
            # Wall Collision Sliding Checks
            if MAP[int(player.y)][int(player.x + dx * 1.5)] == 0: player.x += dx
            if MAP[int(player.y + dy * 1.5)][int(player.x)] == 0: player.y += dy

            if p_cooldown > 0: p_cooldown -= 1
            if keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0]:
                if p_cooldown == 0:
                    p_cooldown = 10
                    
                    hit_target = None
                    target_dist = 20.0
                    for bot in bots:
                        if bot.team != player.team and not bot.is_dead:
                            bx, by = bot.x - player.x, bot.y - player.y
                            b_dist = math.hypot(bx, by)
                            b_ang = math.atan2(by, bx)
                            rel_ang = (b_ang - player.angle + math.pi) % (2 * math.pi) - math.pi
                            
                            if abs(rel_ang) < 0.15 and b_dist < target_dist:
                                target_dist = b_dist
                                hit_target = bot
                                
                    if hit_target:
                        hit_target.take_damage(35, player.name)

        for bot in bots: bot.update(player, bots)
        if player.is_dead and pygame.time.get_ticks() - player.death_time > 4000:
            player.respawn()

        # Render Environment Buffers
        screen.fill(SKY_BLUE)
        pygame.draw.rect(screen, FLOOR_BROWN, (0, HALF_HEIGHT, WIDTH, HALF_HEIGHT))

        # --- THIRD PERSON CAMERA OFFSET SYSTEM ---
        # The camera handles calculations 1.5 blocks directly behind the player's vector orientation
        cam_dist = 1.5
        cam_x = player.x - math.cos(player.angle) * cam_dist
        cam_y = player.y - math.sin(player.angle) * cam_dist
        
        # Keep camera bounded smoothly inside pathway cells
        if MAP[int(cam_y)][int(cam_x)] != 0:
            cam_x, cam_y = player.x, player.y

        # Render Textured Walls relative to Camera Matrix
        num_rays = 120
        ray_w = WIDTH // num_rays
        start_ang = player.angle - HALF_FOV
        
        for r in range(num_rays):
            rang = start_ang + (r * FOV / num_rays)
            cos_r, sin_r = math.cos(rang), math.sin(rang)
            
            for d in range(1, 300):
                tx, ty = cam_x + (d * 0.06) * cos_r, cam_y + (d * 0.06) * sin_r
                if int(ty) >= MAP_SIZE or int(tx) >= MAP_SIZE or int(ty) < 0 or int(tx) < 0:
                    break
                wall_type = MAP[int(ty)][int(tx)]
                
                if wall_type > 0:
                    dist = (d * 0.06) * math.cos(rang - player.angle)
                    wall_h = min(int((40 * HALF_WIDTH / (dist + 0.001)) * 0.5), HEIGHT)
                    render_y = HALF_HEIGHT - wall_h // 2
                    
                    active_tex = human_texture if wall_type == 1 else pigeon_texture
                    if active_tex:
                        hit_x = tx % 1.0 if cos_r > 0 else (1.0 - (tx % 1.0))
                        if abs(ty % 1.0) > abs(tx % 1.0):
                            hit_x = ty % 1.0 if sin_r > 0 else (1.0 - (ty % 1.0))
                        
                        tex_x = int(hit_x * active_tex.get_width()) % active_tex.get_width()
                        slice_surf = pygame.Surface((1, active_tex.get_height()))
                        slice_surf.blit(active_tex, (0, 0), (tex_x, 0, 1, active_tex.get_height()))
                        
                        shade = max(30, int(255 / (1 + dist * dist * 0.02)))
                        shadow = pygame.Surface((1, active_tex.get_height()))
                        shadow.fill((shade, shade, shade))
                        slice_surf.blit(shadow, (0, 0), special_flags=pygame.BLEND_MULT)
                        
                        slice_scaled = pygame.transform.scale(slice_surf, (ray_w, wall_h))
                        screen.blit(slice_scaled, (r * ray_w, render_y))
                    else:
                        base_color = BLUE if wall_type == 1 else WHITE
                        shade = max(30, int(180 / (1 + dist * dist * 0.02)))
                        fallback_color = tuple(int(c * (shade / 255)) for c in base_color)
                        pygame.draw.rect(screen, fallback_color, (r * ray_w, render_y, ray_w, wall_h))
                    break

        # Collect Sprites for Rendering (Including Player Model for Third-Person View)
        sprites = []
        render_entities = bots + ([player] if not player.is_dead else [])
        
        for ent in render_entities:
            bx, by = ent.x - cam_x, ent.y - cam_y
            dist = math.hypot(bx, by)
            if dist < 0.1: continue
            
            b_ang = math.atan2(by, bx)
            rel_ang = (b_ang - player.angle + math.pi) % (2 * math.pi) - math.pi
            
            if abs(rel_ang) < HALF_FOV + 0.5:
                sprites.append((dist, rel_ang, ent))

        sprites.sort(key=lambda x: x[0], reverse=True)

        # Render Entities
        for dist, rel_ang, ent in sprites:
            proj_h = min(int((40 * HALF_WIDTH / dist) * 0.5), HEIGHT)
            sx = int(HALF_WIDTH + math.tan(rel_ang) * (HALF_WIDTH / math.tan(HALF_FOV)))
            sy = HALF_HEIGHT
            
            w_size = proj_h // 2
            h_size = proj_h
            render_y = sy - h_size // 2
            
            active_tex = human_texture if ent.team == "Humans" else pigeon_texture
            if active_tex:
                tex_scaled = pygame.transform.scale(active_tex, (w_size, h_size))
                shade = max(40, int(255 / (1 + dist * dist * 0.02)))
                shadow = pygame.Surface((w_size, h_size))
                shadow.fill((shade, shade, shade))
                tex_scaled.blit(shadow, (0, 0), special_flags=pygame.BLEND_MULT)
                
                screen.blit(tex_scaled, (sx - w_size // 2, render_y))
            else:
                if ent.team == "Humans":
                    pygame.draw.rect(screen, BLUE, (sx - w_size // 2, render_y, w_size, h_size))
                else:
                    pygame.draw.rect(screen, WHITE, (sx - w_size // 2, render_y, w_size, h_size))

            # UI Tags
            tag_color = GREEN if ent.team == player.team else RED
            lbl = font.render(f"{ent.name} [{ent.health}]", True, tag_color)
            screen.blit(lbl, (sx - lbl.get_width() // 2, render_y - 25))

        # HUD Layer Layout
        pygame.draw.circle(screen, GREEN, (HALF_WIDTH, HALF_HEIGHT), 6, 1)
        
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