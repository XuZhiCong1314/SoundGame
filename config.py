# 全局颜色常量（所有模块共享，避免重复定义）
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (50, 150, 255)
PURPLE = (150, 50, 255)
GREEN = (50, 255, 50)
RED = (255, 50, 50)
ORANGE = (255, 150, 50)
YELLOW = (255, 255, 0)
GRAY = (100, 100, 100)
DARK_BLUE = (20, 30, 70)
LIGHT_GRAY = (200, 200, 200)
# 游戏核心常量
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CENTER_POS = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
FPS = 60
MAX_ENEMIES = 8  # 增加最大敌人数量
MIN_SPAWN_DISTANCE = 500
MAX_SPAWN_DISTANCE = 1500
BASE_SPAWN_INTERVAL = 2000
MIN_SPAWN_INTERVAL = 800
SPAWN_SPEEDUP_RATE = 50
BULLET_MAX_DISTANCE = 3000
RELOAD_TIME = 1200  # 换弹时间（毫秒）
AUTO_SAVE_INTERVAL = 30000  # 自动存档间隔（30秒）

# 敌人配置
ENEMY_BASE_HEALTH = 8
ENEMY_ELITE_HEALTH = 15
ENEMY_BASE_DAMAGE = 20
ENEMY_ELITE_DAMAGE = 40
ENEMY_BASE_SPEED = (1.8, 2.8)  # 速度范围
ENEMY_ELITE_SPEED_MULTIPLIER = 1.4
ENEMY_ELITE_CHANCE = 0.4  # 精英怪概率
ENEMY_STRENGTH_INCREMENT = 0.3  # 每阶段强度提升比例
ENEMY_STRENGTH_INTERVAL = 60000  # 强度提升间隔（毫秒）
ENEMY_CONTACT_RADIUS = 50  # 接触玩家造成伤害的半径
ENEMY_ATTACK_INTERVAL = 1500  # 持续伤害间隔（毫秒）

# MySQL数据库配置（对接用户数据持久化）
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "XZCWin",
    "password": "xuzhicong1",
    "database": "game_db",
    "charset": "utf8mb4"
}

# DB_CONFIG = {
#     "host": "192.168.100.104",
#     "user": "XZCWin",
#     "password": "xuzhicong1",
#     "database": "game_db",
#     "charset": "utf8mb4"
# }