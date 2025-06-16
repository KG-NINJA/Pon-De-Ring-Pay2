import pygame
import random
import math # Needed for atan2 and vector math

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512) # Initialize the mixer

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Helicopter Game"

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0) # Player, Enemy Bullets
GREEN = (0, 255, 0) # Health bars, Stage Clear
YELLOW = (255, 255, 0) # Vulcan Bullets
ORANGE = (255, 165, 0) # Missiles
BROWN = (139, 69, 19) # Warehouses
GRAY = (128, 128, 128) # AA Guns, Battleship
DARK_GRAY = (100, 100, 100) # AA Gun color
VERY_DARK_GRAY = (50, 50, 50) # Battleship main color
LIGHT_RED = (255, 100, 100) # Player hit flash
BLUE = (0, 0, 255) # Fighter Jets


# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(SCREEN_TITLE)

# Game clock
clock = pygame.time.Clock()
FPS = 60

# Difficulty Scaling Parameters
BASE_WAREHOUSE_HEALTH = 100
WAREHOUSE_HEALTH_INCREASE_PER_STAGE = 20
BASE_AAGUN_HEALTH = 50
AAGUN_HEALTH_INCREASE_PER_STAGE = 10
BASE_AAGUN_FIRE_RATE_MS = 2000
AAGUN_FIRE_RATE_DECREASE_PER_STAGE = 100
MIN_AAGUN_FIRE_RATE_MS = 800
BASE_FIGHTER_HEALTH = 75
FIGHTER_HEALTH_INCREASE_PER_STAGE = 15
BASE_BATTLESHIP_HEALTH = 800
BATTLESHIP_HEALTH_INCREASE_PER_STAGE = 100

# Sound Loading Helper
def load_sound(name, default_volume=1.0):
    fullname = f"assets/sounds/{name}.wav.txt" # Load the .txt file
    try:
        # In a real scenario, this would be pygame.mixer.Sound(fullname_wav)
        # For simulation, we're just checking if the .txt placeholder exists
        # and creating a dummy sound object or returning None.
        with open(fullname, 'r') as f:
            description = f.read()
            if description:
                class DummySound: # Simulate Pygame Sound object for this task
                    def __init__(self, desc): self.description = desc; self.vol = default_volume
                    def play(self, loops=0): pass # print(f"Simulated play: {self.description[:30]} at vol {self.vol}")
                    def set_volume(self, vol): self.vol = vol # Store volume

                sound = DummySound(description)
                sound.set_volume(default_volume) # Apply default volume
                return sound
            else:
                print(f"Sound placeholder exists but is empty: {fullname}")
                return None
    except IOError:
        print(f"Cannot load sound placeholder: {fullname}")
        return None

# Load All Sounds
sound_vulcan_fire = load_sound("vulcan_fire.wav.txt", 0.3) # Corrected filenames
sound_missile_fire = load_sound("missile_fire.wav.txt", 0.6)
sound_enemy_fire = load_sound("enemy_fire.wav.txt", 0.3)
sound_explosion_small = load_sound("explosion.wav.txt", 0.5)
sound_player_damage = load_sound("player_damage.wav.txt", 0.7)
sound_battleship_explosion = load_sound("battleship_explosion.wav.txt", 1.0)
sound_stage_clear = load_sound("stage_clear.wav.txt", 0.8)
sound_game_over = load_sound("game_over.wav.txt", 0.8)

# Helper to play sounds safely
def play_sound(sound_obj, loops=0): # Volume is now set at load time or per sound object
    if sound_obj and hasattr(sound_obj, 'play'):
        sound_obj.play(loops)

# Bullet Class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction_x, direction_y):
        super().__init__()
        try:
            self.image = pygame.image.load("assets/images/vulcan_bullet.png").convert_alpha()
        except pygame.error as e:
            print(f"Error loading vulcan_bullet.png: {e}")
            self.image = pygame.Surface([10, 4]) # Fallback
            self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speed = 15
        self.velocity_x = direction_x * self.speed
        self.velocity_y = direction_y * self.speed
        self.damage = 5

    def update(self):
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT or \
           self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

    def draw(self, surface):
        surface.blit(self.image, self.rect)

# Missile Class
class Missile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction_x, direction_y):
        super().__init__()
        try:
            self.image = pygame.image.load("assets/images/missile.png").convert_alpha()
        except pygame.error as e:
            print(f"Error loading missile.png: {e}")
            self.image = pygame.Surface([20, 8]) # Fallback
            self.image.fill(ORANGE)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speed = 8
        self.velocity_x = direction_x * self.speed
        self.velocity_y = direction_y * self.speed
        self.damage = 25

    def update(self):
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT or \
           self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

    def draw(self, surface):
        surface.blit(self.image, self.rect)

