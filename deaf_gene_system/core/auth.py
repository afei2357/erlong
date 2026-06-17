#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, Optional
from datetime import datetime, timedelta
import json

from config import USER_ROLES, PERMISSIONS, SECURITY_CONFIG
from core.database import db


class AccountLockedError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class SessionExpiredError(Exception):
    pass


class AuthManager:
    def __init__(self):
        self.current_user = None
        self.session_start = None
        self.login_attempts = {}
        
    def login(self, username: str, password: str) -> Dict:
        try:
            if self._is_locked(username):
                raise AccountLockedError("账户已被锁定，请稍后再试")
            
            user = db.verify_user(username, password)
            
            if not user:
                raise InvalidCredentialsError("用户名或密码错误")
            
            self._on_login_success(user, username)
            
            return {
                "success": True,
                "message": "登录成功",
                "user": self._get_user_info(user)
            }
            
        except (AccountLockedError, InvalidCredentialsError) as e:
            self._handle_login_failure(username, str(e))
            return {
                "success": False,
                "message": str(e)
            }
    
    def _on_login_success(self, user, username):
        self.current_user = user
        self.session_start = datetime.now()
        self._reset_attempts(username)
        
        db.log_audit(
            user_id=user["id"],
            action="login",
            table_name="users",
            record_id=user["id"],
            new_values=json.dumps({"login_time": datetime.now().isoformat()})
        )
    
    def _handle_login_failure(self, username, message):
        if "锁定" not in message:
            self._record_failed_attempt(username)
    
    def logout(self):
        if self.current_user:
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
        if not self.current_user or not self.session_start:
            return False
        
        session_duration = datetime.now() - self.session_start
        if session_duration.total_seconds() > SECURITY_CONFIG["session_timeout"]:
            self.logout()
            return False
        
        return True
    
    def has_permission(self, permission: str) -> bool:
        if not self.current_user:
            return False
        
        user_role = self.current_user["role"]
        user_permissions = PERMISSIONS.get(user_role, [])
        return permission in user_permissions
    
    def get_user_info(self) -> Optional[Dict]:
        if not self.current_user:
            return None
        return self._get_user_info(self.current_user)
    
    def _get_user_info(self, user: Dict) -> Dict:
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
        if username not in self.login_attempts:
            self.login_attempts[username] = {"count": 0, "last_attempt": None}
        
        self.login_attempts[username]["count"] += 1
        self.login_attempts[username]["last_attempt"] = datetime.now()
    
    def _reset_attempts(self, username: str):
        if username in self.login_attempts:
            del self.login_attempts[username]
    
    def _is_locked(self, username: str) -> bool:
        if username not in self.login_attempts:
            return False
        
        attempts = self.login_attempts[username]
        
        if attempts["count"] >= SECURITY_CONFIG["max_login_attempts"]:
            if attempts["last_attempt"]:
                lock_duration = datetime.now() - attempts["last_attempt"]
                if lock_duration.total_seconds() < 1800:
                    return True
                else:
                    self._reset_attempts(username)
                    return False
        
        return False
    
    def change_password(self, old_password: str, new_password: str) -> Dict:
        if not self.current_user:
            return {"success": False, "message": "未登录"}
        
        if not db.verify_user(self.current_user["username"], old_password):
            return {"success": False, "message": "原密码错误"}
        
        if len(new_password) < SECURITY_CONFIG["password_min_length"]:
            return {
                "success": False,
                "message": f"密码长度至少{SECURITY_CONFIG['password_min_length']}位"
            }
        
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