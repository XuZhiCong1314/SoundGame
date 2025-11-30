import sys
import os
from utils.db_utils import DBUtils

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_game_flow():
    """测试游戏中的数据读写流程"""
    db = DBUtils()
    username = "xzc"

    # 1. 获取用户数据
    user = db.get_user(username)
    if not user:
        print(f"❌ 用户 [{username}] 不存在，创建新用户...")
        db.save_user({
            "username": username,
            "password": "123456"
        })
        user = db.get_user(username)

    # 2. 更新玩家数据（模拟游戏中受伤）
    db.update_player_data(username, {"current_hp": 50})

    # 3. 解锁新武器（模拟游戏中解锁M16A4）
    new_weapon = {
        "M16A4": {
            "name": "M16A4",
            "damage": 40,
            "bullet_speed": 12.5,
            "bullet_size": 5,
            "clip_capacity": 30,
            "total_ammo": 66,
            "current_clip": 30,
            "current_ammo": 36,
            "single_rate": 280,
            "auto_rate": 90,
            "active_mode": "single"
        }
    }
    db.update_unlocked_weapons(username, new_weapon)

    # 4. 更新玩家武器列表（装备新解锁的武器）
    user = db.get_user(username)
    user["player"]["weapons"][2] = new_weapon["M16A4"]
    user["player"]["current_weapon_index"] = 2  # 切换到第2把武器
    db.save_user(user)

    # 5. 读取数据并使用（模拟游戏加载）
    user = db.get_user(username)
    print(f"\n✅ 游戏加载成功！")
    print(f"当前玩家HP：{user['player']['current_hp']}")
    print(f"当前使用武器索引：{user['player']['current_weapon_index']}")
    
    # 安全获取当前武器（避免索引错误）
    current_index = user["player"]["current_weapon_index"]
    if 0 <= current_index < len(user["player"]["weapons"]):
        current_weapon = user["player"]["weapons"][current_index]
        if current_weapon:
            print(f"当前使用武器：{current_weapon['name']}，伤害：{current_weapon['damage']}")
        else:
            print(f"当前武器栏位为空，自动切换到默认武器")
            current_index = 0
            current_weapon = user["player"]["weapons"][current_index]
            print(f"切换到默认武器：{current_weapon['name']}")
    else:
        print(f"武器索引无效，使用默认武器")
        current_index = 0
        current_weapon = user["player"]["weapons"][current_index]
        print(f"当前使用武器：{current_weapon['name']}")

if __name__ == "__main__":
    test_game_flow()