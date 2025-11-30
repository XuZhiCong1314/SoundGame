from typing import Optional
from .Player import Player
from .Weapon import Weapon, DEFAULT_WEAPONS
from utils.db_utils import DBUtils

class User:
    def __init__(self, username: str, password: str):
        self.username = username  # 用户名（唯一）
        self.password = password  # 密码（实际项目需加密）
        self.total_score = 10000  # 初始积分（方便测试抽奖）
        self.unlocked_weapons = {}  # 已解锁武器
        self.player = Player()    # 关联玩家角色
        self._init_default_weapons()  # 初始解锁P92

    def _init_default_weapons(self):
        """默认解锁P92并装备"""
        default_weapon = DEFAULT_WEAPONS["P92"]
        self.unlocked_weapons[default_weapon.name] = default_weapon
        self.player.equip_weapon(0, default_weapon)

    # 添加积分
    def add_score(self, amount: int):
        self.total_score += max(0, amount)

    # 减少积分（抽奖用）
    def reduce_score(self, amount: int):
        self.total_score = max(0, self.total_score - amount)

    # 解锁新武器
    def unlock_weapon(self, weapon_name: str):
        if weapon_name in DEFAULT_WEAPONS and weapon_name not in self.unlocked_weapons:
            self.unlocked_weapons[weapon_name] = DEFAULT_WEAPONS[weapon_name]
            return True
        return False

    # 保存用户数据到文件（持久化）
    def save_to_db(self):
        db = DBUtils()
        # 武器数据序列化
        weapon_data = {name: weapon.to_dict() for name, weapon in self.unlocked_weapons.items()}
        
        user_data = {
            "username": self.username,
            "password": self.password,
            "total_score": self.total_score,
            "unlocked_weapons": weapon_data,
            "player": self.player.to_dict()
        }
        db.save_user(user_data)

    # 从文件加载用户数据
    @classmethod
    def from_db(cls, username: str):
        db = DBUtils()
        user_data = db.get_user(username)
        if not user_data:
            return None
        
        user = cls(username=user_data["username"], password=user_data["password"])
        user.total_score = user_data.get("total_score", 0)
        
        # 恢复解锁武器
        weapon_data = user_data.get("unlocked_weapons", {})
        user.unlocked_weapons = {
            name: Weapon.from_dict(weapon_info)
            for name, weapon_info in weapon_data.items()
        }
        
        # 恢复玩家装备
        user.player = Player.from_dict(user_data.get("player", {}), user.unlocked_weapons)
        return user

    # 适配登录页调用
    @classmethod
    def load_from_db(cls, username: str):
        return cls.from_db(username)