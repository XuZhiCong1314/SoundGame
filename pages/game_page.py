from pages.base_page import BasePage
from core.Weapon import Weapon, DEFAULT_WEAPONS
from utils.db_utils import DBUtils
import pygame
import random
import math
import numpy  # 确保导入numpy（音效合成需要）
from datetime import datetime

class GamePage(BasePage):
    def __init__(self, screen: pygame.Surface, page_manager):
        super().__init__(screen, page_manager)
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        
        # 游戏基础配置
        self.FPS = 60
        self.CENTER_POS = (self.screen_width//2, self.screen_height//2)  # 玩家固定中心
        self.MAX_ENEMIES = 8
        self.BASE_SPAWN_INTERVAL = 2000
        self.MIN_SPAWN_INTERVAL = 800
        self.SPAWN_SPEEDUP_RATE = 50
        self.BULLET_MAX_DISTANCE = 600
        self.RELOAD_TIME = 1200
        
        # 敌人生成距离（保持500-1500像素极远距）
        self.MIN_SPAWN_DISTANCE = 500
        self.MAX_SPAWN_DISTANCE = 1500
        
        # 颜色定义
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.BLUE = (50, 150, 255)
        self.GREEN = (50, 255, 50)
        self.RED = (255, 50, 50)
        self.ORANGE = (255, 150, 50)
        self.YELLOW = (255, 255, 0)
        
        # 关键属性初始化
        self.is_paused = False
        self.current_weapon_idx = 0  # 对应Player的current_weapon_index
        self.show_mode_tip = False
        self.tip_show_start_time = 0
        self.game_start_time = pygame.time.get_ticks()
        
        # 按键防抖：解决Q/E冲突（核心新增）
        self.last_q_time = 0
        self.last_e_time = 0
        self.last_r_time = 0
        self.debounce_time = 200  # 防抖时间（毫秒），避免长按连续触发
        
        # 初始化混音器
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        
        # 音效合成（保留时长0.6秒+音量0.8）
        self.sounds = self._generate_all_sounds()
        self.enemy_sounds = {
            "up": self._generate_enemy_sound("up"),
            "down": self._generate_enemy_sound("down"),
            "left": self._generate_enemy_sound("left"),
            "right": self._generate_enemy_sound("right")
        }
        
        # -------------------------- 内部类 --------------------------
        class Bullet:
            def __init__(self, x, y, angle, speed, color, size, damage, parent):
                self.x = x
                self.y = y
                self.speed_x = math.cos(angle) * speed
                self.speed_y = math.sin(angle) * speed
                self.color = color
                self.size = size
                self.damage = damage
                self.flight_distance = 0
                self.parent = parent
            
            def update(self):
                self.x += self.speed_x
                self.y += self.speed_y
                self.flight_distance += math.hypot(self.speed_x, self.speed_y)
                return (self.x < -100 or self.x > self.parent.screen_width + 100 or
                        self.y < -100 or self.y > self.parent.screen_height + 100 or
                        self.flight_distance > self.parent.BULLET_MAX_DISTANCE)
            
            def draw(self, screen):
                pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

        class Enemy:
            def __init__(self, parent):
                self.parent = parent
                self.spawn_distance = random.randint(parent.MIN_SPAWN_DISTANCE, parent.MAX_SPAWN_DISTANCE)
                side = random.choice(["up", "down", "left", "right"])
                self.side = side
                
                # 屏幕外极远处生成逻辑
                if side == "up":
                    self.x = random.randint(0, self.parent.screen_width)
                    self.y = -self.spawn_distance  # 上方向外500-1500像素
                elif side == "down":
                    self.x = random.randint(0, self.parent.screen_width)
                    self.y = self.parent.screen_height + self.spawn_distance  # 下方向外
                elif side == "left":
                    self.x = -self.spawn_distance  # 左方向外
                    self.y = random.randint(0, self.parent.screen_height)
                else:  # right
                    self.x = self.parent.screen_width + self.spawn_distance  # 右方向外
                    self.y = random.randint(0, self.parent.screen_height)
                
                # 敌人属性（屏幕外低速，屏幕内加速）
                self.size = 35
                self.is_elite = random.random() < 0.3
                # 保存最大血量（用于计算百分比）
                self.max_health = 350 if self.is_elite else 150
                self.health = self.max_health  # 当前血量初始化为最大血量
                self.base_speed = random.uniform(1, 1.5) * (1.2 if self.is_elite else 1.0)
                self.speed = self.base_speed  # 初始速度=屏幕外低速
                self.damage = 20 if self.is_elite else 12
                self.hit_flash = False
                self.flash_timer = 0
                self.spawn_sound_played = False  # 控制仅播放一次
                self.horizontal_offset = self.x - self.parent.CENTER_POS[0] if side in ["left", "right"] else self.y - self.parent.CENTER_POS[1]
            
            def update(self):
                # 追踪玩家
                dx = self.parent.CENTER_POS[0] - self.x
                dy = self.parent.CENTER_POS[1] - self.y
                dist = math.hypot(dx, dy)
                
                if dist > 5:
                    # 屏幕外低速，屏幕内加速
                    is_inside_screen = (self.x > -50 and self.x < self.parent.screen_width + 50 and
                                       self.y > -50 and self.y < self.parent.screen_height + 50)
                    
                    if is_inside_screen:
                        speed_multiplier = 1.8 * (1.2 if self.is_elite else 1.0)
                    else:
                        speed_multiplier = 1.0
                    
                    self.speed = self.base_speed * speed_multiplier
                    self.x += (dx / dist) * self.speed
                    self.y += (dy / dist) * self.speed
                
                # 击中闪烁
                if self.hit_flash:
                    self.flash_timer += 1
                    if self.flash_timer > 3:
                        self.hit_flash = False
                        self.flash_timer = 0
                
                # 生成即播放音效（仅一次）
                if not self.spawn_sound_played:
                    self.parent._play_enemy_sound(self.side, self.horizontal_offset)
                    self.spawn_sound_played = True
            
            def draw(self, screen):
                color = self.parent.RED if self.is_elite else self.parent.ORANGE
                if self.hit_flash:
                    color = self.parent.WHITE
                pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size//2)
                # 血量条：固定总长度100像素（所有敌人统一长度）
                health_bar_total_width = 100  # 固定总长度
                health_bar_height = 4
                # 计算血量百分比（当前血量/最大血量）
                health_ratio = self.health / self.max_health if self.max_health > 0 else 0
                # 实际显示的血量条长度（按百分比计算）
                health_bar_display_width = int(health_bar_total_width * health_ratio)
                
                # 绘制黑色背景条（总长度）
                pygame.draw.rect(screen, self.parent.BLACK, 
                                (int(self.x) - health_bar_total_width//2,  # 水平居中
                                 int(self.y) + self.size//2 + 8, 
                                 health_bar_total_width, health_bar_height))
                # 绘制彩色血量条（实际长度）
                health_color = self.parent.GREEN if health_ratio > 0.6 else self.parent.ORANGE if health_ratio > 0.3 else self.parent.RED
                pygame.draw.rect(screen, health_color, 
                                (int(self.x) - health_bar_total_width//2,  # 水平居中
                                 int(self.y) + self.size//2 + 8, 
                                 health_bar_display_width, health_bar_height))
                # 精英怪标记
                if self.is_elite:
                    elite_surf = self.parent.small_font.render("精英", True, self.parent.WHITE)
                    screen.blit(elite_surf, (int(self.x) - 15, int(self.y) - self.size//2 - 20))
            
            def is_reached_center(self):
                return math.hypot(self.x - self.parent.CENTER_POS[0], self.y - self.parent.CENTER_POS[1]) < 40
            
            def take_damage(self, damage):
                self.health -= damage
                self.hit_flash = True
                self.parent._play_sound("hit_enemy")
                return self.health <= 0
        
        self.Bullet = Bullet
        self.Enemy = Enemy
        
        # -------------------------- 游戏状态 --------------------------
        self.bullets = []
        self.enemies = []
        self.last_spawn_time = pygame.time.get_ticks()
        self.last_fire_time = pygame.time.get_ticks()
        self.game_score = 0
        self.game_over = False
        self.is_reloading = False
        self.reload_start_time = 0
        
        # 按键状态（仅保留功能按键，新增实时检测相关）
        self.mouse_left_held = False
        
        # 数据库实例
        self.db = DBUtils()

    # -------------------------- 音效合成方法 --------------------------
    def _generate_sound(self, freq_start, freq_end, duration, volume=0.5, wave_type="square"):
        sample_rate = 44100
        num_samples = int(sample_rate * duration)
        samples = []
        
        for i in range(num_samples):
            t = i / sample_rate
            freq = freq_start + (freq_end - freq_start) * (t / duration)
            
            if wave_type == "square":
                value = 32767 if math.sin(2 * math.pi * freq * t) > 0 else -32768
            elif wave_type == "sawtooth":
                value = int(32767 * (2 * (t * freq - math.floor(t * freq + 0.5))))
            elif wave_type == "sine":
                value = int(32767 * math.sin(2 * math.pi * freq * t))
            else:
                value = 0
            
            decay = 1.0 - (t / duration)
            value = int(value * volume * decay)
            samples.append(value.to_bytes(2, byteorder='little', signed=True))
        
        sound_data = b''.join(samples)
        sound = pygame.mixer.Sound(buffer=sound_data)
        return sound

    def _generate_all_sounds(self):
        return {
            "gun_shot": self._generate_sound(800, 400, 0.1, volume=0.4, wave_type="square"),
            "reload": self._generate_reload_sound(),
            "switch_weapon": self._generate_sound(1000, 800, 0.08, volume=0.5, wave_type="sawtooth"),
            "switch_mode": self._generate_sound(1200, 1500, 0.05, volume=0.3, wave_type="sine"),
            "hit_enemy": self._generate_sound(2000, 1800, 0.03, volume=0.3, wave_type="square"),
            "enemy_death": self._generate_sound(500, 200, 0.2, volume=0.5, wave_type="sawtooth"),
            "player_hit": self._generate_player_hit_sound(),
            "game_over": self._generate_sound(200, 50, 1.0, volume=0.7, wave_type="sawtooth"),
            "pause": self._generate_sound(800, 800, 0.05, volume=0.4, wave_type="sine"),
            "resume": self._generate_sound(1000, 1000, 0.05, volume=0.4, wave_type="sine")
        }

    def _generate_reload_sound(self):
        sound1 = self._generate_sound(600, 400, 0.2, volume=0.5, wave_type="sawtooth")
        sound2 = self._generate_sound(800, 1000, 0.1, volume=0.6, wave_type="sawtooth")
        samples1 = pygame.sndarray.array(sound1)
        samples2 = pygame.sndarray.array(sound2)
        combined_samples = numpy.concatenate([samples1, samples2])
        return pygame.mixer.Sound(combined_samples)

    def _generate_player_hit_sound(self):
        sample_rate = 44100
        duration = 0.2
        num_samples = int(sample_rate * duration)
        samples = []
        
        for i in range(num_samples):
            t = i / sample_rate
            sine1 = math.sin(2 * math.pi * 440 * t)
            sine2 = math.sin(2 * math.pi * 880 * t)
            value = int(32767 * (sine1 + sine2) * 0.2)
            decay = 1.0 - (t / duration)
            value = int(value * decay)
            samples.append(value.to_bytes(2, byteorder='little', signed=True))
        
        sound_data = b''.join(samples)
        return pygame.mixer.Sound(buffer=sound_data)

    def _generate_enemy_sound(self, side):
        """敌人音效：时长0.6秒+音量0.8（保留之前优化）"""
        freq_map = {
            "up": (300, 250),
            "down": (350, 300),
            "left": (400, 350),
            "right": (450, 400)
        }
        freq_start, freq_end = freq_map[side]
        return self._generate_sound(freq_start, freq_end, 0.6, volume=0.8, wave_type="sawtooth")

    # -------------------------- 音效播放方法 --------------------------
    def _play_sound(self, sound_key):
        sound = self.sounds.get(sound_key)
        if sound:
            sound.play(maxtime=0)

    def _play_enemy_sound(self, side, horizontal_offset):
        """敌人生成即播放音效（仅一次，立体声定位）"""
        sound = self.enemy_sounds.get(side)
        if not sound:
            return
        
        if side in ["left", "right"]:
            max_offset = self.screen_width // 2
            pan = max(-1.0, min(1.0, horizontal_offset / max_offset))
        else:  # up/down
            max_offset = self.screen_height // 2
            pan = max(-1.0, min(1.0, horizontal_offset / max_offset)) * 0.5
        
        # 音量保持0.6（边缘）-0.9（中间），确保清晰可闻
        volume = 0.6 if abs(pan) > 0.8 else 0.9
        sound.set_volume(volume)
        channel = sound.play(maxtime=0)
        if channel:
            channel.set_volume(1.0 - abs(pan) if pan < 0 else 1.0,
                               1.0 - abs(pan) if pan > 0 else 1.0)

    # -------------------------- 核心联动（完全适配你的 Player 类）--------------------------
    def get_equipped_weapons(self):
        """适配 Player 类的 weapons 装备槽列表（3个槽位）"""
        if not self.current_user or not hasattr(self.current_user, "player"):
            return [DEFAULT_WEAPONS["P92"]]  # 默认武器
        player = self.current_user.player
        
        # 直接读取 Player 的 weapons 列表，过滤空槽
        if hasattr(player, "weapons") and isinstance(player.weapons, list):
            equipped = [weapon for weapon in player.weapons if weapon is not None]
        else:
            equipped = [DEFAULT_WEAPONS["P92"]]
        
        return equipped if equipped else [DEFAULT_WEAPONS["P92"]]

    def get_current_weapon(self):
        """适配 Player 的 get_current_weapon 方法"""
        if not self.current_user or not hasattr(self.current_user, "player"):
            return DEFAULT_WEAPONS["P92"]
        player = self.current_user.player
        current_weapon = player.get_current_weapon()
        return current_weapon if current_weapon else DEFAULT_WEAPONS["P92"]

    def switch_weapon(self):
        """适配 Player 的 switch_weapon 方法（循环切换3个槽位）"""
        if self.game_over or self.is_reloading or self.is_paused:
            return
        player = self.current_user.player
        # 获取当前槽位索引，切换到下一个有武器的槽位
        current_idx = player.current_weapon_index
        equipped = self.get_equipped_weapons()
        if len(equipped) <= 1:
            return
        
        # 循环查找下一个有武器的槽位
        next_idx = (current_idx + 1) % 3
        while player.weapons[next_idx] is None and next_idx != current_idx:
            next_idx = (next_idx + 1) % 3
        
        if next_idx != current_idx:
            player.switch_weapon(next_idx)
            self._play_sound("switch_weapon")
        self.last_fire_time = pygame.time.get_ticks()

    # -------------------------- 游戏核心逻辑 --------------------------
    def get_dynamic_spawn_interval(self):
        game_duration = (pygame.time.get_ticks() - self.game_start_time) / 1000
        speedup_amount = game_duration * self.SPAWN_SPEEDUP_RATE
        spawn_interval = self.BASE_SPAWN_INTERVAL - speedup_amount
        return max(self.MIN_SPAWN_INTERVAL, spawn_interval)

    def spawn_enemy(self):
        current_time = pygame.time.get_ticks()
        spawn_interval = self.get_dynamic_spawn_interval()
        burst_spawn = random.random() < 0.1
        max_spawn = 2 if burst_spawn else 1
        
        if (current_time - self.last_spawn_time > spawn_interval and 
            len(self.enemies) < self.MAX_ENEMIES and not self.game_over and not self.is_paused):
            for _ in range(max_spawn):
                if len(self.enemies) < self.MAX_ENEMIES:
                    self.enemies.append(self.Enemy(self))  # 生成敌人时自动播放音效
            self.last_spawn_time = current_time

    def fire_bullet(self, mouse_pos):
        current_weapon = self.get_current_weapon()
        if not current_weapon or self.game_over or self.is_reloading or self.is_paused:
            return
        
        current_time = pygame.time.get_ticks()
        fire_interval = current_weapon.get_fire_interval()
        if current_time - self.last_fire_time < fire_interval:
            return
        
        if not current_weapon.consume_ammo():
            self.start_reload()
            return
        
        angle = math.atan2(mouse_pos[1] - self.CENTER_POS[1], mouse_pos[0] - self.CENTER_POS[0])
        self.bullets.append(self.Bullet(
            x=self.CENTER_POS[0], y=self.CENTER_POS[1],
            angle=angle, speed=current_weapon.bullet_speed,
            color=current_weapon.color, size=current_weapon.bullet_size,
            damage=current_weapon.damage, parent=self
        ))
        
        self._play_sound("gun_shot")
        self.last_fire_time = current_time

    def start_reload(self):
        current_weapon = self.get_current_weapon()
        if not current_weapon or self.is_reloading or current_weapon.current_ammo <= 0 or self.is_paused:
            return
        self.is_reloading = True
        self.reload_start_time = pygame.time.get_ticks()
        self._play_sound("reload")

    def update_reload(self):
        if not self.is_reloading or self.is_paused:
            return
        current_time = pygame.time.get_ticks()
        if current_time - self.reload_start_time >= self.RELOAD_TIME:
            current_weapon = self.get_current_weapon()
            current_weapon.reload()
            self.is_reloading = False

    def switch_fire_mode(self):
        if self.game_over or self.is_reloading or self.is_paused:
            return
        current_weapon = self.get_current_weapon()
        if current_weapon.switch_mode():
            self._play_sound("switch_mode")
        self.last_fire_time = pygame.time.get_ticks()

    def check_collisions(self):
        hit_bullets = []
        hit_enemies = []
        
        for bullet_idx, bullet in enumerate(self.bullets):
            for enemy_idx, enemy in enumerate(self.enemies):
                if math.hypot(bullet.x - enemy.x, bullet.y - enemy.y) < (enemy.size//2) + bullet.size:
                    hit_bullets.append(bullet_idx)
                    if enemy.take_damage(bullet.damage):
                        hit_enemies.append(enemy_idx)
                        self.game_score += 200 if enemy.is_elite else 80
                        self.random_reload_ammo(enemy.is_elite)
                        self._play_sound("enemy_death")
        
        for idx in reversed(hit_bullets):
            if idx < len(self.bullets):
                del self.bullets[idx]
        for idx in reversed(hit_enemies):
            if idx < len(self.enemies):
                del self.enemies[idx]

    def random_reload_ammo(self, is_elite):
        current_weapon = self.get_current_weapon()
        max_reload = math.ceil(current_weapon.clip_capacity * 0.5) if is_elite else math.ceil(current_weapon.clip_capacity * 0.2)
        reload_amount = random.randint(1, max_reload)
        current_weapon.current_ammo += reload_amount
        current_weapon.current_ammo = min(current_weapon.current_ammo, current_weapon.total_ammo * 2)

    def check_enemy_damage(self):
        """适配 Player 的 take_damage 和 current_hp 属性"""
        if self.game_over or self.is_paused or not self.current_user:
            return
        player = self.current_user.player
        for enemy in self.enemies[:]:
            if enemy.is_reached_center():
                self.enemies.remove(enemy)
                # 调用 Player 的 take_damage 方法
                player.take_damage(enemy.damage)
                self._play_sound("player_hit")
                # 判断是否死亡（current_hp <= 0）
                if player.current_hp <= 0:
                    self.game_over = True
                    self.current_user.add_score(self.game_score)
                    self.current_user.save_to_db()
                    self._play_sound("game_over")

    def reset_game(self):
        """适配 Player 的 reset 方法"""
        if self.current_user and hasattr(self.current_user, "player"):
            player = self.current_user.player
            player.reset()  # Player 类的 reset 方法已重置 current_hp 和武器
        self.game_score = 0
        self.game_over = False
        self.is_paused = False
        self.is_reloading = False
        self.bullets.clear()
        self.enemies.clear()
        self.last_spawn_time = pygame.time.get_ticks()
        self.last_fire_time = pygame.time.get_ticks()
        self.game_start_time = pygame.time.get_ticks()
        self.show_mode_tip = False
        # 重置防抖时间
        self.last_q_time = 0
        self.last_e_time = 0
        self.last_r_time = 0

    # -------------------------- 实时按键检测（核心新增，解决冲突）--------------------------
    def check_real_time_keys(self, current_time):
        """实时检测Q/E/R按键，避免冲突"""
        keys = pygame.key.get_pressed()
        
        # 1. 换弹（R键，防抖）
        if keys[pygame.K_r] and (current_time - self.last_r_time > self.debounce_time):
            self.start_reload()
            # 互斥保护：防止同时触发Q/E
            self.last_q_time = current_time
            self.last_e_time = current_time
            self.last_r_time = current_time
        
        # 2. 武器切换（Q键，防抖）
        if keys[pygame.K_q] and (current_time - self.last_q_time > self.debounce_time):
            self.switch_weapon()
            # 互斥保护：防止同时触发E/R
            self.last_q_time = current_time
            self.last_e_time = current_time
            self.last_r_time = current_time
        
        # 3. 模式切换（E键，防抖）
        if keys[pygame.K_e] and (current_time - self.last_e_time > self.debounce_time):
            self.switch_fire_mode()
            # 互斥保护：防止同时触发Q/R
            self.last_e_time = current_time
            self.last_q_time = current_time
            self.last_r_time = current_time

    # -------------------------- UI绘制（完全适配 Player 类）--------------------------
    def draw_ui(self):
        font_small = self.small_font
        font_medium = self.medium_font
        
        score_surf = font_medium.render(f"得分: {self.game_score}", True, self.YELLOW)
        self.screen.blit(score_surf, (20, 20))
        if self.current_user:
            total_surf = font_medium.render(f"总得分: {self.current_user.total_score}", True, self.GREEN)
            self.screen.blit(total_surf, (20, 50))
        
        if self.current_user and hasattr(self.current_user, "player"):
            player = self.current_user.player
            # 适配 Player 的 current_hp 属性
            health = player.current_hp
            health_color = self.GREEN if health > 60 else self.ORANGE if health > 30 else self.RED
            health_surf = font_medium.render(f"血量: {health}/{player.max_hp}", True, health_color)
            self.screen.blit(health_surf, (self.screen_width - 180, 20))
            health_bar_width = 200
            health_bar_height = 10
            pygame.draw.rect(self.screen, self.BLACK, (self.screen_width - 200, 55, health_bar_width, health_bar_height))
            # 计算血量条长度（按比例）
            health_bar_length = int(health_bar_width * (health / player.max_hp))
            pygame.draw.rect(self.screen, health_color, (self.screen_width - 200, 55, health_bar_length, health_bar_height))
        
        current_weapon = self.get_current_weapon()
        weapon_surf = font_medium.render(
            f"{current_weapon.name} | {current_weapon.active_mode.upper()} | 弹夹: {current_weapon.current_clip}/{current_weapon.clip_capacity} | 备用: {current_weapon.current_ammo}",
            True, current_weapon.color
        )
        self.screen.blit(weapon_surf, (self.screen_width//2 - 450, 20))
        
        if self.is_reloading:
            reload_progress = min(1.0, (pygame.time.get_ticks() - self.reload_start_time) / self.RELOAD_TIME)
            reload_surf = font_medium.render(f"换弹中... {int(reload_progress*100)}%", True, self.ORANGE)
            self.screen.blit(reload_surf, (self.screen_width//2 - 100, self.screen_height - 60))
        
        game_duration = int((pygame.time.get_ticks() - self.game_start_time) / 1000)
        difficulty_text = f"游戏时长: {game_duration}秒 | 敌人强度: {'高' if game_duration > 60 else '中等'}"
        difficulty_surf = font_small.render(difficulty_text, True, self.ORANGE)
        self.screen.blit(difficulty_surf, (20, self.screen_height - 30))
        
        if self.is_paused:
            pause_surf = font_medium.render("游戏暂停（P键继续）", True, self.RED)
            self.screen.blit(pause_surf, (self.screen_width//2 - 120, self.screen_height//2))
        elif self.game_over:
            over_surf = font_medium.render(f"游戏结束！得分: {self.game_score}", True, self.RED)
            restart_surf = font_small.render("SPACE重启 | ESC返回", True, self.WHITE)
            self.screen.blit(over_surf, (self.screen_width//2 - 120, self.screen_height//2 - 30))
            self.screen.blit(restart_surf, (self.screen_width//2 - 100, self.screen_height//2 + 20))
        
        # 控制提示（移除移动相关按键）
        control_surf = font_small.render("Q切换武器 | E切换模式 | R换弹 | P暂停 | 鼠标射击", True, self.WHITE)
        self.screen.blit(control_surf, (self.screen_width//2 - 250, self.screen_height - 30))

    # -------------------------- 父类方法重写 --------------------------
    def update(self, dt: float):
        if self.show_mode_tip:
            if pygame.time.get_ticks() - self.tip_show_start_time > 1000:
                self.show_mode_tip = False
        
        if self.is_paused or self.game_over or not self.current_user:
            return
        
        current_time = pygame.time.get_ticks()
        # 实时检测按键（核心冲突解决）
        self.check_real_time_keys(current_time)
        
        self.spawn_enemy()
        self.update_reload()
        
        for enemy in self.enemies:
            enemy.update()
        
        self.bullets[:] = [bullet for bullet in self.bullets if not bullet.update()]
        
        self.check_collisions()
        self.check_enemy_damage()
        
        # 自动射击（按住鼠标左键，自动模式）
        if self.mouse_left_held:
            current_weapon = self.get_current_weapon()
            if current_weapon and current_weapon.active_mode == "auto":
                self.fire_bullet(pygame.mouse.get_pos())

    def draw(self):
        self.screen.fill(self.BLACK)
        
        if not self.current_user:
            tip_surf = self.medium_font.render("请先登录并装备武器", True, self.WHITE)
            self.screen.blit(tip_surf, (self.screen_width//2 - 150, self.screen_height//2))
            return
        
        # 绘制固定在中心的玩家
        current_weapon = self.get_current_weapon()
        player_color = current_weapon.color if current_weapon else self.WHITE
        pygame.draw.circle(self.screen, player_color, self.CENTER_POS, 15)
        pygame.draw.line(self.screen, self.WHITE, (self.CENTER_POS[0]-15, self.CENTER_POS[1]), (self.CENTER_POS[0]+15, self.CENTER_POS[1]), 3)
        pygame.draw.line(self.screen, self.WHITE, (self.CENTER_POS[0], self.CENTER_POS[1]-15), (self.CENTER_POS[0], self.CENTER_POS[1]+15), 3)
        
        # 绘制子弹和敌人
        for bullet in self.bullets:
            bullet.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        
        # 绘制UI
        self.draw_ui()

    def handle_event(self, event: pygame.event.Event):
        if not self.current_user:
            return
        
        # 仅处理非实时按键（ESC、SPACE、P、鼠标点击）
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self.game_over:
                self.reset_game()
            elif event.key == pygame.K_p:
                self.is_paused = not self.is_paused
                self._play_sound("pause" if self.is_paused else "resume")
            elif event.key == pygame.K_ESCAPE:
                if self.current_user:
                    self.current_user.save_to_db()
                self.page_manager.switch_page("home")
        
        # 鼠标射击（点击/按住）
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.mouse_left_held = True
            if not self.game_over and not self.is_paused:
                self.fire_bullet(pygame.mouse.get_pos())
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.mouse_left_held = False

# 确保numpy已安装（音效合成必需）
try:
    import numpy
except ImportError:
    raise ImportError("请安装numpy库以支持音效合成：pip install numpy")