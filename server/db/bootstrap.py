"""数据库初始化与种子数据灌入。

这个模块承担“本地单机生产仿真”的冷启动准备：
1. 创建扩展
2. 建表
3. 灌权限/角色
4. 灌默认用户
5. 从 CSV 导入用户报告样例数据
"""

import csv
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from server.core.config import get_settings
from server.core.security import hash_password
from server.db.base import Base
from server.db.models import Permission, Role, User, UserDeviceReport
from server.db.session import SessionLocal, engine


ROLE_PERMISSIONS = {
    "user": ["kb:read", "report:read:self"],
    "admin": ["kb:read", "report:read:self", "report:read:any", "admin:knowledge:write"],
}


DEFAULT_USERS = [
    {"username": "user1001", "account_code": "1001", "full_name": "王吱呲", "location": "上海", "password": "user1001"},
    {"username": "user1002", "account_code": "1002", "full_name": "李小拖", "location": "北京", "password": "user1002"},
    {"username": "admin", "account_code": "9001", "full_name": "系统管理员", "location": "上海", "password": "admin123"},
]


class DatabaseBootstrapper:
    """数据库启动自举器。"""

    def __init__(self) -> None:
        self.settings = get_settings()

    def bootstrap(self) -> None:
        """执行完整自举流程。"""
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            self._seed_permissions_roles(db)
            self._seed_users(db)
            self._seed_reports(db)

    def _seed_permissions_roles(self, db: Session) -> None:
        """初始化权限点和角色。

        当前只做最小 RBAC：
        - user
        - admin
        """
        permissions: dict[str, Permission] = {}
        for permission_name in {item for values in ROLE_PERMISSIONS.values() for item in values}:
            permission = db.scalar(select(Permission).where(Permission.name == permission_name))
            if permission is None:
                permission = Permission(name=permission_name, description=permission_name)
                db.add(permission)
                db.flush()
            permissions[permission_name] = permission

        for role_name, permission_names in ROLE_PERMISSIONS.items():
            role = db.scalar(select(Role).where(Role.name == role_name))
            if role is None:
                role = Role(name=role_name, description=role_name)
                db.add(role)
                db.flush()
            role.permissions = [permissions[name] for name in permission_names]
        db.commit()

    def _seed_users(self, db: Session) -> None:
        """初始化默认测试账号。"""
        user_role = db.scalar(select(Role).where(Role.name == "user"))
        admin_role = db.scalar(select(Role).where(Role.name == "admin"))
        for item in DEFAULT_USERS:
            user = db.scalar(select(User).where(User.username == item["username"]))
            if user is None:
                user = User(
                    username=item["username"],
                    account_code=item["account_code"],
                    full_name=item["full_name"],
                    location=item["location"],
                    password_hash=hash_password(item["password"]),
                )
                db.add(user)
                db.flush()
            if item["username"] == "admin":
                user.roles = [admin_role]
            else:
                user.roles = [user_role]
        db.commit()

    def _seed_reports(self, db: Session) -> None:
        """从 CSV 导入用户月报样例数据到 user_device_reports。"""
        report_path = Path(self.settings.report_csv_path)
        if not report_path.exists():
            return

        with report_path.open("r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                account_code = row.get("用户ID", "").strip().strip('"')
                month = row.get("时间", "").strip().strip('"')
                if not account_code or not month:
                    continue
                user = db.scalar(select(User).where(User.account_code == account_code))
                if user is None:
                    continue
                existing = db.scalar(
                    select(UserDeviceReport).where(
                        UserDeviceReport.user_id == user.id,
                        UserDeviceReport.month == month,
                    )
                )
                if existing:
                    continue
                db.add(
                    UserDeviceReport(
                        user_id=user.id,
                        month=month,
                        feature=row.get("特征", "").strip().strip('"'),
                        efficiency=row.get("清洁效率", "").strip().strip('"'),
                        consumables=row.get("耗材", "").strip().strip('"'),
                        comparison=row.get("对比", "").strip().strip('"'),
                        raw_payload=row,
                    )
                )
            db.commit()


bootstrapper = DatabaseBootstrapper()
