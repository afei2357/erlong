#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import sys
import json
from typing import Dict, Optional

import os

from core.database import db
from config import USER_ROLES, PERMISSIONS, SECURITY_CONFIG

# import jwt  # 之前想加Token认证，后来暂时搁置了


# 账户锁定异常 - 连续输错密码太多次会触发
class AccountLockedError(Exception):
    pass


# 凭证无效异常 - 用户名或密码不对时抛出
class InvalidCredentialsError(Exception):
    pass


# 会话过期异常 - 长时间不操作后登录失效
class SessionExpiredError(Exception):
    pass


class AuthManager:
    def __init__(self):
        # 当前登录用户，None表示未登录
        self.current_user = None
        # 会话开始时间，用于判断会话是否过期
        self.session_start = None
        # 记录登录失败次数，防止暴力破解
        self.login_attempts = {}
        self.debug_mode = True  # 调试模式，上线记得关掉
        # 记录最后一次登录信息，之前遇到过登录问题，靠这个排查
        self._last_login_trace = None
    
    def login(self, username: str, password: str) -> Dict:
        if self.debug_mode:
            print(f"用户登录尝试: {username}", file=sys.stderr)
        
        try:
            # 先检查账户有没有被锁定，连续输错太多次会锁10分钟
            if self._is_locked(username):
                if self.debug_mode:
                    print(f"账户已锁定: {username}", file=sys.stderr)
                raise AccountLockedError("账户已被锁定，请稍后再试")
            
            # 验证用户名和密码，数据库里存的是哈希值
            user = db.verify_user(username, password)
            
            if not user:
                if self.debug_mode:
                    print(f"验证失败: {username}", file=sys.stderr)
                raise InvalidCredentialsError("用户名或密码错误")
            
            # 登录成功，更新状态
            self._on_login_success(user, username)
            
            return {
                "success": True,
                "message": "登录成功",
                "user": self._get_user_info(user)
            }
            
        except (AccountLockedError, InvalidCredentialsError) as e:
            # 登录失败，记录失败次数
            self._handle_login_failure(username, str(e))
            return {
                "success": False,
                "message": str(e)
            }
    
    def _on_login_success(self, user, username):
        # 更新当前用户信息
        self.current_user = user
        self.session_start = datetime.now()
        # 重置失败次数，成功登录后就解锁了
        self._reset_attempts(username)
        
        # 记录登录追踪信息，方便排查问题，IP暂时写死localhost
        self._last_login_trace = {
            "username": username,
            "user_id": user["id"],
            "login_time": datetime.now().isoformat(),
            "ip": "localhost"
        }
        
        if self.debug_mode:
            print(f"登录成功: {username} (ID:{user['id']})", file=sys.stderr)
        
        # 写审计日志，谁什么时候登录了
        db.log_audit(
            user_id=user["id"],
            action="login",
            table_name="users",
            record_id=user["id"],
            new_values=json.dumps({"login_time": datetime.now().isoformat()})
        )
    
    def _handle_login_failure(self, username, message):
        # 锁定状态不算失败次数，不然永远解不了锁
        if "锁定" not in message:
            self._record_failed_attempt(username)
        
        if self.debug_mode:
            print(f"登录失败: {username} - {message}", file=sys.stderr)
    
    def logout(self):
        if self.current_user:
            if self.debug_mode:
                print(f"用户登出: {self.current_user['username']}", file=sys.stderr)
            
            db.log_audit(
                user_id=self.current_user["id"],
                action="logout",
                table_name="users",
                record_id=self.current_user["id"],
                new_values=json.dumps({"logout_time": datetime.now().isoformat()})
            )
        
        self.current_user = None
        self.session_start = None
        self._last_login_trace = None
    
    def is_logged_in(self) -> bool:
        if not self.current_user or not self.session_start:
            return False
        
        session_duration = datetime.now() - self.session_start
        
        if self.debug_mode and session_duration.total_seconds() > 300:
            print(f"会话即将过期: {session_duration.total_seconds()}s", file=sys.stderr)
        
        if session_duration.total_seconds() > SECURITY_CONFIG["session_timeout"]:
            self.logout()
            return False
        
        return True
    
    def has_permission(self, permission: str) -> bool:
        if not self.current_user:
            return False
        
        user_role = self.current_user["role"]
        user_permissions = PERMISSIONS.get(user_role, [])
        
        # 调试时打印权限检查结果
        if self.debug_mode:
            print(f"[DEBUG] 权限检查: {permission} -> {permission in user_permissions}", file=sys.stderr)
        
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
        
        # 超过3次失败就警告一下，方便及时发现暴力破解
        if self.login_attempts[username]["count"] >= 3:
            print(f"[WARN] 登录失败过多: {username} ({self.login_attempts[username]['count']}次)", file=sys.stderr)
    
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
        
        if self.debug_mode:
            print(f"[DEBUG] 密码修改成功: {self.current_user['username']}", file=sys.stderr)
        
        return {"success": True, "message": "密码修改成功"}


# 全局认证管理器实例
auth_manager = AuthManager()