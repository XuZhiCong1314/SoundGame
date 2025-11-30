import pygame

class Weapon:
    def __init__(self, name, damage, bullet_speed=10, bullet_size=6, 
                 clip_capacity=30, total_ammo=120, single_rate=500, auto_rate=None):
        self.name = name
        self.damage = damage
        self.bullet_speed = bullet_speed
        self.bullet_size = bullet_size
        self.clip_capacity = clip_capacity
        self.total_ammo = total_ammo
        self.current_clip = clip_capacity
        self.current_ammo = total_ammo - self.current_clip
        self.single_rate = single_rate
        self.auto_rate = auto_rate
        self.supported_modes = ["single"]
        if auto_rate:
            self.supported_modes.append("auto")
        self.active_mode = self.supported_modes[0]
        self.color = self._get_weapon_color()

    def _get_weapon_color(self):
        color_map = {
            "M249": (50, 150, 255),
            "M416": (70, 130, 230),
            "M16A4": (90, 110, 210),
            "AUG": (110, 90, 190),
            "AKM": (130, 70, 170),
            "98K": (255, 50, 50),
            "P92": (50, 255, 50)
        }
        return color_map.get(self.name, (255, 255, 255))

    def switch_mode(self):
        if len(self.supported_modes) >= 2:
            current_idx = self.supported_modes.index(self.active_mode)
            next_idx = (current_idx + 1) % len(self.supported_modes)
            self.active_mode = self.supported_modes[next_idx]
            return True
        return False

    def get_fire_interval(self):
        if self.active_mode == "auto":
            return self.auto_rate
        return self.single_rate

    def consume_ammo(self):
        if self.current_clip > 0:
            self.current_clip -= 1
            return True
        return False

    def reload(self):
        if self.current_ammo <= 0 or self.current_clip >= self.clip_capacity:
            return 0
        need_ammo = self.clip_capacity - self.current_clip
        reload_ammo = min(need_ammo, self.current_ammo)
        self.current_clip += reload_ammo
        self.current_ammo -= reload_ammo
        return reload_ammo

    def add_reserve_ammo(self, amount):
        self.current_ammo += amount
        self.current_ammo = min(self.current_ammo, self.total_ammo * 2)

    def reset(self):
        self.current_clip = self.clip_capacity
        self.current_ammo = self.total_ammo - self.current_clip
        self.active_mode = self.supported_modes[0]

    def to_dict(self):
        return {
            "name": self.name,
            "damage": self.damage,
            "bullet_speed": self.bullet_speed,
            "bullet_size": self.bullet_size,
            "clip_capacity": self.clip_capacity,
            "total_ammo": self.total_ammo,
            "current_clip": self.current_clip,
            "current_ammo": self.current_ammo,
            "single_rate": self.single_rate,
            "auto_rate": self.auto_rate,
            "active_mode": self.active_mode
        }

    @classmethod
    def from_dict(cls, data):
        weapon = cls(
            name=data["name"],
            damage=data["damage"],
            bullet_speed=data.get("bullet_speed", 10),
            bullet_size=data.get("bullet_size", 6),
            clip_capacity=data["clip_capacity"],
            total_ammo=data["total_ammo"],
            single_rate=data.get("single_rate", 500),
            auto_rate=data.get("auto_rate")
        )
        weapon.current_clip = data.get("current_clip", weapon.clip_capacity)
        weapon.current_ammo = data.get("current_ammo", weapon.total_ammo - weapon.clip_capacity)
        weapon.active_mode = data.get("active_mode", weapon.supported_modes[0])
        return weapon

    # -------------------------- 新增：判断弹夹是否已满 --------------------------
    def is_full_clip(self):
        return self.current_clip >= self.clip_capacity

# -------------------------- DEFAULT_WEAPONS 保持不变 --------------------------
DEFAULT_WEAPONS = {
    "M249": Weapon(
        name="M249",
        damage=40,
        bullet_speed=11,
        bullet_size=6,
        clip_capacity=50,
        total_ammo=15 + (4 * 50),
        single_rate=350,
        auto_rate=80
    ),
    "M416": Weapon(
        name="M416",
        damage=40,
        bullet_speed=12,
        bullet_size=5,
        clip_capacity=30,
        total_ammo=1 + (3 * 30),
        single_rate=300,
        auto_rate=100
    ),
    "M16A4": Weapon(
        name="M16A4",
        damage=40,
        bullet_speed=12.5,
        bullet_size=5,
        clip_capacity=30,
        total_ammo=6 + (2 * 30),
        single_rate=280,
        auto_rate=90
    ),
    "AUG": Weapon(
        name="AUG",
        damage=41,
        bullet_speed=11.5,
        bullet_size=5,
        clip_capacity=30,
        total_ammo=6 + (2 * 30),
        single_rate=320,
        auto_rate=110
    ),
    "AKM": Weapon(
        name="AKM",
        damage=47,
        bullet_speed=11,
        bullet_size=5,
        clip_capacity=30,
        total_ammo=6 + (2 * 30),
        single_rate=350,
        auto_rate=120
    ),
    "98K": Weapon(
        name="98K",
        damage=79,
        bullet_speed=15,
        bullet_size=8,
        clip_capacity=5,
        total_ammo=5 + (5 * 5),
        single_rate=1500
    ),
    "P92": Weapon(
        name="P92",
        damage=50,
        bullet_speed=9,
        bullet_size=4,
        clip_capacity=7,
        total_ammo=7 + 56,
        single_rate=400
    )
}