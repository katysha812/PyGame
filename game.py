import pygame
import sys
import os
import json
import random
from typing import List, Dict
from constants import *
from game_objects import *

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Грибное приключение")
        self.clock = pygame.time.Clock()
        self.running = True
        self.max_background_offset = 2400
        self.loading_hints = [
            "Используйте стрелки влево/вправо для движения",
            "Нажмите SPACE для атаки",
            "Используйте 1-4 для смены оружия",
            "Собирайте грибы и побеждайте врагов!",
            "Собирайте мозги за 100 очков!",
            "После удара у вас есть 3 секунды неуязвимости"
        ]
        self.current_hint = 0
        self.hint_timer = 0
        self.background = self.load_background("forest")
        self.loading_bg = self.load_background("loading")
        self.leaderboard_bg = self.load_background("leaderboard")
        self.character = None
        self.mushrooms = []
        self.brains = []
        self.current_group = 0
        self.group_defeated = True
        self.background_offset = 0
        arrow_y = SCREEN_HEIGHT // 2 - ARROW_HEIGHT // 2
        self.left_arrow = ArrowButton(50, arrow_y, "left")
        self.right_arrow = ArrowButton(SCREEN_WIDTH - 50, arrow_y, "right")
        self.score = 0
        self.game_state = "loading"
        self.player_name = ""
        self.loading_progress = 0
        self.leaderboard = self.load_leaderboard()

    def load_background(self, bg_type: str) -> pygame.Surface:
        bg_images = [f for f in os.listdir(BACKGROUNDS_DIR) if f.startswith(bg_type) and f.endswith(('.png', '.jpg', '.jpeg'))]
        if bg_images:
            bg = pygame.image.load(os.path.join(BACKGROUNDS_DIR, bg_images[0]))
            return pygame.transform.scale(bg, (self.max_background_offset, SCREEN_HEIGHT)).convert()
        else:
            surf = pygame.Surface((self.max_background_offset, SCREEN_HEIGHT))
            color1 = PURPLE if bg_type == "loading" else (BLUE if bg_type == "leaderboard" else GREEN)
            color2 = BLACK if bg_type == "forest" else (100, 100, 100)
            surf.fill(color1)
            pygame.draw.rect(surf, color2, (0, GROUND_HEIGHT, self.max_background_offset, SCREEN_HEIGHT - GROUND_HEIGHT))
            return surf

    def load_leaderboard(self) -> List[Dict]:
        leaderboard_file = "leaderboard.json"
        default_data = []
        if not os.path.exists(leaderboard_file):
            with open(leaderboard_file, 'w') as f:
                json.dump(default_data, f)
            return default_data
        try:
            with open(leaderboard_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return default_data
        except (json.JSONDecodeError, IOError):
            print("Ошибка чтения таблицы лидеров, создаем новую")
            return default_data

    def save_leaderboard(self):
        try:
            with open("leaderboard.json", 'w') as f:
                json.dump(self.leaderboard, f, indent=4)
        except IOError:
            print("Ошибка сохранения таблицы лидеров")

    def add_to_leaderboard(self, name: str, score: int):
        if not name:
            name = "Unknown"
        new_entry = {
            "name": name,
            "score": score,
            "character": self.character.char_type if self.character else "Unknown"
        }
        self.leaderboard.append(new_entry)
        self.leaderboard.sort(key=lambda x: x["score"], reverse=True)
        self.leaderboard = self.leaderboard[:10]
        self.save_leaderboard()

    def spawn_mushroom_group(self):
        group_size = random.randint(3, 6)
        start_x = self.background_offset + SCREEN_WIDTH + 100
        has_big = random.random() < 0.3
        for i in range(group_size):
            x = start_x + i * 100
            is_big = has_big and (i == group_size - 1)
            mushroom = Mushroom(x, GROUND_HEIGHT, is_big)
            mushroom.state_timer = random.randint(30, 90)
            self.mushrooms.append(mushroom)
        self.group_defeated = False
        self.current_group += 1

    def run(self):
        self.loading_progress = 0
        while self.running:
            self.handle_events()
            if self.game_state == "loading":
                self.update_loading()
                self.draw_loading_screen()
            elif self.game_state == "character_select":
                self.draw_character_select()
            elif self.game_state in ["playing", "moving_forward"]:
                self.update_game()
                self.draw_game()
            elif self.game_state == "game_over":
                self.draw_game_over()
            elif self.game_state == "leaderboard":
                self.draw_leaderboard()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if self.game_state == "loading":
                    if self.loading_progress < 100:
                        self.loading_progress = 100
                elif self.game_state == "character_select":
                    char_types = ["elf", "witch", "warrior", "bard", "healer", "student"]
                    if pygame.K_1 <= event.key <= pygame.K_6:
                        char_index = event.key - pygame.K_1
                        self.character = Character(SCREEN_WIDTH//4, GROUND_HEIGHT, char_types[char_index])
                        self.player_name = ["Эльф", "Ведьма", "Воин", "Бард", "Лекарша", "Студентка"][char_index]
                        self.game_state = "playing"
                        self.spawn_mushroom_group()
                elif self.game_state == "playing":
                    if event.key == pygame.K_SPACE and self.character:
                        attack_result = self.character.attack()
                        if attack_result:
                            for mushroom in self.mushrooms[:]:
                                attack_pos = self.character.x + self.character.direction * attack_result["range"]
                                if abs(mushroom.x - attack_pos) < 30:
                                    destroyed, brain_drop = mushroom.take_damage(attack_result["damage"])
                                    if destroyed:
                                        self.score += mushroom.points
                                        if brain_drop:
                                            self.brains.append(Brain(mushroom.x, mushroom.y))
                    elif event.key == pygame.K_ESCAPE:
                        self.game_state = "game_over"
                elif self.game_state == "game_over":
                    if event.key == pygame.K_RETURN:
                        self.__init__()
                        self.game_state = "character_select"
                    elif event.key == pygame.K_l:
                        self.game_state = "leaderboard"
                elif self.game_state == "leaderboard" and event.key == pygame.K_ESCAPE:
                    self.game_state = "game_over"

    def update_loading(self):
        self.loading_progress += 0.5
        self.hint_timer += 1
        if self.hint_timer >= 180:
            self.hint_timer = 0
            self.current_hint = (self.current_hint + 1) % len(self.loading_hints)
        if self.loading_progress >= 100:
            self.game_state = "character_select"

    def update_game(self):
        if self.character:
            self.character.update()
            keys = pygame.key.get_pressed()
            self.left_arrow.is_pressed = keys[pygame.K_LEFT]
            self.right_arrow.is_pressed = keys[pygame.K_RIGHT]
            if keys[pygame.K_1]:
                self.character.current_weapon = 0
            elif keys[pygame.K_2]:
                self.character.current_weapon = 1
            elif keys[pygame.K_3]:
                self.character.current_weapon = 2
            elif keys[pygame.K_4]:
                self.character.current_weapon = 3
        if self.game_state == "playing":
            active_mushrooms = 0
            for mushroom in self.mushrooms[:]:
                if mushroom.is_dead():
                    self.mushrooms.remove(mushroom)
                    continue
                mushroom.update(self.character.x if self.character else SCREEN_WIDTH//2)
                if mushroom.is_attacking() and self.character and abs(mushroom.x - self.character.x) < 50:
                    if self.character.take_damage():
                        if self.character.health <= 0:
                            self.game_state = "game_over"
                            self.add_to_leaderboard(self.player_name, self.score)
                if mushroom.health > 0 and mushroom.death_animation <= 0:
                    active_mushrooms += 1
            for brain in self.brains[:]:
                if brain.update():
                    self.brains.remove(brain)
                elif self.character and pygame.sprite.collide_rect(self.character, brain):
                    self.score += 100
                    self.brains.remove(brain)
            if active_mushrooms == 0 and len(self.mushrooms) > 0:
                self.mushrooms = []
                self.group_defeated = True
                self.game_state = "moving_forward"
            if self.group_defeated and len(self.mushrooms) == 0:
                self.spawn_mushroom_group()
        elif self.game_state == "moving_forward":
            if self.character:
                self.character.x += self.character.speed
                self.background_offset += self.character.speed
                if self.character.x >= SCREEN_WIDTH // 2:
                    self.character.x = SCREEN_WIDTH // 4
                    self.game_state = "playing"
                if self.background_offset >= self.max_background_offset - SCREEN_WIDTH:
                    self.background_offset = self.max_background_offset - SCREEN_WIDTH
                    self.game_state = "game_over"
                    self.add_to_leaderboard(self.player_name, self.score)

    def draw_loading_screen(self):
        self.screen.blit(self.loading_bg, (0, 0))
        progress = min(100, self.loading_progress)
        pygame.draw.rect(self.screen, WHITE, (SCREEN_WIDTH//2 - 150, GROUND_HEIGHT - 20, 300, 20), 2)
        pygame.draw.rect(self.screen, YELLOW, (SCREEN_WIDTH//2 - 150, GROUND_HEIGHT - 20, 300 * progress / 100, 20))
        loading_text = font_large.render("Загрузка...", True, WHITE)
        self.screen.blit(loading_text, (SCREEN_WIDTH//2 - loading_text.get_width()//2, GROUND_HEIGHT - 70))
        hint_text = font_medium.render(self.loading_hints[self.current_hint], True, WHITE)
        self.screen.blit(hint_text, (SCREEN_WIDTH//2 - hint_text.get_width()//2, GROUND_HEIGHT + 50))
        percent_text = font_medium.render(f"{progress}%", True, WHITE)
        self.screen.blit(percent_text, (SCREEN_WIDTH//2 - percent_text.get_width()//2, GROUND_HEIGHT + 10))

    def draw_character_select(self):
        self.screen.blit(self.background, (-self.background_offset, 0))
        pygame.draw.rect(self.screen, BLACK, (0, GROUND_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_HEIGHT))
        title_text = font_large.render("Выберите персонажа", True, WHITE)
        self.screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 50))
        characters = [
            {"name": "Эльф", "key": pygame.K_1},
            {"name": "Ведьма", "key": pygame.K_2},
            {"name": "Воин", "key": pygame.K_3},
            {"name": "Бард", "key": pygame.K_4},
            {"name": "Лекарша", "key": pygame.K_5},
            {"name": "Студентка", "key": pygame.K_6}
        ]
        for i, char in enumerate(characters):
            y_pos = 120 + i * 60
            char_text = font_medium.render(f"{i+1}. {char['name']}", True, WHITE)
            self.screen.blit(char_text, (SCREEN_WIDTH//2 - char_text.get_width()//2, y_pos))
        hint_text = font_small.render("Нажмите цифру от 1 до 6 для выбора персонажа", True, WHITE)
        self.screen.blit(hint_text, (SCREEN_WIDTH//2 - hint_text.get_width()//2, SCREEN_HEIGHT - 50))

    def draw_game(self):
        self.screen.blit(self.background, (-self.background_offset, 0))
        pygame.draw.rect(self.screen, BLACK, (0, GROUND_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_HEIGHT))
        for brain in self.brains:
            brain.draw(self.screen)
        for mushroom in self.mushrooms:
            if mushroom.death_animation <= 0 or mushroom.alpha > 0:
                mushroom.draw(self.screen)
        if self.character:
            self.character.draw(self.screen)
            self.character.draw_weapon(self.screen)
            weapon = self.character.get_current_weapon()
            if self.character.attack_cooldown > weapon["cooldown"] - 10:
                attack_pos = self.character.x + self.character.direction * weapon["range"]
                pygame.draw.circle(self.screen, WHITE, (attack_pos, self.character.y), 20)
        self.left_arrow.draw(self.screen)
        self.right_arrow.draw(self.screen)
        score_text = font_medium.render(f"Очки: {self.score}", True, WHITE)
        health_text = font_medium.render(f"Здоровье: {self.character.health if self.character else 0}", True, WHITE)
        group_text = font_medium.render(f"Группа: {self.current_group}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(health_text, (10, 40))
        self.screen.blit(group_text, (10, 70))
        if self.character:
            weapon = self.character.get_current_weapon()
            weapon_text = font_small.render(f"{weapon['name']} (Урон: {weapon['damage']}, Дальность: {weapon['range']})", True, WHITE)
            self.screen.blit(weapon_text, (SCREEN_WIDTH//2 - weapon_text.get_width()//2, 10))
            controls_text = font_small.render("1-4: смена оружия, SPACE: атака, ESC: пауза", True, WHITE)
            self.screen.blit(controls_text, (SCREEN_WIDTH//2 - controls_text.get_width()//2, SCREEN_HEIGHT - 30))

    def draw_game_over(self):
        self.screen.blit(self.background, (-self.background_offset, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        message = "Игра окончена!" if self.character and self.character.health <= 0 else "Победа!"
        message_text = font_large.render(message, True, WHITE)
        score_text = font_medium.render(f"Ваш счет: {self.score}", True, WHITE)
        restart_text = font_medium.render("Нажмите ENTER для рестарта", True, WHITE)
        leaderboard_text = font_medium.render("Нажмите L для таблицы лидеров", True, WHITE)
        self.screen.blit(message_text, (SCREEN_WIDTH//2 - message_text.get_width()//2, SCREEN_HEIGHT//2 - 60))
        self.screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, SCREEN_HEIGHT//2))
        self.screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 60))
        self.screen.blit(leaderboard_text, (SCREEN_WIDTH//2 - leaderboard_text.get_width()//2, SCREEN_HEIGHT//2 + 100))

    def draw_leaderboard(self):
        self.screen.blit(self.leaderboard_bg, (0, 0))
        title_text = font_large.render("Таблица лидеров", True, WHITE)
        self.screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 50))
        if not self.leaderboard:
            no_data_text = font_medium.render("Нет данных", True, WHITE)
            self.screen.blit(no_data_text, (SCREEN_WIDTH//2 - no_data_text.get_width()//2, 120))
        else:
            for i, entry in enumerate(self.leaderboard[:10]):
                name = entry.get('name', 'Unknown')
                score = entry.get('score', 0)
                character = entry.get('character', '???')
                entry_text = font_medium.render(f"{i+1}. {name} ({character}): {score}", True, WHITE)
                self.screen.blit(entry_text, (SCREEN_WIDTH//2 - entry_text.get_width()//2, 120 + i * 40))
        back_text = font_medium.render("Нажмите ESC для возврата", True, WHITE)
        self.screen.blit(back_text, (SCREEN_WIDTH//2 - back_text.get_width()//2, SCREEN_HEIGHT - 50))