import pygame
import os
import random
from typing import List, Dict, Tuple, Optional
from constants import *

class GameObject:
    def __init__(self, x: int, y: int, width: int, height: int, image_path: str):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.image = self.load_image(image_path, width, height)
        self.rect = self.image.get_rect(center=(x, y))
        self.alpha = 255

    def load_image(self, path: str, width: int, height: int) -> pygame.Surface:
        try:
            image = pygame.image.load(path)
            return pygame.transform.scale(image, (width, height)).convert_alpha()
        except (pygame.error, FileNotFoundError):
            surf = pygame.Surface((width, height), pygame.SRCALPHA)
            surf.fill(RED)
            return surf

    def draw(self, screen: pygame.Surface):
        if self.alpha != 255:
            self.image.set_alpha(self.alpha)
        screen.blit(self.image, self.rect)


class Character(GameObject):
    def __init__(self, x: int, y: int, char_type: str):
        self.char_type = char_type
        image_path = os.path.join(CHARACTERS_DIR, f"{char_type}.png") if os.path.exists(os.path.join(CHARACTERS_DIR, f"{char_type}.png")) else ""
        super().__init__(x, y, CHARACTER_WIDTH, CHARACTER_HEIGHT, image_path)
        self.speed = 5
        self.max_health = 5
        self.health = self.max_health
        self.attack_cooldown = 0
        self.direction = 1
        self.current_weapon = 0
        self.weapons = self.load_weapons()
        self.invincible_timer = 0
        self.blink_timer = 0

    def load_weapons(self) -> List[Dict]:
        weapons = [
            {"name": "Шариковая ручка", "damage": 1, "range": 60, "cooldown": 20, "image": "pen"},
            {"name": "Канцелярский нож", "damage": 2, "range": 70, "cooldown": 30, "image": "knife"},
            {"name": "Метла", "damage": 3, "range": 80, "cooldown": 40, "image": "broom"},
            {"name": "Меч", "damage": 4, "range": 90, "cooldown": 50, "image": "sword"}
        ]
        for weapon in weapons:
            image_path = os.path.join(WEAPONS_DIR, f"{weapon['image']}.png")
            weapon["image_surface"] = self.load_image(image_path, WEAPON_WIDTH, WEAPON_HEIGHT)
        return weapons

    def get_current_weapon(self) -> Dict:
        return self.weapons[self.current_weapon]

    def switch_weapon(self, direction: int):
        self.current_weapon = (self.current_weapon + direction) % len(self.weapons)

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.x -= self.speed
            self.direction = -1
        elif keys[pygame.K_RIGHT]:
            self.x += self.speed
            self.direction = 1
        self.x = max(0, min(self.x, SCREEN_WIDTH))
        self.y = GROUND_HEIGHT - self.height // 2
        self.rect.center = (self.x, self.y)
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
            self.blink_timer += 1
            if self.blink_timer % 10 == 0:
                self.alpha = 128 if self.alpha == 255 else 255
        else:
            self.alpha = 255
            self.image.set_alpha(255)

    def take_damage(self, amount: int = 1) -> bool:
        if self.invincible_timer <= 0:
            self.health -= amount
            self.invincible_timer = 180
            self.blink_timer = 0
            return True
        return False

    def attack(self) -> Optional[Dict]:
        weapon = self.get_current_weapon()
        if self.attack_cooldown == 0:
            self.attack_cooldown = weapon["cooldown"]
            return weapon
        return None

    def draw_weapon(self, screen: pygame.Surface):
        weapon = self.get_current_weapon()
        weapon_x = self.x + self.direction * 40
        weapon_y = self.y - 20
        img = pygame.transform.flip(weapon["image_surface"], self.direction == -1, False)
        screen.blit(img, (weapon_x - WEAPON_WIDTH//2, weapon_y - WEAPON_HEIGHT//2))


class Mushroom(GameObject):
    def __init__(self, x: int, y: int, is_big: bool = False):
        self.is_big = is_big
        if is_big:
            image_files = [f for f in os.listdir(MUSHROOMS_DIR) if f.startswith("big_") and f.endswith(('.png', '.jpg', '.jpeg'))]
            image_file = random.choice(image_files) if image_files else ""
            image_path = os.path.join(MUSHROOMS_DIR, image_file) if image_file else ""
            super().__init__(x, y, BIG_MUSHROOM_WIDTH, BIG_MUSHROOM_HEIGHT, image_path)
            self.health = 4
            self.points = 10
            self.brain_chance = 0.3
        else:
            image_files = [f for f in os.listdir(MUSHROOMS_DIR) if f.startswith("small_") and f.endswith(('.png', '.jpg', '.jpeg'))]
            image_file = random.choice(image_files[:5]) if len(image_files) >= 5 else ""
            image_path = os.path.join(MUSHROOMS_DIR, image_file) if image_file else ""
            super().__init__(x, y, MUSHROOM_WIDTH, MUSHROOM_HEIGHT, image_path)
            self.health = 2
            self.points = 5
            self.brain_chance = 0
        self.speed = 2
        self.attack_cooldown = 0
        self.state = "idle"
        self.state_timer = 0
        self.death_animation = 0

    def update(self, target_x: int):
        if self.death_animation > 0:
            self.death_animation -= 1
            self.alpha = max(0, self.alpha - 15)
            return
        if self.state == "idle":
            self.state_timer -= 1
            if self.state_timer <= 0:
                if random.random() < 0.3:
                    self.state = "moving"
                    self.state_timer = random.randint(30, 90)
                else:
                    self.state_timer = random.randint(30, 60)
        elif self.state == "moving":
            if self.x < target_x:
                self.x += self.speed
            elif self.x > target_x:
                self.x -= self.speed
            self.state_timer -= 1
            if self.state_timer <= 0 or abs(self.x - target_x) < 20:
                self.state = "attacking"
                self.state_timer = 30
        elif self.state == "attacking":
            self.state_timer -= 1
            if self.state_timer <= 0:
                self.state = "idle"
                self.state_timer = random.randint(60, 120)
        self.y = GROUND_HEIGHT - self.height // 2
        self.rect.center = (self.x, self.y)

    def take_damage(self, damage: int) -> Tuple[bool, bool]:
        self.health -= damage
        if self.health <= 0:
            self.death_animation = 20
            brain_drop = self.is_big and random.random() < self.brain_chance
            return (True, brain_drop)
        return (False, False)

    def is_attacking(self) -> bool:
        return self.state == "attacking" and self.state_timer > 25

    def is_dead(self) -> bool:
        return self.death_animation > 0 and self.alpha <= 0


class Brain(GameObject):
    def __init__(self, x: int, y: int):
        image_path = os.path.join(EFFECTS_DIR, "brain.png") if os.path.exists(os.path.join(EFFECTS_DIR, "brain.png")) else ""
        super().__init__(x, y, BRAIN_WIDTH, BRAIN_HEIGHT, image_path)
        self.lifetime = 180

    def update(self):
        self.lifetime -= 1
        return self.lifetime <= 0


class ArrowButton(GameObject):
    def __init__(self, x: int, y: int, direction: str):
        image_path = os.path.join(UI_DIR, "arrow.png") if os.path.exists(os.path.join(UI_DIR, "arrow.png")) else ""
        super().__init__(x, y, ARROW_WIDTH, ARROW_HEIGHT, image_path)
        self.direction = direction
        self.is_pressed = False
        self.original_image = self.image.copy()

    def draw(self, screen: pygame.Surface):
        if self.direction == "left":
            img = pygame.transform.flip(self.original_image, True, False)
        else:
            img = self.original_image.copy()
        if self.is_pressed:
            img.fill((255, 255, 255, 128), None, pygame.BLEND_RGBA_MULT)
        screen.blit(img, self.rect)