# Enemy Bullet Class
class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x=None, target_y=None, fixed_direction_y=-1):
        super().__init__()
        try:
            self.image = pygame.image.load("assets/images/enemy_bullet.png").convert_alpha()
        except pygame.error as e:
            print(f"Error loading enemy_bullet.png: {e}")
            self.image = pygame.Surface([8, 8]) # Fallback
            self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speed = 7
        self.damage = 10

        if target_x is not None and target_y is not None:
            direction_x = target_x - x
            direction_y = target_y - y
            magnitude = (direction_x**2 + direction_y**2)**0.5
            if magnitude > 0:
                self.velocity_x = (direction_x / magnitude) * self.speed
                self.velocity_y = (direction_y / magnitude) * self.speed
            else:
                self.velocity_x = 0
                self.velocity_y = -self.speed
        else:
            self.velocity_x = 0
            self.velocity_y = fixed_direction_y * self.speed

    def update(self):
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT or \
           self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

    def draw(self, surface):
        surface.blit(self.image, self.rect)

# Warehouse Class
class Warehouse(pygame.sprite.Sprite):
    def __init__(self, x, y, width=100, height=60, initial_health=100):
        super().__init__()
        try:
            self.image_orig = pygame.image.load("assets/images/warehouse.png").convert_alpha()
        except pygame.error as e:
            print(f"Error loading warehouse.png: {e}")
            self.image_orig = pygame.Surface([width, height])
            self.image_orig.fill(BROWN)

        self.image = self.image_orig.copy()
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        if self.image_orig.get_width() != width or self.image_orig.get_height() != height:
             self.rect.width = self.image_orig.get_width()
             self.rect.height = self.image_orig.get_height()
        self.max_health = initial_health
        self.health = self.max_health
        self.health_bar_height = 7
        self.health_bar_y_offset = 10

    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0:
            self.health = 0
        self.update_health_bar()

    def is_destroyed(self):
        return self.health <= 0

    def update_health_bar(self):
        self.image = self.image_orig.copy()
        if self.health > 0:
            health_ratio = self.health / self.max_health
            pygame.draw.rect(self.image, BLACK, (0, -self.health_bar_y_offset, self.rect.width, self.health_bar_height), 1)
            pygame.draw.rect(self.image, GREEN, (1, -self.health_bar_y_offset + 1, (self.rect.width - 2) * health_ratio, self.health_bar_height - 2))

    def draw(self, surface):
        surface.blit(self.image, (self.rect.x, self.rect.y - self.health_bar_y_offset if self.health > 0 else self.rect.y))

# Anti-Aircraft Gun (AAGun) Class
class AAGun(pygame.sprite.Sprite):
    def __init__(self, x, y, fire_rate_ms=BASE_AAGUN_FIRE_RATE_MS, initial_health=BASE_AAGUN_HEALTH):
        super().__init__()
        try:
            self.image_orig = pygame.image.load("assets/images/aagun.png").convert_alpha()
        except pygame.error as e:
            print(f"Error loading aagun.png: {e}")
            self.image_orig = pygame.Surface([30, 30])
            self.image_orig.fill(DARK_GRAY)
        self.image = self.image_orig.copy()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.fire_rate = fire_rate_ms
        self.last_shot_time = pygame.time.get_ticks() + random.randint(0, int(fire_rate_ms))
        self.max_health = initial_health
        self.health = self.max_health
        self.health_bar_height = 5
        self.health_bar_y_offset = 8
        self.enemy_bullets_group = None

    def set_enemy_bullets_group(self, group):
        self.enemy_bullets_group = group

    def update(self, player_pos):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time > self.fire_rate:
            self.last_shot_time = current_time
            if self.enemy_bullets_group is not None:
                play_sound(sound_enemy_fire)
                bullet = EnemyBullet(self.rect.centerx, self.rect.top, fixed_direction_y=-1)
                self.enemy_bullets_group.add(bullet)
        self.update_health_bar()

    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0:
            self.health = 0

    def is_destroyed(self):
        return self.health <= 0

    def update_health_bar(self):
        self.image = self.image_orig.copy()
        if self.health > 0 and self.health < self.max_health:
            health_ratio = self.health / self.max_health
            pygame.draw.rect(self.image, BLACK, (0, -self.health_bar_y_offset, self.rect.width, self.health_bar_height), 1)
            pygame.draw.rect(self.image, RED, (1, -self.health_bar_y_offset + 1, (self.rect.width - 2) * health_ratio, self.health_bar_height - 2))

    def draw(self, surface):
        surface.blit(self.image, (self.rect.x, self.rect.y - self.health_bar_y_offset if self.health > 0 and self.health < self.max_health else self.rect.y))

