import pygame
from pages.base_page import BasePage
from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.register_page import RegisterPage
from pages.equipment_page import EquipmentPage
from pages.game_page import GamePage
from pages.lottery_page import LotteryPage  # 导入抽奖页面

class PageManager:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.pages = {}  # {页面名称: 页面实例}
        self.current_page = None  # 当前激活页面

    def register_page(self, page_name: str, page: BasePage):
        """注册页面"""
        self.pages[page_name] = page

    def switch_page(self, page_name: str):
        """切换页面"""
        if page_name in self.pages:
            self.current_page = self.pages[page_name]
            self.current_page.is_active = True
            print(f"切换到页面：{page_name}")

    def update(self, dt: float):
        """更新当前页面逻辑"""
        if self.current_page:
            self.current_page.update(dt)

    def draw(self):
        """渲染当前页面"""
        if self.current_page:
            self.current_page.draw()

    def handle_event(self, event: pygame.event.Event):
        """处理当前页面事件"""
        if self.current_page:
            self.current_page.handle_event(event)

def main():
    # 初始化Pygame
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("游戏项目整合示例")
    clock = pygame.time.Clock()
    running = True

    # 初始化页面管理器
    page_manager = PageManager(screen)

    # 注册所有页面（包含抽奖页面，删除云端页面）
    page_manager.register_page("home", HomePage(screen, page_manager))
    page_manager.register_page("login", LoginPage(screen, page_manager))
    page_manager.register_page("register", RegisterPage(screen, page_manager))
    page_manager.register_page("equipment", EquipmentPage(screen, page_manager))
    page_manager.register_page("game", GamePage(screen, page_manager))
    page_manager.register_page("lottery", LotteryPage(screen, page_manager))  # 注册抽奖页面

    # 默认进入登录页面
    page_manager.switch_page("login")

    # 主循环
    while running:
        dt = clock.tick(60) / 1000  # 帧率60FPS，时间增量（秒）

        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            page_manager.handle_event(event)

        # 逻辑更新
        page_manager.update(dt)

        # 界面渲染w
        page_manager.draw()

        # 刷新屏幕
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()