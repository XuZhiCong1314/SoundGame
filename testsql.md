# init
-- ==============================================
-- 游戏云端数据库初始化脚本（完整版）
-- 包含：数据库创建 + 表结构创建 + 索引优化 + 可选授权
-- ==============================================

-- 1. 创建游戏数据库（不存在则创建，避免重复执行报错）
CREATE DATABASE IF NOT EXISTS game_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci 
COMMENT '游戏用户数据存储库';

-- 2. 切换到游戏数据库
USE game_db;1

-- 3. 创建用户表（支持完整JSON嵌套字段，兼容低版本MySQL）
CREATE TABLE IF NOT EXISTS users (
    -- 基础字段
    username VARCHAR(50) PRIMARY KEY COMMENT '用户名（唯一标识，不可重复）',
    password VARCHAR(50) NOT NULL COMMENT '用户密码（建议后续优化为MD5加密存储）',
    total_score INT DEFAULT 0 COMMENT '用户总得分',
    
    -- JSON嵌套字段（存储武器和玩家数据，不设默认值兼容低版本MySQL）
    unlocked_weapons JSON COMMENT '解锁的武器列表（JSON格式，键为武器名）',
    player JSON COMMENT '玩家状态数据（JSON格式，含HP、武器栏、当前武器索引等）',
    
    -- 时间字段（自动记录创建和更新时间）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '用户创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '数据最后更新时间',
    
    -- 额外扩展字段（可选，根据游戏需求增减）
    email VARCHAR(100) DEFAULT '' COMMENT '用户邮箱（用于找回密码）',
    register_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间（与created_at功能一致，冗余备用）',
    last_login_time TIMESTAMP DEFAULT '1970-01-01 00:00:00' COMMENT '最后登录时间',
    is_active TINYINT DEFAULT 1 COMMENT '账号状态：1-正常，0-禁用'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '游戏核心用户表（本地+云端双端同步）';

-- 4. 创建索引（优化查询速度，针对常用查询字段）
-- 索引1：按得分排序查询（如排行榜功能）
CREATE INDEX idx_users_total_score ON users(total_score DESC);
-- 索引2：按最后登录时间查询（如活跃用户统计）
CREATE INDEX idx_users_last_login ON users(last_login_time DESC);
-- 索引3：邮箱查询（如找回密码功能）
CREATE INDEX idx_users_email ON users(email);

-- 5. （可选）插入测试用户数据（快速验证数据库可用性）
INSERT INTO users (username, password, total_score, unlocked_weapons, player, email)
VALUES (
    'test_admin',
    'admin123456',
    9999,
    -- unlocked_weapons JSON数据
    '{
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
            "auto_rate": null,
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
    }',
    -- player JSON数据
    '{
        "max_hp": 100,
        "current_hp": 100,
        "speed": 5,
        "is_invincible": false,
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
                "auto_rate": null,
                "active_mode": "single"
            },
            {
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
            },
            null
        ]
    }',
    'test_admin@game.com'
) ON DUPLICATE KEY UPDATE
    password = VALUES(password),
    total_score = VALUES(total_score),
    unlocked_weapons = VALUES(unlocked_weapons),
    player = VALUES(player),
    updated_at = CURRENT_TIMESTAMP;

-- 6. （可选）给数据库用户授权（解决权限不足问题）
-- 授权 XZCWin 用户操作 game_db 数据库的所有权限（本地连接）
GRANT ALL PRIVILEGES ON game_db.* TO 'XZCWin'@'localhost' IDENTIFIED BY 'xuzhicong1';
-- 若需要远程连接（如数据库在另一台服务器），授权远程访问：
-- GRANT ALL PRIVILEGES ON game_db.* TO 'XZCWin'@'%' IDENTIFIED BY 'xuzhicong1';
-- 刷新权限生效
FLUSH PRIVILEGES;

-- 7. 验证初始化结果
SELECT '数据库初始化完成！' AS result;
-- 查看表结构
DESCRIBE users;
-- 查看测试用户数据（格式化JSON）
SELECT 
    username,
    total_score,
    JSON_PRETTY(unlocked_weapons) AS unlocked_weapons,
    JSON_PRETTY(player) AS player
FROM users WHERE username = 'test_admin';