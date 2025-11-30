from pages.base_page import BasePage
import pygame
from config import *  # 导入所有颜色常量

class HomePage(BasePage):
    def __init__(self, screen: pygame.Surface, page_manager):
        super().__init__(screen, page_manager)
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        
        # 按钮配置（居中排列，统一尺寸）
        btn_width = 220
        btn_height = 55
        btn_x = (self.screen_width - btn_width) // 2
        btn_y_start = 180  # 上移，容纳4个按钮
        btn_spacing = 70  # 按钮间距
        
        # 功能按钮（包含抽奖按钮，使用配置文件颜色）
        self.btn_configs = [
            {
                "rect": pygame.Rect(btn_x, btn_y_start, btn_width, btn_height),
                "text": "开始新局",
                "color": BLUE,
                "page": "game"
            },
            {
                "rect": pygame.Rect(btn_x, btn_y_start + btn_spacing, btn_width, btn_height),
                "text": "装备管理",
                "color": GREEN,
                "page": "equipment"
            },
            {
                "rect": pygame.Rect(btn_x, btn_y_start + 2*btn_spacing, btn_width, btn_height),
                "text": "装备抽奖",
                "color": PURPLE,  # 抽奖按钮颜色
                "page": "lottery"
            },
            {
                "rect": pygame.Rect(btn_x, btn_y_start + 3*btn_spacing, btn_width, btn_height),
                "text": "退出登录",
                "color": RED,
                "page": "login"
            }
        ]
        
        # 用户信息栏（顶部右侧）
        self.user_info_rect = pygame.Rect(self.screen_width - 300, 20, 280, 60)

    def draw(self):
        self.screen.fill((245, 247, 250))  # 淡蓝色背景
        
        # 1. 绘制标题
        title_surf = self.font.render("🎮 游戏主菜单", True, BLACK)
        title_rect = title_surf.get_rect(center=(self.screen_width//2, 100))
        self.screen.blit(title_surf, title_rect)
        
        # 2. 绘制用户信息（登录后显示）
        if self.current_user:
            # 信息栏背景
            pygame.draw.rect(self.screen, WHITE, self.user_info_rect, border_radius=8)
            pygame.draw.rect(self.screen, GRAY, self.user_info_rect, 1)
            
            # 用户名和得分
            user_text = self.small_font.render(f"用户：{self.current_user.username}", True, BLACK)
            score_text = self.small_font.render(f"总积分：{self.current_user.total_score}", True, BLUE)
            
            self.screen.blit(user_text, (self.user_info_rect.x + 15, self.user_info_rect.y + 10))
            self.screen.blit(score_text, (self.user_info_rect.x + 15, self.user_info_rect.y + 35))
        
        # 3. 绘制功能按钮
        for config in self.btn_configs:
            rect = config["rect"]
            color = config["color"]
            text = config["text"]
            
            # 鼠标悬浮效果
            if rect.collidepoint(pygame.mouse.get_pos()):
                btn_color = (color[0]-30, color[1]-30, color[2]-30)  # 深色版
                text_color = WHITE
            else:
                btn_color = color
                text_color = WHITE
            
            # 绘制按钮
            pygame.draw.rect(self.screen, btn_color, rect, border_radius=8)
            
            # 绘制按钮文字（居中）
            text_surf = self.medium_font.render(text, True, text_color)
            text_rect = text_surf.get_rect(center=rect.center)
            self.screen.blit(text_surf, text_rect)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 点击功能按钮
            for config in self.btn_configs:
                if config["rect"].collidepoint(event.pos):
                    target_page = config["page"]
                    
                    # 开始新局：重置Player状态
                    if target_page == "game" and self.current_user:
                        self.current_user.player.reset()
                    
                    # 退出登录：清空所有页面的当前用户
                    if target_page == "login":
                        for page in self.page_manager.pages.values():
                            page.set_current_user(None)
                    
                    # 跳转到目标页面
                    self.page_manager.switch_page(target_page)
                    return