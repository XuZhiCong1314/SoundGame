from pages.base_page import BasePage
from core.Weapon import DEFAULT_WEAPONS
import pygame
import random
from config import *

class LotteryPage(BasePage):
    def __init__(self, screen: pygame.Surface, page_manager):
        super().__init__(screen, page_manager)
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        
        # 页面元素
        self.back_btn_rect = pygame.Rect(50, 30, 100, 35)
        self.lottery_btn_rect = pygame.Rect(
            self.screen_width//2 - 120,
            self.screen_height - 150,
            240, 60
        )
        
        # 抽奖配置
        self.lottery_cost = 3000  # 3000积分一次
        self.lottery_pool = list(DEFAULT_WEAPONS.values())  # 你的7把武器
        
        # 抽奖状态
        self.is_drawing = False
        self.draw_progress = 0
        self.result_weapon = None
        self.result_show_time = 0

    def update(self, dt: float):
        """抽奖动画更新"""
        if self.is_drawing:
            self.draw_progress += dt * 40
            if self.draw_progress >= 100:
                self.is_drawing = False
                self.result_show_time = pygame.time.get_ticks()

    def draw(self):
        self.screen.fill(DARK_BLUE)
        
        # 标题
        title_surf = self.font.render("🎁 装备抽奖", True, YELLOW)
        self.screen.blit(title_surf, (self.screen_width//2 - 130, 50))
        
        # 积分信息
        current_score = self.current_user.total_score if self.current_user else 0
        score_surf = self.medium_font.render(f"当前积分：{current_score}", True, WHITE)
        cost_surf = self.medium_font.render(f"抽奖消耗：{self.lottery_cost} 积分", True, RED)
        self.screen.blit(score_surf, (50, 120))
        self.screen.blit(cost_surf, (self.screen_width - 300, 120))
        
        # 抽奖区域
        self._draw_lottery_area()
        
        # 按钮
        self._draw_lottery_button()
        self._draw_back_button()

    def _draw_lottery_area(self):
        """绘制抽奖区域"""
        area_rect = pygame.Rect(
            self.screen_width//2 - 350,
            180,
            700,
            300
        )
        
        # 区域背景
        pygame.draw.rect(self.screen, (50, 50, 100), area_rect, border_radius=10)
        pygame.draw.rect(self.screen, BLUE, area_rect, 3, border_radius=10)
        
        if not self.current_user:
            tip_surf = self.medium_font.render("请先登录后进行抽奖", True, RED)
            self.screen.blit(tip_surf, (area_rect.centerx - tip_surf.get_width()//2, area_rect.centery))
        
        elif self.is_drawing:
            # 抽奖动画
            weapon_index = int(self.draw_progress) % len(self.lottery_pool)
            anim_text = self.lottery_pool[weapon_index].name
            anim_surf = self.font.render(anim_text, True, WHITE)
            self.screen.blit(anim_surf, (area_rect.centerx - anim_surf.get_width()//2, area_rect.centery))
        
        elif self.result_weapon:
            # 显示结果（3秒）
            if pygame.time.get_ticks() - self.result_show_time < 3000:
                name_surf = self.font.render(f"恭喜获得：{self.result_weapon.name}", True, YELLOW)
                attr_surf = self.small_font.render(
                    f"伤害：{self.result_weapon.damage} | 弹夹：{self.result_weapon.clip_capacity}",
                    True, WHITE
                )
                self.screen.blit(name_surf, (area_rect.centerx - name_surf.get_width()//2, area_rect.centery - 40))
                self.screen.blit(attr_surf, (area_rect.centerx - attr_surf.get_width()//2, area_rect.centery + 20))
            else:
                self.result_weapon = None
        
        else:
            # 未抽奖提示
            tip_surf1 = self.medium_font.render("奖池：M249、M416、M16A4、AUG、AKM、98K、P92", True, WHITE)
            tip_surf2 = self.small_font.render("未解锁→解锁武器 | 已解锁→补充弹药", True, LIGHT_GRAY)
            self.screen.blit(tip_surf1, (area_rect.centerx - tip_surf1.get_width()//2, area_rect.centery - 30))
            self.screen.blit(tip_surf2, (area_rect.centerx - tip_surf2.get_width()//2, area_rect.centery + 20))

    def _draw_lottery_button(self):
        """绘制抽奖按钮"""
        if not self.current_user:
            btn_color = GRAY
            btn_text = "请先登录"
        elif self.current_user.total_score < self.lottery_cost:
            btn_color = GRAY
            btn_text = "积分不足（需3000）"
        elif self.is_drawing or self.result_weapon:
            btn_color = GRAY
            btn_text = "抽奖中..."
        else:
            btn_color = (100, 200, 100) if self.lottery_btn_rect.collidepoint(pygame.mouse.get_pos()) else GREEN
            btn_text = f"消耗{self.lottery_cost}积分 开始抽奖"
        
        pygame.draw.rect(self.screen, btn_color, self.lottery_btn_rect, border_radius=8)
        pygame.draw.rect(self.screen, WHITE, self.lottery_btn_rect, 2, border_radius=8)
        
        btn_surf = self.small_font.render(btn_text, True, WHITE)
        self.screen.blit(btn_surf, (
            self.lottery_btn_rect.centerx - btn_surf.get_width()//2,
            self.lottery_btn_rect.centery - btn_surf.get_height()//2
        ))

    def _draw_back_button(self):
        """绘制返回按钮"""
        btn_color = (180, 50, 50) if self.back_btn_rect.collidepoint(pygame.mouse.get_pos()) else RED
        pygame.draw.rect(self.screen, btn_color, self.back_btn_rect, border_radius=5)
        
        btn_surf = self.small_font.render("返回主菜单", True, WHITE)
        self.screen.blit(btn_surf, (self.back_btn_rect.x + 10, self.back_btn_rect.y + 5))

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 返回主菜单
            if self.back_btn_rect.collidepoint(event.pos):
                self.page_manager.switch_page("home")
                self.result_weapon = None
                return
            
            # 开始抽奖
            if self.lottery_btn_rect.collidepoint(event.pos) and self.current_user:
                if self.current_user.total_score >= self.lottery_cost and not self.is_drawing and not self.result_weapon:
                    self._start_lottery()

    def _start_lottery(self):
        """执行抽奖"""
        # 扣除积分
        self.current_user.reduce_score(self.lottery_cost)
        
        # 抽取武器
        selected_weapon = random.choice(self.lottery_pool)
        self.result_weapon = selected_weapon
        
        # 处理结果
        if selected_weapon.name not in self.current_user.unlocked_weapons:
            self.current_user.unlock_weapon(selected_weapon.name)
        else:
            # 补充弹药（2个弹夹）
            self.current_user.unlocked_weapons[selected_weapon.name].add_reserve_ammo(selected_weapon.clip_capacity * 2)
        
        # 保存数据
        self.current_user.save_to_db()
        
        # 启动动画
        self.is_drawing = True
        self.draw_progress = 0