import json
import os
import pymysql
from pymysql.err import OperationalError, ProgrammingError
from config import DB_CONFIG

DB_PATH = "user_db.json"

class DBUtils:
    def __init__(self):
        self._init_local_db()
        self.cloud_conn = None
        self.db_config = DB_CONFIG

    def _init_local_db(self):
        if not os.path.exists(DB_PATH):
            with open(DB_PATH, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)

    def _get_cloud_conn(self):
        if self.cloud_conn and self.cloud_conn.open:
            return self.cloud_conn
        
        try:
            self.cloud_conn = pymysql.connect(**self.db_config)
            print("✅ 云端MySQL连接成功")
            return self.cloud_conn
        except OperationalError as e:
            print(f"❌ 云端MySQL连接失败：{e}")
            print(f"当前配置：{self.db_config}")
            return None

    def _get_default_unlocked_weapons(self):
        """默认解锁武器（P92）"""
        return {
            "P92": {
                "name": "P92",
                "damage": 50,
                "bullet_speed": 9,
                "bullet_size": 4,
                "clip_capacity": 7,
                "total_ammo": 63,
                "current_clip": 7,
                "current_ammo": 56,
                "single_rate": 400,
                "auto_rate": None,
                "active_mode": "single"
            }
        }

    def _get_default_player(self):
        """默认玩家数据（确保weapons列表长度为3，避免索引错误）"""
        default_weapon = self._get_default_unlocked_weapons()["P92"]
        return {
            "max_hp": 100,
            "current_hp": 100,
            "speed": 5,
            "is_invincible": False,
            "current_weapon_index": 0,  # 默认使用第0把武器
            "weapons": [default_weapon, None, None]  # 固定长度3
        }

    def _add_missing_fields(self):
        """添加缺失字段（JSON字段不设置默认值，兼容低版本MySQL）"""
        conn = self._get_cloud_conn()
        if not conn:
            return False

        # JSON字段不设置默认值（解决1101错误）
        required_fields = {
            "total_score": "INT DEFAULT 0 COMMENT '用户总得分'",
            "unlocked_weapons": "JSON COMMENT '解锁的武器（JSON格式）'",
            "player": "JSON COMMENT '玩家数据（JSON格式）'",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'"
        }

        try:
            with conn.cursor() as cursor:
                # 获取已存在字段
                cursor.execute("""
                    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'users'
                """, (self.db_config["database"],))
                existing_fields = [row[0] for row in cursor.fetchall()]
                print(f"✅ 当前表中已存在的字段：{existing_fields}")

                # 添加缺失字段
                for field_name, field_def in required_fields.items():
                    if field_name not in existing_fields:
                        alter_sql = f"ALTER TABLE users ADD COLUMN {field_name} {field_def};"
                        cursor.execute(alter_sql)
                        print(f"✅ 已添加缺失字段：{field_name}")
                    else:
                        print(f"✅ 字段 {field_name} 已存在，无需添加")
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"❌ 添加缺失字段失败：{e}")
            return False

    def _ensure_table_valid(self):
        """确保表存在且字段完整（JSON字段不设默认值）"""
        conn = self._get_cloud_conn()
        if not conn:
            return False

        try:
            with conn.cursor() as cursor:
                # 创建表（JSON字段不设默认值，兼容低版本MySQL）
                create_sql = """
                CREATE TABLE IF NOT EXISTS users (
                    username VARCHAR(50) PRIMARY KEY COMMENT '用户名（唯一）',
                    password VARCHAR(50) NOT NULL COMMENT '用户密码',
                    total_score INT DEFAULT 0 COMMENT '用户总得分',
                    unlocked_weapons JSON COMMENT '解锁的武器（JSON格式）',
                    player JSON COMMENT '玩家数据（JSON格式）',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '游戏用户表';
                """
                cursor.execute(create_sql)
                print("✅ 用户表已存在（或已创建）")

                # 补全缺失字段
                self._add_missing_fields()
            
            return True
        except Exception as e:
            conn.rollback()
            print(f"❌ 确保表结构有效失败：{e}")
            return False

    # -------------------------- 本地存储操作 --------------------------
    def _read_local_db(self) -> dict:
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 读取本地数据库失败：{e}")
            return {}

    def _write_local_db(self, db_data: dict):
        try:
            with open(DB_PATH, "w", encoding="utf-8") as f:
                json.dump(db_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 写入本地数据库失败：{e}")

    # -------------------------- 云端存储操作 --------------------------
    def _sync_to_cloud(self, user_data: dict):
        """同步完整用户数据到云端（JSON字段手动处理默认值）"""
        conn = self._get_cloud_conn()
        if not conn:
            print("❌ 云端连接失败，跳过同步")
            return False

        self._ensure_table_valid()

        # 补全默认值（JSON字段为空时手动设置默认值）
        user_data.setdefault("total_score", 0)
        unlocked_weapons = user_data.get("unlocked_weapons") or self._get_default_unlocked_weapons()
        player = user_data.get("player") or self._get_default_player()

        try:
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO users (username, password, total_score, unlocked_weapons, player)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    password = VALUES(password),
                    total_score = VALUES(total_score),
                    unlocked_weapons = VALUES(unlocked_weapons),
                    player = VALUES(player),
                    updated_at = CURRENT_TIMESTAMP
                """
                # 字典转JSON字符串（空值时传入默认JSON）
                cursor.execute(
                    sql,
                    (
                        user_data["username"],
                        user_data["password"],
                        user_data["total_score"],
                        json.dumps(unlocked_weapons, ensure_ascii=False),
                        json.dumps(player, ensure_ascii=False)
                    )
                )
            conn.commit()
            print(f"✅ 用户 [{user_data['username']}] 已完整同步到云端")
            return True
        except Exception as e:
            conn.rollback()
            print(f"❌ 同步到云端失败：{e}")
            return False

    def _get_from_cloud(self, username: str) -> dict:
        """从云端获取完整用户数据（JSON字符串转字典，补全默认值）"""
        conn = self._get_cloud_conn()
        if not conn:
            return None

        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT username, password, total_score, unlocked_weapons, player
                FROM users WHERE username = %s
                """
                cursor.execute(sql, (username,))
                result = cursor.fetchone()

                if result:
                    # 处理JSON字段（为空时用默认值）
                    result["unlocked_weapons"] = json.loads(result["unlocked_weapons"]) if result["unlocked_weapons"] else self._get_default_unlocked_weapons()
                    result["player"] = json.loads(result["player"]) if result["player"] else self._get_default_player()

                    # 确保player.weapons列表长度为3（避免索引错误）
                    if len(result["player"]["weapons"]) < 3:
                        result["player"]["weapons"].extend([None] * (3 - len(result["player"]["weapons"])))
                    elif len(result["player"]["weapons"]) > 3:
                        result["player"]["weapons"] = result["player"]["weapons"][:3]

                    # 确保current_weapon_index不越界
                    max_index = len([w for w in result["player"]["weapons"] if w]) - 1
                    if result["player"]["current_weapon_index"] > max_index:
                        result["player"]["current_weapon_index"] = max_index if max_index >= 0 else 0
                return result
        except Exception as e:
            print(f"❌ 从云端获取用户 [{username}] 失败：{e}")
            return None

    # -------------------------- 对外公开方法 --------------------------
    def get_user(self, username: str) -> dict:
        if not username:
            print("❌ 用户名不能为空")
            return None

        # 1. 查本地
        local_data = self._read_local_db()
        local_user = local_data.get(username)
        if local_user:
            # 补全默认值
            local_user.setdefault("unlocked_weapons", self._get_default_unlocked_weapons())
            local_user.setdefault("player", self._get_default_player())

            # 修复weapons列表长度和索引
            self._fix_player_weapons_index(local_user["player"])

            print(f"✅ 从本地获取用户 [{username}]")
            return local_user

        # 2. 查云端并同步到本地
        cloud_user = self._get_from_cloud(username)
        if cloud_user:
            local_data[username] = cloud_user
            self._write_local_db(local_data)
            print(f"✅ 从云端同步用户 [{username}] 到本地")
            return cloud_user

        print(f"❌ 用户 [{username}] 不存在")
        return None

    def _fix_player_weapons_index(self, player_data: dict):
        """修复player.weapons列表长度和current_weapon_index索引"""
        # 确保weapons列表长度为3
        if len(player_data["weapons"]) < 3:
            player_data["weapons"].extend([None] * (3 - len(player_data["weapons"])))
        elif len(player_data["weapons"]) > 3:
            player_data["weapons"] = player_data["weapons"][:3]

        # 确保current_weapon_index不越界
        available_weapons = [w for w in player_data["weapons"] if w]
        if not available_weapons:
            # 没有可用武器时，添加默认武器
            player_data["weapons"][0] = self._get_default_unlocked_weapons()["P92"]
            player_data["current_weapon_index"] = 0
        else:
            max_index = len(available_weapons) - 1
            if player_data["current_weapon_index"] > max_index:
                player_data["current_weapon_index"] = max_index

    def save_user(self, user_data: dict):
        """保存完整用户数据（支持所有嵌套字段）"""
        required_fields = ["username", "password"]
        for field in required_fields:
            if not user_data.get(field):
                print(f"❌ 错误：{field} 不能为空")
                return

        # 补全默认值
        user_data.setdefault("total_score", 0)
        user_data.setdefault("unlocked_weapons", self._get_default_unlocked_weapons())
        user_data.setdefault("player", self._get_default_player())

        # 修复索引问题
        self._fix_player_weapons_index(user_data["player"])

        # 1. 保存到本地
        local_data = self._read_local_db()
        local_data[user_data["username"]] = user_data
        self._write_local_db(local_data)
        print(f"✅ 用户 [{user_data['username']}] 已完整保存到本地")

        # 2. 同步到云端
        self._sync_to_cloud(user_data)

    def check_user_exist(self, username: str) -> bool:
        if not username:
            return False

        local_data = self._read_local_db()
        if username in local_data:
            return True

        return self._get_from_cloud(username) is not None

    def verify_password(self, username: str, password: str) -> bool:
        user_data = self.get_user(username)
        if not user_data:
            return False
        return user_data["password"] == password

    def update_user_score(self, username: str, new_score: int):
        """更新得分（同时保留其他字段）"""
        if not username or new_score < 0:
            print("❌ 用户名不能为空，得分不能为负数")
            return

        # 获取完整用户数据
        user_data = self.get_user(username)
        if not user_data:
            print(f"❌ 用户 [{username}] 不存在")
            return

        # 更新得分
        user_data["total_score"] = new_score
        self.save_user(user_data)  # 重新保存完整数据

    def update_player_data(self, username: str, new_player_data: dict):
        """单独更新玩家数据"""
        user_data = self.get_user(username)
        if not user_data:
            print(f"❌ 用户 [{username}] 不存在")
            return

        # 合并新玩家数据（不覆盖未修改的字段）
        user_data["player"].update(new_player_data)
        # 修复索引
        self._fix_player_weapons_index(user_data["player"])
        self.save_user(user_data)
        print(f"✅ 用户 [{username}] 玩家数据已更新")

    def update_unlocked_weapons(self, username: str, new_weapons: dict):
        """单独更新解锁武器"""
        user_data = self.get_user(username)
        if not user_data:
            print(f"❌ 用户 [{username}] 不存在")
            return

        # 合并新武器数据
        user_data["unlocked_weapons"].update(new_weapons)
        self.save_user(user_data)
        print(f"✅ 用户 [{username}] 解锁武器已更新")

    def __del__(self):
        if self.cloud_conn and self.cloud_conn.open:
            self.cloud_conn.close()
            print("✅ 云端MySQL连接已关闭")

if __name__ == "__main__":
    # 自测：保存完整用户数据
    db = DBUtils()
    test_user = {
        "username": "full_test_user",
        "password": "full123",
        "total_score": 5000,
        "unlocked_weapons": {
            "P92": {
                "name": "P92",
                "damage": 50,
                "bullet_speed": 9,
                "bullet_size": 4,
                "clip_capacity": 7,
                "total_ammo": 63,
                "current_clip": 7,
                "current_ammo": 56,
                "single_rate": 400,
                "auto_rate": None,
                "active_mode": "single"
            },
            "AKM": {
                "name": "AKM",
                "damage": 47,
                "bullet_speed": 11,
                "bullet_size": 5,
                "clip_capacity": 30,
                "total_ammo": 66,
                "current_clip": 30,
                "current_ammo": 96,
                "single_rate": 350,
                "auto_rate": 120,
                "active_mode": "single"
            }
        },
        "player": {
            "max_hp": 100,
            "current_hp": 80,
            "speed": 5,
            "is_invincible": False,
            "current_weapon_index": 1,
            "weapons": [
                {
                    "name": "P92",
                    "damage": 50,
                    "bullet_speed": 9,
                    "bullet_size": 4,
                    "clip_capacity": 7,
                    "total_ammo": 63,
                    "current_clip": 7,
                    "current_ammo": 56,
                    "single_rate": 400,
                    "auto_rate": None,
                    "active_mode": "single"
                },
                {
                    "name": "AKM",
                    "damage": 47,
                    "bullet_speed": 11,
                    "bullet_size": 5,
                    "clip_capacity": 30,
                    "total_ammo": 66,
                    "current_clip": 18,
                    "current_ammo": 7,
                    "single_rate": 350,
                    "auto_rate": 120,
                    "active_mode": "auto"
                },
                None
            ]
        }
    }
    db.save_user(test_user)
    print("\n✅ 完整用户数据保存成功，读取结果：")
    print(json.dumps(db.get_user("full_test_user"), ensure_ascii=False, indent=2))