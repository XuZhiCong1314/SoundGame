# pages/base_page.py（修改 update 方法定义）
import pygame
from typing import Optional
from core.User import User

class BasePage:
    def __init__(self, screen: pygame.Surface, page_manager):
        self.screen = screen
        self.page_manager = page_manager
        self.is_active = True
        self.current_user: Optional[User] = None
        
        # 中文支持：中文字体初始化（之前配置的代码保留）
        self.font = self._get_chinese_font(40)
        self.medium_font = self._get_chinese_font(32)
        self.small_font = self._get_chinese_font(24)

    def _get_chinese_font(self, font_size: int) -> pygame.font.Font:
        """获取支持中文的字体（容错处理）"""
        try:
            return pygame.font.Font("simhei.ttf", font_size)
        except FileNotFoundError:
            try:
                return pygame.font.Font("msyh.ttc", font_size)
            except FileNotFoundError:
                return pygame.font.SysFont("SimHei", font_size)

    # 关键修复：给 update 方法添加 dt 参数（默认值 None，兼容无逻辑的子类）
    def update(self, dt: float | None = None):
        """更新页面逻辑（子类重写）"""
        pass

    def draw(self):
        """渲染页面（子类重写）"""
        pass

    def handle_event(self, event: pygame.event.Event):
        """处理事件（子类重写）"""
        pass

    def set_current_user(self, user: Optional[User]):
        """设置当前登录用户（所有页面共享）"""
        self.current_user = user