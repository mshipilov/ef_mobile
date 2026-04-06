

from sqlalchemy import ForeignKey, String, Boolean, Table, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60))
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(60))
    is_active: Mapped[bool] = mapped_column(default=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"))
    
    role: Mapped["Role"] = relationship(back_populates="users")
    

    def __repr__(self):
        return f'User with email {self.email}'
      

class Role(Base):
    __tablename__ = "role"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)
    
    users: Mapped[list["User"]] = relationship(back_populates="role")
    access_roles_rules: Mapped[list["AccessRolesRule"]] = relationship(back_populates="role")


class BusinessElement(Base):
    __tablename__ = "business_element"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)

    access_roles_rules: Mapped[list["AccessRolesRule"]] = relationship(back_populates="business_element")

class AccessRolesRule(Base):
    __tablename__ = "access_roles_rule"
    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"))
    business_element_id: Mapped[int] = mapped_column(ForeignKey("business_element.id"))
    read_permission: Mapped[bool] = mapped_column(nullable=True)
    read_all_permission: Mapped[bool] = mapped_column(nullable=True)
    create_permission: Mapped[bool] = mapped_column(nullable=True)
    update_permission: Mapped[bool] = mapped_column(nullable=True)
    update_all_permission: Mapped[bool] = mapped_column(nullable=True)
    delete_permission: Mapped[bool] = mapped_column(nullable=True)
    delete_all_permission: Mapped[bool] = mapped_column(nullable=True)

    role: Mapped["Role"] = relationship(back_populates="access_roles_rules")
    business_element: Mapped["BusinessElement"] = relationship(back_populates="access_roles_rules")


   


