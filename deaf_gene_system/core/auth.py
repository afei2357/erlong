#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户认证和权限管理模块
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import json

from config import USER_ROLES, PERMISSIONS, SECURITY_CONFIG
from core.database import db


class AuthManager:
    """认证管理器"""
    
    def __init__(self):
        self.current_user = None
        self.session_start = None
        self.login_attempts = {}
        
    def login(self, username: str, password: str) -> Dict:
        """用户登录"""
        # 检查登录尝试次数
        if self._is_locked(username):
            return {
                "success": False,
                "message": "账户已被锁定，请稍后再试"
            }
        
        # 验证用户
        user = db.verify_user(username, password)
        
        if user:
            # 登录成功
            self.current_user = user
            self.session_start = datetime.now()
            self._reset_attempts(username)
            
            # 记录登录日志
            db.log_audit(
                user_id=user["id"],
                action="login",
                table_name="users",
                record_id=user["id"],
                new_values=json.dumps({"login_time": datetime.now().isoformat()})
            )
            
            return {
                "success": True,
                "message": "登录成功",
                "user": self._get_user_info(user)
            }
        else:
            # 登录失败
            self._record_failed_attempt(username)
            return {
                "success": False,
                "message": "用户名或密码错误"
            }
    
    def logout(self):
        """用户登出"""
        if self.current_user:
            # 记录登出日志
            db.log_audit(
                user_id=self.current_user["id"],
                action="logout",
                table_name="users",
                record_id=self.current_user["id"],
                new_values=json.dumps({"logout_time": datetime.now().isoformat()})
            )
        
        self.current_user = None
        self.session_start = None
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        if not self.current_user or not self.session_start:
            return False
        
        # 检查会话是否超时
        session_duration = datetime.now() - self.session_start
        if session_duration.total_seconds() > SECURITY_CONFIG["session_timeout"]:
            self.logout()
            return False
        
        return True
    
    def has_permission(self, permission: str) -> bool:
        """检查用户权限"""
        if not self.current_user:
            return False
        
        user_role = self.current_user["role"]
        user_permissions = PERMISSIONS.get(user_role, [])
        return permission in user_permissions
    
    def get_user_info(self) -> Optional[Dict]:
        """获取当前用户信息"""
        if not self.current_user:
            return None
        return self._get_user_info(self.current_user)
    
    def _get_user_info(self, user: Dict) -> Dict:
        """获取用户信息（不包含敏感信息）"""
        return {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "role_name": USER_ROLES.get(user["role"], "未知"),
            "real_name": user.get("real_name", ""),
            "permissions": PERMISSIONS.get(user["role"], []),
            "last_login": user.get("last_login")
        }
    
    def _record_failed_attempt(self, username: str):
        """记录失败登录尝试"""
        if username not in self.login_attempts:
            self.login_attempts[username] = {"count": 0, "last_attempt": None}
        
        self.login_attempts[username]["count"] += 1
        self.login_attempts[username]["last_attempt"] = datetime.now()
    
    def _reset_attempts(self, username: str):
        """重置登录尝试次数"""
        if username in self.login_attempts:
            del self.login_attempts[username]
    
    def _is_locked(self, username: str) -> bool:
        """检查账户是否被锁定"""
        if username not in self.login_attempts:
            return False
        
        attempts = self.login_attempts[username]
        
        # 检查尝试次数
        if attempts["count"] >= SECURITY_CONFIG["max_login_attempts"]:
            # 检查锁定时间（30分钟）
            if attempts["last_attempt"]:
                lock_duration = datetime.now() - attempts["last_attempt"]
                if lock_duration.total_seconds() < 1800:  # 30分钟
                    return True
                else:
                    # 锁定时间已过，重置
                    self._reset_attempts(username)
                    return False
        
        return False
    
    def change_password(self, old_password: str, new_password: str) -> Dict:
        """修改密码"""
        if not self.current_user:
            return {"success": False, "message": "未登录"}
        
        # 验证旧密码
        if not db.verify_user(self.current_user["username"], old_password):
            return {"success": False, "message": "原密码错误"}
        
        # 验证新密码强度
        if len(new_password) < SECURITY_CONFIG["password_min_length"]:
            return {
                "success": False,
                "message": f"密码长度至少{SECURITY_CONFIG['password_min_length']}位"
            }
        
        # 更新密码
        hashed_password = db.hash_password(new_password)
        db.execute_query(
            "UPDATE users SET password = ? WHERE id = ?",
            (hashed_password, self.current_user["id"])
        )
        db.commit()
        
        # 记录审计日志
        db.log_audit(
            user_id=self.current_user["id"],
            action="change_password",
            table_name="users",
            record_id=self.current_user["id"]
        )
        
        return {"success": True, "message": "密码修改成功"}


# 全局认证管理器实例
auth_manager = AuthManager()