# Fighter Jet Class
class FighterJet(pygame.sprite.Sprite):
    def __init__(self, x, y, player_ref_for_speed, enemy_bullets_group_ref, initial_health=BASE_FIGHTER_HEALTH):
        super().__init__()
        self.size = 30
        try:
            self.original_image = pygame.image.load("assets/images/fighter_jet.png").convert_alpha()
        except pygame.error as e:
            print(f"Error loading fighter_jet.png: {e}")
            self.original_image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.polygon(self.original_image, BLUE, [(self.size, self.size // 2), (0, 0), (0, self.size -1)])
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(x,y))
        self.max_health = initial_health
        self.health = self.max_health
        self.speed = player_ref_for_speed + 1
        self.turn_speed_rad = math.radians(3)
        self.current_angle_rad = random.uniform(0, 2 * math.pi)
        self.velocity_x = math.cos(self.current_angle_rad) * self.speed
        self.velocity_y = math.sin(self.current_angle_rad) * self.speed
        self.fire_rate = 2500
        self.last_shot_time = pygame.time.get_ticks() + random.randint(0, self.fire_rate)
        self.enemy_bullets_group = enemy_bullets_group_ref
        self.health_bar_height = 5
        self.health_bar_y_offset = 10

    def update(self, player_pos):
        target_dx = player_pos[0] - self.rect.centerx
        target_dy = player_pos[1] - self.rect.centery
        angle_to_player_rad = math.atan2(target_dy, target_dx)
        angle_diff = (angle_to_player_rad - self.current_angle_rad + math.pi) % (2 * math.pi) - math.pi
        if angle_diff > self.turn_speed_rad:
            self.current_angle_rad += self.turn_speed_rad
        elif angle_diff < -self.turn_speed_rad:
            self.current_angle_rad -= self.turn_speed_rad
        else:
            self.current_angle_rad = angle_to_player_rad
        self.current_angle_rad %= (2 * math.pi)
        self.velocity_x = math.cos(self.current_angle_rad) * self.speed
        self.velocity_y = math.sin(self.current_angle_rad) * self.speed
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y
        self.image = pygame.transform.rotate(self.original_image, -math.degrees(self.current_angle_rad))
        self.rect = self.image.get_rect(center=self.rect.center)
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time > self.fire_rate:
            self.last_shot_time = current_time
            if self.enemy_bullets_group is not None:
                play_sound(sound_enemy_fire)
                bullet_dx = math.cos(self.current_angle_rad)
                bullet_dy = math.sin(self.current_angle_rad)
                spawn_x = self.rect.centerx + bullet_dx * (self.size / 2)
                spawn_y = self.rect.centery + bullet_dy * (self.size / 2)
                bullet = EnemyBullet(spawn_x, spawn_y, target_x=spawn_x + bullet_dx, target_y=spawn_y + bullet_dy)
                self.enemy_bullets_group.add(bullet)
        if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.velocity_x *= -1
            self.current_angle_rad = math.atan2(self.velocity_y, self.velocity_x)
            self.rect.left = max(0, self.rect.left)
            self.rect.right = min(SCREEN_WIDTH, self.rect.right)
        if self.rect.top < 0 or self.rect.bottom > SCREEN_HEIGHT:
            self.velocity_y *= -1
            self.current_angle_rad = math.atan2(self.velocity_y, self.velocity_x)
            self.rect.top = max(0, self.rect.top)
            self.rect.bottom = min(SCREEN_HEIGHT, self.rect.bottom)
        self.update_health_bar()

    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0:
            self.health = 0

    def is_destroyed(self):
        return self.health <= 0

    def update_health_bar(self):
        pass

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        if self.health > 0 and self.health < self.max_health:
            bar_width = self.rect.width * 0.8
            bar_height = self.health_bar_height
            bar_pos_x = self.rect.centerx - bar_width / 2
            bar_pos_y = self.rect.top - self.health_bar_y_offset - bar_height
            health_ratio = self.health / self.max_health
            pygame.draw.rect(surface, BLACK, (bar_pos_x, bar_pos_y, bar_width, bar_height), 1)
            pygame.draw.rect(surface, RED, (bar_pos_x + 1, bar_pos_y + 1, (bar_width - 2) * health_ratio, bar_height - 2))

# Battleship Class
class Battleship(pygame.sprite.Sprite):
    def __init__(self, enemy_bullets_group_ref):
        super().__init__()
        self.expected_width = SCREEN_WIDTH * 0.8
        self.expected_height = 100
        try:
            self.original_image = pygame.image.load("assets/images/battleship.png").convert_alpha()
        except pygame.error as e:
            print(f"Error loading battleship.png: {e}")
            self.original_image = pygame.Surface((self.expected_width, self.expected_height))
            self.original_image.fill(VERY_DARK_GRAY)
        self.width = self.original_image.get_width()
        self.height = self.original_image.get_height()
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(-self.width // 2, SCREEN_HEIGHT // 3))
        self.max_health = BASE_BATTLESHIP_HEALTH
        self.health = self.max_health
        self.speed = 0.5
        self.direction = 1
        self.enemy_bullets_group = enemy_bullets_group_ref
        self.is_active = False
        self.turret_positions_relative = [
            (self.width * 0.2, self.height * 0.3), (self.width * 0.5, self.height * 0.3),
            (self.width * 0.8, self.height * 0.3), (self.width * 0.35, self.height * 0.7),
            (self.width * 0.65, self.height * 0.7), ]
        self.turrets = []
        for i, pos in enumerate(self.turret_positions_relative):
            turret_size = 15
            pygame.draw.rect(self.original_image, GRAY, (pos[0] - turret_size//2, pos[1] - turret_size//2, turret_size, turret_size))
            self.turrets.append({
                'rel_pos': pos,
                'last_shot': pygame.time.get_ticks() + random.randint(0, 3000) + (i * 500),
                'fire_rate': random.randint(2800, 3500) })
        self.image = self.original_image.copy()
        self.health_bar_height = 15
        self.health_bar_y_offset = 10

    def activate(self, spawn_y_offset=SCREEN_HEIGHT // 4):
        self.rect.topleft = (-self.width, spawn_y_offset)
        self.health = self.max_health
        self.is_active = True
        self.direction = 1

    def update(self, player_pos):
        if not self.is_active: return
        self.rect.x += self.speed * self.direction
        if self.direction == 1 and self.rect.left >= SCREEN_WIDTH * 0.1:
            self.direction = 0
            pygame.time.set_timer(pygame.USEREVENT + 1, 5000, True)
        elif self.direction == -1 and self.rect.right <= SCREEN_WIDTH * 0.9:
            self.direction = 0
            pygame.time.set_timer(pygame.USEREVENT + 1, 5000, True)
        if self.rect.right > SCREEN_WIDTH + self.width /2 : self.is_active = False
        elif self.rect.left < -self.width * 1.5 : self.is_active = False
        current_time = pygame.time.get_ticks()
        for turret in self.turrets:
            if current_time - turret['last_shot'] > turret['fire_rate']:
                turret['last_shot'] = current_time
                turret_abs_x = self.rect.left + turret['rel_pos'][0]
                turret_abs_y = self.rect.top + turret['rel_pos'][1]
                target_x = player_pos[0] + random.randint(-50, 50)
                target_y = player_pos[1] + random.randint(-20, 20)
                play_sound(sound_enemy_fire)
                bullet = EnemyBullet(turret_abs_x, turret_abs_y, target_x=target_x, target_y=target_y)
                self.enemy_bullets_group.add(bullet)
                all_sprites.add(bullet)

    def take_damage(self, amount):
        if not self.is_active: return
        self.health -= amount
        if self.health < 0: self.health = 0

    def is_destroyed(self): return self.health <= 0

    def draw(self, surface):
        if not self.is_active: return
        surface.blit(self.image, self.rect)
        if self.health > 0:
            bar_width = self.width * 0.9
            bar_height = self.health_bar_height
            bar_pos_x = self.rect.centerx - bar_width / 2
            bar_pos_y = self.rect.top - self.health_bar_y_offset - bar_height
            health_ratio = self.health / self.max_health
            pygame.draw.rect(surface, BLACK, (bar_pos_x, bar_pos_y, bar_width, bar_height), 1)
            pygame.draw.rect(surface, GREEN, (bar_pos_x + 1, bar_pos_y + 1, (bar_width - 2) * health_ratio, bar_height - 2))

# Player Helicopter Class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        try:
            self.original_image = pygame.image.load("assets/images/player_helicopter.png").convert_alpha()
        except pygame.error as e:
            print(f"Error loading player_helicopter.png: {e}")
            self.original_image = pygame.Surface([50, 20])
            self.original_image.fill(RED)
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.speed = 5
        self.velocity_x = 0
        self.velocity_y = 0
        self.vulcan_bullets = pygame.sprite.Group()
        self.missiles = pygame.sprite.Group()
        self.last_vulcan_shot_time = 0
        self.vulcan_shoot_delay = 100
        self.last_missile_shot_time = 0
        self.missile_shoot_delay = 500
        self.max_health = 100
        self.health = self.max_health
        self.is_invulnerable = False
        self.invulnerability_duration = 1000
        self.last_hit_time = 0
        self.flash_duration = 100
        self.flash_timer = 0
        self.last_direction_x = 1
        self.last_direction_y = 0

    def handle_input(self, keys):
        self.velocity_x = 0; self.velocity_y = 0
        current_direction_x = 0; current_direction_y = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.velocity_x = -self.speed; current_direction_x = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.velocity_x = self.speed; current_direction_x = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]: self.velocity_y = -self.speed; current_direction_y = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: self.velocity_y = self.speed; current_direction_y = 1
        if current_direction_x != 0 or current_direction_y != 0:
            self.last_direction_x = current_direction_x
            self.last_direction_y = current_direction_y
        if self.velocity_x != 0 and self.velocity_y != 0:
            self.velocity_x /= 1.414; self.velocity_y /= 1.414
            self.last_direction_x = self.velocity_x / self.speed
            self.last_direction_y = self.velocity_y / self.speed
        if keys[pygame.K_SPACE]: self.shoot_vulcan()
        if keys[pygame.K_m]: self.shoot_missile()

    def shoot_vulcan(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_vulcan_shot_time > self.vulcan_shoot_delay:
            self.last_vulcan_shot_time = current_time
            play_sound(sound_vulcan_fire)
            proj_dx = self.last_direction_x; proj_dy = self.last_direction_y
            if proj_dx == 0 and proj_dy == 0: proj_dx = 1
            if not (abs(proj_dx)==1 and proj_dy==0) and not (abs(proj_dy)==1 and proj_dx==0) and not (proj_dx==0 and proj_dy==0):
                norm = (proj_dx**2 + proj_dy**2)**0.5
                if norm != 0: proj_dx /= norm; proj_dy /= norm
            bullet = Bullet(self.rect.centerx, self.rect.centery, proj_dx, proj_dy)
            self.vulcan_bullets.add(bullet)

    def shoot_missile(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_missile_shot_time > self.missile_shoot_delay:
            self.last_missile_shot_time = current_time
            play_sound(sound_missile_fire)
            proj_dx = self.last_direction_x; proj_dy = self.last_direction_y
            if proj_dx == 0 and proj_dy == 0: proj_dx = 1
            if not (abs(proj_dx)==1 and proj_dy==0) and not (abs(proj_dy)==1 and proj_dx==0) and not (proj_dx==0 and proj_dy==0):
                norm = (proj_dx**2 + proj_dy**2)**0.5
                if norm != 0: proj_dx /= norm; proj_dy /= norm
            missile = Missile(self.rect.centerx, self.rect.centery, proj_dx, proj_dy)
            self.missiles.add(missile)

    def update(self):
        self.rect.x += self.velocity_x; self.rect.y += self.velocity_y
        if self.is_invulnerable:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_hit_time > self.invulnerability_duration:
                self.is_invulnerable = False; self.image = self.original_image.copy()
            else:
                self.flash_timer += clock.get_time()
                if self.flash_timer > self.flash_duration:
                    self.flash_timer = 0
                    if self.image is self.original_image:
                        temp_flash_image = self.original_image.copy(); temp_flash_image.fill(LIGHT_RED); self.image = temp_flash_image
                    else: self.image = self.original_image.copy()
        else: self.image = self.original_image.copy()
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH
        if self.rect.top < 0: self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT: self.rect.bottom = SCREEN_HEIGHT
        self.vulcan_bullets.update(); self.missiles.update()

    def take_damage(self, amount):
        current_time = pygame.time.get_ticks()
        if not self.is_invulnerable:
            self.health -= amount
            play_sound(sound_player_damage)
            if self.health < 0: self.health = 0
            # print(f"Player health: {self.health}") # Removed for cleanup
            self.is_invulnerable = True; self.last_hit_time = current_time; self.flash_timer = 0

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        self.vulcan_bullets.draw(surface); self.missiles.draw(surface)
        if self.health > 0:
             pygame.draw.rect(surface, RED, (10, 10, self.max_health * 2, 20))
             pygame.draw.rect(surface, GREEN, (10, 10, self.health * 2, 20))

# Sprite Groups
all_sprites = pygame.sprite.Group()
warehouses = pygame.sprite.Group()
aa_guns = pygame.sprite.Group()
fighter_jets = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
battleship_group = pygame.sprite.GroupSingle() # For the single battleship

# Create Player
player = Player()
all_sprites.add(player)

# Predefined positions (can be adjusted or made dynamic later)
warehouse_positions = [(150, SCREEN_HEIGHT - 70), (400, SCREEN_HEIGHT - 70), (650, SCREEN_HEIGHT - 70),
                       (250, SCREEN_HEIGHT - 170), (550, SCREEN_HEIGHT - 170)]
aa_gun_positions = [(150, SCREEN_HEIGHT - 30), (400, SCREEN_HEIGHT - 30), (650, SCREEN_HEIGHT - 30)]

# Game state variables
score = 0
game_start_time = 0
current_stage = 1
BATTLESHIP_SPAWN_TIME = 300000
# BATTLESHIP_SPAWN_TIME_DEBUG = 45000 # for testing warning (45s)
BATTLESHIP_WARNING_LEAD_TIME = 30000 # 30 seconds before spawn
BATTLESHIP_WARNING_DURATION = 5000 # Display warning for 5 seconds

game_state = "get_ready" # Start with "get_ready" state
stage_clear_message_display_time = 0
STAGE_CLEAR_DURATION = 3000
GET_READY_DURATION = 2000 # 2 seconds for "Get Ready!"
get_ready_start_time = 0
battleship_warning_shown_this_stage = False
battleship_approaching_message_active = False
battleship_approaching_message_end_time = 0


# Single instance of Battleship, initially inactive
battleship = Battleship(enemy_bullets_group_ref=enemy_bullets)
battleship_group.add(battleship) # Add to its own group

def init_game_values(is_new_game_session=False):
    global game_start_time, score, current_stage, get_ready_start_time, battleship_warning_shown_this_stage, battleship_approaching_message_active
    if is_new_game_session:
        score = 0
        current_stage = 1

    game_start_time = pygame.time.get_ticks() # This is for overall stage time, including "Get Ready"
    get_ready_start_time = pygame.time.get_ticks() # Specifically for the "Get Ready" message timing
    battleship_warning_shown_this_stage = False
    battleship_approaching_message_active = False

    if battleship:
        battleship.is_active = False
        if battleship in all_sprites:
            all_sprites.remove(battleship)

def reset_stage(is_first_load=False):
    global warehouses, player, all_sprites, aa_guns, enemy_bullets, fighter_jets, current_stage, score
    if not is_first_load:
        current_stage += 1
        print(f"Advancing to Stage: {current_stage}")
    else: # For the very first load of the game session (or after game over)
        current_stage = 1
        score = 0

    init_game_values(is_new_game_session=is_first_load)

    # Clear existing sprites before repopulating for the new stage
    player.kill() # Remove old player explicitly
    for s in all_sprites: s.kill() # Clear all other sprites

    warehouses.empty(); aa_guns.empty(); fighter_jets.empty(); enemy_bullets.empty()
    # battleship_group still holds the battleship object, just inactive.

    player.__init__() # Re-initialize player state
    all_sprites.add(player)

    current_warehouse_health = BASE_WAREHOUSE_HEALTH + (current_stage - 1) * WAREHOUSE_HEALTH_INCREASE_PER_STAGE
    current_aagun_health = BASE_AAGUN_HEALTH + (current_stage - 1) * AAGUN_HEALTH_INCREASE_PER_STAGE
    current_aagun_fire_rate = max(MIN_AAGUN_FIRE_RATE_MS, BASE_AAGUN_FIRE_RATE_MS - (current_stage - 1) * AAGUN_FIRE_RATE_DECREASE_PER_STAGE)
    current_fighter_health = BASE_FIGHTER_HEALTH + (current_stage - 1) * FIGHTER_HEALTH_INCREASE_PER_STAGE
    current_battleship_max_health = BASE_BATTLESHIP_HEALTH + (current_stage - 1) * BATTLESHIP_HEALTH_INCREASE_PER_STAGE

    for pos in warehouse_positions:
        warehouse = Warehouse(pos[0], pos[1], initial_health=current_warehouse_health)
        warehouses.add(warehouse); all_sprites.add(warehouse)
    for pos in aa_gun_positions:
        aa_gun = AAGun(pos[0], pos[1], fire_rate_ms=current_aagun_fire_rate, initial_health=current_aagun_health)
        aa_gun.set_enemy_bullets_group(enemy_bullets); aa_guns.add(aa_gun); all_sprites.add(aa_gun)
    jet = FighterJet(SCREEN_WIDTH // 2, 50, player.speed, enemy_bullets, initial_health=current_fighter_health)
    fighter_jets.add(jet); all_sprites.add(jet)

    battleship.is_active = False
    battleship.rect.topleft = (-battleship.width, SCREEN_HEIGHT // 3)
    battleship.max_health = current_battleship_max_health
    battleship.health = battleship.max_health
    if battleship in all_sprites:
        all_sprites.remove(battleship)

    # Start with "get_ready" state for the new stage
    global game_state, get_ready_start_time # Ensure we modify the global game_state
    game_state = "get_ready"
    get_ready_start_time = pygame.time.get_ticks()


reset_stage(is_first_load=True)

# Main Game Loop
while running:
    dt = clock.tick(FPS) / 1000.0
    current_ticks = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == "game_over":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q: running = False
                if event.key == pygame.K_r: reset_stage(is_first_load=True); # game_state becomes "get_ready" via reset_stage
        elif game_state == "get_ready":
            if event.type == pygame.KEYDOWN: # Allow skipping "Get Ready"
                 if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                      game_state = "playing"
                      game_start_time = pygame.time.get_ticks() # Actual gameplay starts now
        elif game_state == "playing":
            if event.type == pygame.USEREVENT + 1:
                if battleship.is_active: battleship.direction *= -1

    keys = pygame.key.get_pressed()

    if game_state == "get_ready":
        if current_ticks - get_ready_start_time > GET_READY_DURATION:
            game_state = "playing"
            game_start_time = pygame.time.get_ticks() # Actual gameplay starts now
            battleship_warning_shown_this_stage = False # Reset warning for new "playing" session
            battleship_approaching_message_active = False


    elif game_state == "playing":
        if keys[pygame.K_ESCAPE]: running = False
        player.handle_input(keys)

        # Updates
        player.update()
        warehouses.update()
        aa_guns.update(player.rect.center)
        fighter_jets.update(player.rect.center)
        enemy_bullets.update()

        # Battleship Warning and Spawning
        time_since_stage_start = current_ticks - game_start_time
        if not battleship.is_active and battleship.health > 0 and not battleship_warning_shown_this_stage:
            time_to_battleship_spawn = BATTLESHIP_SPAWN_TIME - time_since_stage_start
            if 0 < time_to_battleship_spawn <= BATTLESHIP_WARNING_LEAD_TIME:
                battleship_approaching_message_active = True
                battleship_approaching_message_end_time = current_ticks + BATTLESHIP_WARNING_DURATION
                battleship_warning_shown_this_stage = True # Show only once per potential spawn

        if battleship_approaching_message_active and current_ticks > battleship_approaching_message_end_time:
            battleship_approaching_message_active = False

        if not battleship.is_active and battleship.health > 0 and (time_since_stage_start > BATTLESHIP_SPAWN_TIME):
            battleship.activate()
            if battleship not in all_sprites : all_sprites.add(battleship)
            battleship_approaching_message_active = False # Ensure warning is off once spawned

        if battleship.is_active:
            battleship.update(player.rect.center)
            if battleship.health <= 0 and battleship in all_sprites:
                print(f"Battleship Destroyed! +1000 points!")
                play_sound(sound_battleship_explosion)
                score += 1000
                battleship.kill()
                battleship.is_active = False

        # Collision Detections
        for proj_group in [player.vulcan_bullets, player.missiles]:
            for proj in list(proj_group):
                hit_wh = pygame.sprite.spritecollide(proj, warehouses, False)
                for wh in hit_wh:
                    wh.take_damage(proj.damage); proj.kill()
                    if wh.is_destroyed() and wh.health == 0: score += 10; play_sound(sound_explosion_small)
                if not proj.alive(): continue
                hit_aa = pygame.sprite.spritecollide(proj, aa_guns, False)
                for aa in hit_aa:
                    aa.take_damage(proj.damage); proj.kill()
                    if aa.is_destroyed() and aa.health == 0: score += 50; play_sound(sound_explosion_small)
                if not proj.alive(): continue
                hit_jet = pygame.sprite.spritecollide(proj, fighter_jets, False)
                for jet_hit in hit_jet:
                    jet_hit.take_damage(proj.damage); proj.kill()
                    if jet_hit.is_destroyed() and jet_hit.health == 0: score += 100; play_sound(sound_explosion_small)
                if not proj.alive(): continue
                if battleship.is_active and pygame.sprite.collide_rect(proj, battleship):
                    battleship.take_damage(proj.damage); proj.kill()

        for bullet in enemy_bullets:
            if pygame.sprite.collide_rect(bullet, player):
                player.take_damage(bullet.damage); bullet.kill()
                if player.health <= 0:
                    print(f"Game Over - Player health depleted. Final Score: {score}")
                    play_sound(sound_game_over)
                    game_state = "game_over"
                    break
            if game_state == "game_over": break
        if game_state == "game_over": continue

        for wh in list(warehouses):
            if wh.is_destroyed(): wh.kill()
        for gun in list(aa_guns):
            if gun.is_destroyed(): gun.kill()
        for jet_entity in list(fighter_jets):
            if jet_entity.is_destroyed(): jet_entity.kill()

        if not warehouses and not aa_guns and not fighter_jets:
            game_state = "stage_clear"
            stage_clear_message_display_time = pygame.time.get_ticks()
            stage_clear_font = pygame.font.Font(None, 74)
            stage_clear_text = stage_clear_font.render("Stage Clear!", True, GREEN)
            stage_clear_rect = stage_clear_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            print(f"Stage Clear! Current Score: {score}")
            play_sound(sound_stage_clear)

    # Drawing
    screen.fill(BLACK)
    if game_state == "get_ready":
        stage_font_large = pygame.font.Font(None, 74)
        stage_text_large = stage_font_large.render(f"Stage: {current_stage}", True, WHITE)
        stage_rect_large = stage_text_large.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 50))
        screen.blit(stage_text_large, stage_rect_large)

        get_ready_font = pygame.font.Font(None, 74)
        get_ready_text_surf = get_ready_font.render("Get Ready!", True, GREEN)
        get_ready_rect = get_ready_text_surf.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 30))
        screen.blit(get_ready_text_surf, get_ready_rect)

    elif game_state == "playing" or game_state == "stage_clear":
        player.draw(screen); warehouses.draw(screen); aa_guns.draw(screen)
        fighter_jets.draw(screen); enemy_bullets.draw(screen)
        if battleship.is_active: battleship.draw(screen)

        score_font = pygame.font.Font(None, 36)
        score_text_surface = score_font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text_surface, (SCREEN_WIDTH - score_text_surface.get_width() - 10, 10))

        stage_font = pygame.font.Font(None, 36)
        stage_text_surface = stage_font.render(f"Stage: {current_stage}", True, WHITE)
        screen.blit(stage_text_surface, (10, SCREEN_HEIGHT - stage_text_surface.get_height() - 10))

        if battleship_approaching_message_active:
            warn_font = pygame.font.Font(None, 50)
            warn_text_surf = warn_font.render("Battleship Approaching!", True, RED)
            warn_rect = warn_text_surf.get_rect(center=(SCREEN_WIDTH/2, 30))
            screen.blit(warn_text_surf, warn_rect)

        if game_state == "stage_clear":
            screen.blit(stage_clear_text, stage_clear_rect) # Defined when state changes
            if pygame.time.get_ticks() - stage_clear_message_display_time > STAGE_CLEAR_DURATION:
                reset_stage(); # game_state becomes "get_ready"

    elif game_state == "game_over":
        game_over_font = pygame.font.Font(None, 100)
        game_over_text_surf = game_over_font.render("Game Over", True, RED)
        game_over_rect = game_over_text_surf.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/3))
        screen.blit(game_over_text_surf, game_over_rect)
        final_score_font = pygame.font.Font(None, 50)
        final_score_text_surf = final_score_font.render(f"Final Score: {score}", True, WHITE)
        final_score_rect = final_score_text_surf.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        screen.blit(final_score_text_surf, final_score_rect)
        restart_font = pygame.font.Font(None, 40)
        restart_text_surf = restart_font.render("Press 'R' to Restart", True, WHITE)
        restart_rect = restart_text_surf.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT * 0.65))
        screen.blit(restart_text_surf, restart_rect)
        quit_text_surf = restart_font.render("Press 'Q' to Quit", True, WHITE)
        quit_rect = quit_text_surf.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT * 0.75))
        screen.blit(quit_text_surf, quit_rect)

    pygame.display.flip()
pygame.quit()
