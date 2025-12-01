import pymysql
from pymysql.err import OperationalError, ProgrammingError
import json

DB_CONFIG = {
    "host": "192.168.100.104",
    "user": "XZCWin",
    "password": "xuzhicong1",
    "database": "game_db",  # 要创建的数据库名
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}

def init_cloud_db():
    conn = None
    try:
        # 先连接到MySQL服务（不指定数据库）
        conn = pymysql.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            charset=DB_CONFIG["charset"],
            cursorclass=DB_CONFIG["cursorclass"]
        )
        with conn.cursor() as cursor:
            # 1. 创建game_db数据库
            create_db_sql = f"""
                CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} 
                CHARACTER SET utf8mb4 
                COLLATE utf8mb4_unicode_ci;
            """
            cursor.execute(create_db_sql)
            print(f"✅ 数据库 {DB_CONFIG['database']} 已创建或已存在")
            
            # 2. 使用创建好的数据库
            cursor.execute(f"USE {DB_CONFIG['database']};")
            
            # 3. 创建users表
            create_table_sql = """
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
            cursor.execute(create_table_sql)
            print("✅ users表已创建或已存在")
            
            # 4. 补全缺失字段
            cursor.execute("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'users'
            """, (DB_CONFIG["database"],))
            existing_fields = [row["COLUMN_NAME"] for row in cursor.fetchall()]
            required_fields = {
                "total_score": "INT DEFAULT 0 COMMENT '用户总得分'",
                "unlocked_weapons": "JSON COMMENT '解锁的武器（JSON格式）'",
                "player": "JSON COMMENT '玩家数据（JSON格式）'",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'",
                "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'"
            }
            for field_name, field_def in required_fields.items():
                if field_name not in existing_fields:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {field_name} {field_def};")
            
            # 5. 添加默认用户
            default_weapons = json.dumps({"P92": {"name": "P92","damage":50,"bullet_speed":9,"bullet_size":4,"clip_capacity":7,"total_ammo":63,"current_clip":7,"current_ammo":56,"single_rate":400,"auto_rate":None,"active_mode":"single"}}, ensure_ascii=False)
            default_player = json.dumps({"max_hp":100,"current_hp":100,"speed":5,"is_invincible":False,"current_weapon_index":0,"weapons":[{"name":"P92","damage":50,"bullet_speed":9,"bullet_size":4,"clip_capacity":7,"total_ammo":63,"current_clip":7,"current_ammo":56,"single_rate":400,"auto_rate":None,"active_mode":"single"},None,None]}, ensure_ascii=False)
            cursor.execute("INSERT IGNORE INTO users (username,password,total_score,unlocked_weapons,player) VALUES (%s,%s,%s,%s,%s)", ("admin","admin123",0,default_weapons,default_player))
            
            conn.commit()
            print("✅ 云端数据库初始化完成：game_db创建+表结构+默认用户")
            return True
    except OperationalError as e:
        print(f"❌ 连接失败：{e}")
        return False
    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ 初始化失败：{e}")
        return False
    finally:
        if conn and conn.open: conn.close()

if __name__ == "__main__":
    init_cloud_db()