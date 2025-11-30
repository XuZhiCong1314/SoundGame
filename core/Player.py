# 修正导入路径：从 core.Weapon 导入（而非 pages.base_page）
from .Weapon import Weapon

class Player:
    def __init__(self):
        # 核心属性
        self.max_hp = 100
        self.current_hp = 100
        self.speed = 5
        self.is_invincible = False  # 无敌状态
        
        # 装备系统：3个装备槽（默认None）
        self.weapons = [None, None, None]  # 关键：添加装备槽列表
        self.current_weapon_index = 0  # 当前使用的装备槽索引（默认第0槽）

    def reset(self):
        """重置玩家状态（开始新局时调用）"""
        self.current_hp = self.max_hp
        self.is_invincible = False
        # 重置武器弹药（保留装备）
        for weapon in self.weapons:
            if weapon:
                weapon.reset()  # 调用你的Weapon类的 reset 方法

    def equip_weapon(self, slot_index: int, weapon: Weapon):
        """装备武器到指定槽位（0-2）"""
        if 0 <= slot_index < 3 and weapon:
            # 复制武器实例（避免多个槽位引用同一对象导致弹药同步问题）
            weapon_copy = Weapon.from_dict(weapon.to_dict())
            self.weapons[slot_index] = weapon_copy
            # 如果装备的是当前槽位，更新当前武器
            if slot_index == self.current_weapon_index:
                self.current_weapon = weapon_copy

    def get_current_weapon(self) -> Weapon:
        """获取当前使用的武器"""
        return self.weapons[self.current_weapon_index] if self.weapons[self.current_weapon_index] else None

    def switch_weapon(self, slot_index: int):
        """切换到指定槽位的武器"""
        if 0 <= slot_index < 3 and self.weapons[slot_index]:
            self.current_weapon_index = slot_index

    def take_damage(self, damage: int):
        """受到伤害（无敌状态下无效）"""
        if not self.is_invincible:
            self.current_hp = max(0, self.current_hp - damage)

    def to_dict(self) -> dict:
        """转换为字典（用于持久化）"""
        return {
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "speed": self.speed,
            "is_invincible": self.is_invincible,
            "current_weapon_index": self.current_weapon_index,
            # 存储每个槽位的武器数据（适配你的Weapon类的 to_dict 方法）
            "weapons": [
                weapon.to_dict() if weapon else None 
                for weapon in self.weapons
            ]
        }

    @classmethod
    def from_dict(cls, data: dict, unlocked_weapons: dict):
        """从字典恢复（用于加载持久化数据）"""
        player = cls()
        player.max_hp = data.get("max_hp", 100)
        player.current_hp = data.get("current_hp", 100)
        player.speed = data.get("speed", 5)
        player.is_invincible = data.get("is_invincible", False)
        player.current_weapon_index = data.get("current_weapon_index", 0)
        
        # 恢复装备槽武器（适配你的Weapon类的 from_dict 方法）
        weapons_data = data.get("weapons", [None, None, None])
        for i, weapon_data in enumerate(weapons_data):
            if weapon_data:
                # 从已解锁武器中找到对应武器（确保数据一致性）
                weapon_name = weapon_data.get("name")
                if weapon_name in unlocked_weapons:
                    weapon = Weapon.from_dict(weapon_data)
                    player.equip_weapon(i, weapon)
        
        return player