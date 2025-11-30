from pages.base_page import BasePage
from core.Weapon import DEFAULT_WEAPONS
import pygame
from config import *

class EquipmentPage(BasePage):
    def __init__(self, screen: pygame.Surface, page_manager):
        super().__init__(screen, page_manager)
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        
        # 区域位置
        self.slot_area_rect = pygame.Rect(50, 120, 300, 400)
        self.weapon_area_rect = pygame.Rect(450, 120, 300, 400)
        self.back_btn_rect = pygame.Rect(50, 30, 100, 35)  # 返回按钮
        
        # 装备槽配置
        self.slot_size = 80
        self.slot_spacing = 35
        self.slot_rects = []
        self._init_slot_rects()
        
        # 拖动相关
        self.dragging_weapon = None
        self.drag_offset = (0, 0)
        self.unlocked_weapons = {}
        
        # 提示信息（用于重复装备提示）
        self.tip_text = ""
        self.tip_show_time = 0

    def _init_slot_rects(self):
        """初始化3个装备槽位置"""
        start_y = self.slot_area_rect.y + 50
        for i in range(3):
            slot_rect = pygame.Rect(
                self.slot_area_rect.centerx - self.slot_size//2,
                start_y + i * (self.slot_size + self.slot_spacing),
                self.slot_size,
                self.slot_size
            )
            self.slot_rects.append(slot_rect)

    def update(self, dt: float):
        """同步用户已解锁武器+隐藏提示信息"""
        if self.current_user:
            self.unlocked_weapons = self.current_user.unlocked_weapons
        
        # 3秒后隐藏提示信息
        if self.tip_text and pygame.time.get_ticks() - self.tip_show_time > 3000:
            self.tip_text = ""

    def draw(self):
        self.screen.fill(DARK_BLUE)
        
        # 标题
        title_surf = self.font.render("⚔️ 装备管理", True, YELLOW)
        self.screen.blit(title_surf, (self.screen_width//2 - 120, 40))
        
        # 区域边框
        pygame.draw.rect(self.screen, BLUE, self.slot_area_rect, 3)
        pygame.draw.rect(self.screen, GREEN, self.weapon_area_rect, 3)
        
        # 区域标题
        slot_title = self.medium_font.render("装备槽（点击切换）", True, WHITE)
        weapon_title = self.medium_font.render("已解锁武器（拖动装备）", True, WHITE)
        self.screen.blit(slot_title, (self.slot_area_rect.centerx - slot_title.get_width()//2, self.slot_area_rect.y - 30))
        self.screen.blit(weapon_title, (self.weapon_area_rect.centerx - weapon_title.get_width()//2, self.weapon_area_rect.y - 30))
        
        # 绘制核心内容
        self._draw_equipment_slots()
        self._draw_unlocked_weapons()
        self._draw_back_button()
        self._draw_dragging_weapon()
        self._draw_tip_text()  # 绘制提示信息

    def _draw_equipment_slots(self):
        """绘制装备槽及已装备武器"""
        if not self.current_user:
            tip_surf = self.small_font.render("请先登录", True, RED)
            self.screen.blit(tip_surf, (self.slot_area_rect.centerx - 40, self.slot_area_rect.centery))
            return
        
        player_weapons = self.current_user.player.weapons
        
        for i, (slot_rect, weapon) in enumerate(zip(self.slot_rects, player_weapons)):
            # 装备槽背景
            pygame.draw.rect(self.screen, (30, 30, 60), slot_rect, border_radius=5)
            pygame.draw.rect(self.screen, GRAY, slot_rect, 2, border_radius=5)
            
            # 槽位编号
            slot_num = self.small_font.render(f"{i+1}", True, WHITE)
            self.screen.blit(slot_num, (slot_rect.x + 5, slot_rect.y + 5))
            
            # 已装备武器
            if weapon:
                weapon_name = self.small_font.render(weapon.name[:6], True, weapon.color)
                ammo_text = f"{weapon.current_clip}/{weapon.current_ammo}"
                ammo_surf = self.small_font.render(ammo_text, True, WHITE)
                
                self.screen.blit(weapon_name, (slot_rect.x + 5, slot_rect.y + 30))
                self.screen.blit(ammo_surf, (slot_rect.x + 5, slot_rect.y + 55))

    def _draw_unlocked_weapons(self):
        """绘制已解锁武器列表"""
        if not self.current_user or not self.unlocked_weapons:
            tip_surf = self.small_font.render("暂无解锁武器", True, RED)
            self.screen.blit(tip_surf, (self.weapon_area_rect.centerx - 60, self.weapon_area_rect.centery))
            return
        
        # 2列排列武器
        weapon_list = list(self.unlocked_weapons.values())
        col_count = 2
        weapon_size = 70
        spacing = 25
        start_x = self.weapon_area_rect.x + 20
        start_y = self.weapon_area_rect.y + 20
        
        for idx, weapon in enumerate(weapon_list):
            row = idx // col_count
            col = idx % col_count
            weapon_rect = pygame.Rect(
                start_x + col * (weapon_size + spacing),
                start_y + row * (weapon_size + spacing),
                weapon_size,
                weapon_size
            )
            
            # 绘制武器
            pygame.draw.rect(self.screen, weapon.color, weapon_rect, border_radius=5)
            pygame.draw.rect(self.screen, WHITE, weapon_rect, 1, border_radius=5)
            
            name_surf = self.small_font.render(weapon.name[:6], True, WHITE)
            damage_surf = self.small_font.render(f"伤害：{weapon.damage}", True, WHITE)
            
            self.screen.blit(name_surf, (weapon_rect.x + 3, weapon_rect.y + 3))
            self.screen.blit(damage_surf, (weapon_rect.x + 3, weapon_rect.y + 45))

    def _draw_back_button(self):
        """绘制返回按钮（优化视觉反馈）"""
        if self.back_btn_rect.collidepoint(pygame.mouse.get_pos()):
            btn_color = (180, 50, 50)  # 悬浮深色
            text_color = (255, 255, 255)
        else:
            btn_color = RED  # 默认红色
            text_color = (255, 255, 255)
        
        pygame.draw.rect(self.screen, btn_color, self.back_btn_rect, border_radius=5)
        btn_surf = self.small_font.render("返回主菜单", True, text_color)
        self.screen.blit(btn_surf, (
            self.back_btn_rect.centerx - btn_surf.get_width()//2,
            self.back_btn_rect.centery - btn_surf.get_height()//2
        ))

    def _draw_dragging_weapon(self):
        """绘制拖动中的武器"""
        if self.dragging_weapon:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            weapon_rect = pygame.Rect(
                mouse_x - self.drag_offset[0],
                mouse_y - self.drag_offset[1],
                70,
                70
            )
            
            pygame.draw.rect(self.screen, self.dragging_weapon.color, weapon_rect, border_radius=5)
            pygame.draw.rect(self.screen, WHITE, weapon_rect, 1, border_radius=5)
            
            name_surf = self.small_font.render(self.dragging_weapon.name[:6], True, WHITE)
            self.screen.blit(name_surf, (weapon_rect.x + 3, weapon_rect.y + 3))

    def _draw_tip_text(self):
        """绘制提示信息（重复装备/操作成功）"""
        if self.tip_text:
            tip_surf = self.small_font.render(self.tip_text, True, RED if "不能" in self.tip_text else GREEN)
            self.screen.blit(tip_surf, (self.screen_width//2 - tip_surf.get_width()//2, 100))

    def handle_event(self, event: pygame.event.Event):
        # 修复返回键：优先处理返回按钮点击（解决失效问题）
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 点击返回按钮：直接返回主菜单（最高优先级）
            if self.back_btn_rect.collidepoint(event.pos):
                self.page_manager.switch_page("home")
                self.tip_text = ""
                return
            
            # 其他点击：拖动武器/切换槽位
            self._start_drag_weapon(event.pos)
            self._switch_equipment_slot(event.pos)
        
        # 鼠标松开：装备武器
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._end_drag_weapon(event.pos)

    def _start_drag_weapon(self, mouse_pos):
        """开始拖动武器"""
        weapon_list = list(self.unlocked_weapons.values())
        col_count = 2
        weapon_size = 70
        spacing = 25
        start_x = self.weapon_area_rect.x + 20
        start_y = self.weapon_area_rect.y + 20
        
        for idx, weapon in enumerate(weapon_list):
            row = idx // col_count
            col = idx % col_count
            weapon_rect = pygame.Rect(
                start_x + col * (weapon_size + spacing),
                start_y + row * (weapon_size + spacing),
                weapon_size,
                weapon_size
            )
            
            if weapon_rect.collidepoint(mouse_pos):
                self.dragging_weapon = weapon
                self.drag_offset = (mouse_pos[0] - weapon_rect.x, mouse_pos[1] - weapon_rect.y)
                self.tip_text = ""  # 拖动时清空提示
                break

    def _end_drag_weapon(self, mouse_pos):
        """结束拖动，装备到槽位（禁止重复装备）"""
        if not self.dragging_weapon or not self.current_user:
            self.dragging_weapon = None
            self.drag_offset = (0, 0)
            return
        
        player_weapons = self.current_user.player.weapons
        target_weapon_name = self.dragging_weapon.name
        
        # 检查是否已装备该武器（禁止重复）
        if target_weapon_name in [w.name for w in player_weapons if w]:
            self.tip_text = f"不能重复装备 {target_weapon_name}！"
            self.tip_show_time = pygame.time.get_ticks()
            self.dragging_weapon = None
            self.drag_offset = (0, 0)
            return
        
        # 装备到目标槽位
        for i, slot_rect in enumerate(self.slot_rects):
            if slot_rect.collidepoint(mouse_pos):
                self.current_user.player.equip_weapon(i, self.dragging_weapon)
                self.current_user.save_to_db()  # 保存装备状态
                self.tip_text = f"成功装备 {target_weapon_name} 到槽位{i+1}！"
                self.tip_show_time = pygame.time.get_ticks()
                break
        
        # 重置拖动状态
        self.dragging_weapon = None
        self.drag_offset = (0, 0)

    def _switch_equipment_slot(self, mouse_pos):
        """点击槽位切换当前武器"""
        for i, slot_rect in enumerate(self.slot_rects):
            if slot_rect.collidepoint(mouse_pos):
                target_weapon = self.current_user.player.weapons[i]
                if target_weapon:
                    self.current_user.player.switch_weapon(i)
                    self.tip_text = f"切换到 {target_weapon.name}（槽位{i+1}）"
                    self.tip_show_time = pygame.time.get_ticks()
                else:
                    self.tip_text = "该槽位未装备武器！"
                    self.tip_show_time = pygame.time.get_ticks()
                break