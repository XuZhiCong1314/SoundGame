from pages.base_page import BasePage
from core.User import User
from utils.db_utils import DBUtils
import pygame
from config import *

class RegisterPage(BasePage):
    def __init__(self, screen: pygame.Surface, page_manager):
        super().__init__(screen, page_manager)
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        
        # 输入框配置
        self.input_rects = {
            "username": pygame.Rect(self.screen_width//2 - 150, 220, 300, 45),
            "password": pygame.Rect(self.screen_width//2 - 150, 300, 300, 45),
            "confirm_password": pygame.Rect(self.screen_width//2 - 150, 380, 300, 45)
        }
        # 输入状态
        self.active_input = None
        self.input_texts = {"username": "", "password": "", "confirm_password": ""}
        
        # 按钮配置
        self.register_btn_rect = pygame.Rect(self.screen_width//2 - 150, 470, 300, 50)
        self.back_btn_rect = pygame.Rect(50, 30, 100, 35)
        
        # 提示信息
        self.tip_text = ""
        self.tip_color = RED

    def draw(self):
        self.screen.fill((245, 247, 250))
        
        # 标题
        title_surf = self.font.render("用户注册", True, BLUE)
        self.screen.blit(title_surf, (self.screen_width//2 - 100, 150))
        
        # 输入框标签
        labels = {
            "username": "用户名",
            "password": "密码",
            "confirm_password": "确认密码"
        }
        for name, label in labels.items():
            label_surf = self.medium_font.render(label, True, BLACK)
            self.screen.blit(label_surf, (self.screen_width//2 - 200, self.input_rects[name].y + 5))
        
        # 绘制输入框
        for name, rect in self.input_rects.items():
            if self.active_input == name:
                border_color = BLUE
                bg_color = WHITE
            else:
                border_color = GRAY
                bg_color = (240, 240, 240)
            
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)
            pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=5)
            
            # 密码和确认密码隐藏为*
            if name in ["password", "confirm_password"]:
                display_text = "*" * len(self.input_texts[name])
            else:
                display_text = self.input_texts[name]
            
            text_surf = self.medium_font.render(display_text, True, BLACK)
            self.screen.blit(text_surf, (rect.x + 15, rect.y + 8))
        
        # 绘制按钮
        # 注册按钮
        if self.register_btn_rect.collidepoint(pygame.mouse.get_pos()):
            btn_color = (50, 255, 150)
        else:
            btn_color = GREEN
        pygame.draw.rect(self.screen, btn_color, self.register_btn_rect, border_radius=8)
        register_text = self.medium_font.render("注册", True, WHITE)
        self.screen.blit(register_text, (self.register_btn_rect.centerx - 25, self.register_btn_rect.centery - 15))
        
        # 返回按钮
        if self.back_btn_rect.collidepoint(pygame.mouse.get_pos()):
            back_color = (220, 220, 220)
        else:
            back_color = LIGHT_GRAY
        pygame.draw.rect(self.screen, back_color, self.back_btn_rect, border_radius=5)
        back_text = self.small_font.render("返回登录", True, BLACK)
        self.screen.blit(back_text, (self.back_btn_rect.x + 10, self.back_btn_rect.y + 5))
        
        # 提示信息
        if self.tip_text:
            tip_surf = self.small_font.render(self.tip_text, True, self.tip_color)
            self.screen.blit(tip_surf, (self.screen_width//2 - tip_surf.get_width()//2, 440))

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 激活输入框
            for name, rect in self.input_rects.items():
                if rect.collidepoint(event.pos):
                    self.active_input = name
                    self.tip_text = ""
                    return
            
            # 点击注册按钮
            if self.register_btn_rect.collidepoint(event.pos):
                self._handle_register()
                return
            
            # 点击返回按钮
            if self.back_btn_rect.collidepoint(event.pos):
                self.page_manager.switch_page("login")
                self.input_texts = {"username": "", "password": "", "confirm_password": ""}
                self.active_input = None
                self.tip_text = ""
                return
        
        # 输入文本处理
        if event.type == pygame.KEYDOWN and self.active_input:
            if event.key == pygame.K_BACKSPACE:
                self.input_texts[self.active_input] = self.input_texts[self.active_input][:-1]
            elif event.key == pygame.K_RETURN:
                self._handle_register()
            else:
                if len(self.input_texts[self.active_input]) < 16:
                    self.input_texts[self.active_input] += event.unicode
    def _handle_register(self):
        """处理注册逻辑"""
        username = self.input_texts["username"].strip()
        password = self.input_texts["password"].strip()
        confirm_password = self.input_texts["confirm_password"].strip()
        
        # 验证输入
        if not username or not password or not confirm_password:
            self.tip_text = "所有字段不能为空！"
            self.tip_color = RED
            return
        
        if len(username) < 3 or len(username) > 16:
            self.tip_text = "用户名长度需在3-16字符之间！"
            self.tip_color = RED
            return
        
        if len(password) < 6:
            self.tip_text = "密码长度不能少于6字符！"
            self.tip_color = RED
            return
        
        if password != confirm_password:
            self.tip_text = "两次输入的密码不一致！"
            self.tip_color = RED
            return
        
        # 检查用户名是否已存在
        db = DBUtils()
        if db.check_user_exist(username):
            self.tip_text = "用户名已被注册！"
            self.tip_color = RED
            return
        
        # 注册成功：创建用户并保存到数据库
        new_user = User(username=username, password=password)
        new_user.save_to_db()  # 自动初始化默认武器（P92）
        
        # 提示注册成功并返回登录页
        self.tip_text = "注册成功！即将跳转到登录页..."
        self.tip_color = GREEN
        
        # 延迟1秒跳转到登录页
        pygame.time.set_timer(pygame.USEREVENT, 1000)
        self.register_success = True

    def handle_event(self, event: pygame.event.Event):
        # 处理注册成功后的跳转事件
        if hasattr(self, "register_success") and self.register_success and event.type == pygame.USEREVENT:
            self.page_manager.switch_page("login")
            self.input_texts = {"username": "", "password": "", "confirm_password": ""}
            self.active_input = None
            self.tip_text = ""
            self.register_success = False
            pygame.time.set_timer(pygame.USEREVENT, 0)  # 取消定时器
            return
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 激活输入框
            for name, rect in self.input_rects.items():
                if rect.collidepoint(event.pos):
                    self.active_input = name
                    self.tip_text = ""
                    return
            
            # 点击注册按钮
            if self.register_btn_rect.collidepoint(event.pos):
                self._handle_register()
                return
            
            # 点击返回按钮
            if self.back_btn_rect.collidepoint(event.pos):
                self.page_manager.switch_page("login")
                self.input_texts = {"username": "", "password": "", "confirm_password": ""}
                self.active_input = None
                self.tip_text = ""
                return
        
        # 输入文本处理
        if event.type == pygame.KEYDOWN and self.active_input:
            if event.key == pygame.K_BACKSPACE:
                self.input_texts[self.active_input] = self.input_texts[self.active_input][:-1]
            elif event.key == pygame.K_RETURN:
                self._handle_register()
            else:
                if len(self.input_texts[self.active_input]) < 16:
                    self.input_texts[self.active_input] += event.unicode