from pages.base_page import BasePage
from core.User import User
import pygame
from config import *

class LoginPage(BasePage):
    def __init__(self, screen: pygame.Surface, page_manager):
        super().__init__(screen, page_manager)
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        
        # 输入框配置
        self.input_rects = {
            "username": pygame.Rect(self.screen_width//2 - 150, 250, 300, 45),
            "password": pygame.Rect(self.screen_width//2 - 150, 330, 300, 45)
        }
        # 输入状态
        self.active_input = None  # 当前激活的输入框
        self.input_texts = {"username": "", "password": ""}
        
        # 按钮配置
        self.login_btn_rect = pygame.Rect(self.screen_width//2 - 150, 420, 300, 50)
        self.register_btn_rect = pygame.Rect(self.screen_width//2 - 150, 490, 300, 50)
        
        # 提示信息
        self.tip_text = ""
        self.tip_color = RED

    def draw(self):
        self.screen.fill((245, 247, 250))  # 淡蓝色背景
        
        # 标题
        title_surf = self.font.render("用户登录", True, BLUE)
        self.screen.blit(title_surf, (self.screen_width//2 - 100, 150))
        
        # 输入框标签
        username_label = self.medium_font.render("用户名", True, BLACK)
        password_label = self.medium_font.render("密码", True, BLACK)
        self.screen.blit(username_label, (self.screen_width//2 - 200, 255))
        self.screen.blit(password_label, (self.screen_width//2 - 200, 335))
        
        # 绘制输入框
        for name, rect in self.input_rects.items():
            # 激活状态高亮
            if self.active_input == name:
                border_color = BLUE
                bg_color = (255, 255, 255)
            else:
                border_color = GRAY
                bg_color = (240, 240, 240)
            
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)
            pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=5)
            
            # 绘制输入文本（密码隐藏为*）
            if name == "password":
                display_text = "*" * len(self.input_texts[name])
            else:
                display_text = self.input_texts[name]
            
            text_surf = self.medium_font.render(display_text, True, BLACK)
            self.screen.blit(text_surf, (rect.x + 15, rect.y + 8))
        
        # 绘制按钮
        # 登录按钮
        if self.login_btn_rect.collidepoint(pygame.mouse.get_pos()):
            login_btn_color = (50, 150, 255)
        else:
            login_btn_color = BLUE
        pygame.draw.rect(self.screen, login_btn_color, self.login_btn_rect, border_radius=8)
        login_text = self.medium_font.render("登录", True, WHITE)
        self.screen.blit(login_text, (self.login_btn_rect.centerx - 25, self.login_btn_rect.centery - 15))
        
        # 注册按钮
        if self.register_btn_rect.collidepoint(pygame.mouse.get_pos()):
            register_btn_color = (50, 255, 150)
        else:
            register_btn_color = GREEN
        pygame.draw.rect(self.screen, register_btn_color, self.register_btn_rect, border_radius=8)
        register_text = self.medium_font.render("注册账号", True, WHITE)
        self.screen.blit(register_text, (self.register_btn_rect.centerx - 45, self.register_btn_rect.centery - 15))
        
        # 提示信息
        if self.tip_text:
            tip_surf = self.small_font.render(self.tip_text, True, self.tip_color)
            self.screen.blit(tip_surf, (self.screen_width//2 - tip_surf.get_width()//2, 390))

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 点击输入框激活
            for name, rect in self.input_rects.items():
                if rect.collidepoint(event.pos):
                    self.active_input = name
                    self.tip_text = ""
                    return
            
            # 点击登录按钮
            if self.login_btn_rect.collidepoint(event.pos):
                self._handle_login()
                return
            
            # 点击注册按钮
            if self.register_btn_rect.collidepoint(event.pos):
                self.page_manager.switch_page("register")
                return
        
        # 输入文本处理
        if event.type == pygame.KEYDOWN and self.active_input:
            # 退格键删除
            if event.key == pygame.K_BACKSPACE:
                self.input_texts[self.active_input] = self.input_texts[self.active_input][:-1]
            # 回车键提交
            elif event.key == pygame.K_RETURN:
                self._handle_login()
            # 普通字符输入
            else:
                if len(self.input_texts[self.active_input]) < 16:  # 限制输入长度
                    self.input_texts[self.active_input] += event.unicode

    def _handle_login(self):
        """处理登录逻辑"""
        username = self.input_texts["username"].strip()
        password = self.input_texts["password"].strip()
        
        if not username or not password:
            self.tip_text = "用户名和密码不能为空！"
            self.tip_color = RED
            return
        
        # 验证用户
        user = User.load_from_db(username)
        if not user:
            self.tip_text = "用户名不存在！"
            self.tip_color = RED
            return
        
        if user.password != password:
            self.tip_text = "密码错误！"
            self.tip_color = RED
            return
        
        # 登录成功：设置全局用户，切换到主菜单
        for page in self.page_manager.pages.values():
            page.set_current_user(user)
        
        self.page_manager.switch_page("home")
        # 重置输入框
        self.input_texts = {"username": "", "password": ""}
        self.active_input = None
        self.tip_text = ""