import pygame
import os

pygame.init()
pygame.font.init()

# Константы экрана
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GROUND_HEIGHT = 500
FPS = 60

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
YELLOW = (255, 255, 0)

# Размеры объектов
CHARACTER_WIDTH, CHARACTER_HEIGHT = 60, 90
MUSHROOM_WIDTH, MUSHROOM_HEIGHT = 50, 70
BIG_MUSHROOM_WIDTH, BIG_MUSHROOM_HEIGHT = 70, 100
WEAPON_WIDTH, WEAPON_HEIGHT = 60, 60
ARROW_WIDTH, ARROW_HEIGHT = 50, 50
BRAIN_WIDTH, BRAIN_HEIGHT = 40, 40

# Пути к ресурсам
ASSETS_DIR = "assets"
BACKGROUNDS_DIR = os.path.join(ASSETS_DIR, "backgrounds")
CHARACTERS_DIR = os.path.join(ASSETS_DIR, "characters")
MUSHROOMS_DIR = os.path.join(ASSETS_DIR, "mushrooms")
WEAPONS_DIR = os.path.join(ASSETS_DIR, "weapons")
UI_DIR = os.path.join(ASSETS_DIR, "ui")
EFFECTS_DIR = os.path.join(ASSETS_DIR, "effects")

# Создание директорий при необходимости
os.makedirs(BACKGROUNDS_DIR, exist_ok=True)
os.makedirs(CHARACTERS_DIR, exist_ok=True)
os.makedirs(MUSHROOMS_DIR, exist_ok=True)
os.makedirs(WEAPONS_DIR, exist_ok=True)
os.makedirs(UI_DIR, exist_ok=True)
os.makedirs(EFFECTS_DIR, exist_ok=True)

# Шрифты
font_small = pygame.font.SysFont('Arial', 18)
font_medium = pygame.font.SysFont('Arial', 24)
font_large = pygame.font.SysFont('Arial', 32)