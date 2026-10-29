from enum import Enum
from typing import List, Set

class Role(str, Enum):
    SUPER_ADMIN = "Super Admin"
    ADMIN = "Admin"
    ORDER_MANAGER = "Order Manager"
    INVENTORY_MANAGER = "Inventory Manager"
    CUSTOMER_SUPPORT = "Customer Support"
    CUSTOMER = "Customer"

class Permission(str, Enum):
    # Storefront / Customer
    VIEW_CATALOG = "catalog:view"
    MANAGE_OWN_CART = "cart:manage_own"
    MANAGE_OWN_ORDERS = "orders:manage_own"
    MANAGE_OWN_PROFILE = "profile:manage_own"
    
    # Products & Inventory
    PRODUCTS_VIEW = "products:view"
    PRODUCTS_CREATE = "products:create"
    PRODUCTS_EDIT = "products:edit"
    PRODUCTS_DELETE = "products:delete"
    INVENTORY_ADJUST = "inventory:adjust"
    
    # Categories
    CATEGORIES_MANAGE = "categories:manage"
    
    # Orders & Fulfilment
    ORDERS_VIEW_ALL = "orders:view_all"
    ORDERS_PROCESS = "orders:process"
    ORDERS_SHIP = "orders:ship"
    RETURNS_MANAGE = "returns:manage"
    
    # Customers & Support
    CUSTOMERS_VIEW = "customers:view"
    CUSTOMERS_MANAGE = "customers:manage"
    SUPPORT_TICKETS = "support:manage"
    
    # Marketing & Settings
    COUPONS_MANAGE = "coupons:manage"
    ANALYTICS_VIEW = "analytics:view"
    SETTINGS_MANAGE = "settings:manage"
    USERS_MANAGE = "users:manage"
    AUDIT_LOGS_VIEW = "audit_logs:view"

# Role to permission mapping
ROLE_PERMISSIONS: dict[str, Set[Permission]] = {
    Role.SUPER_ADMIN: set(Permission), # All permissions
    Role.ADMIN: {
        Permission.VIEW_CATALOG,
        Permission.PRODUCTS_VIEW,
        Permission.PRODUCTS_CREATE,
        Permission.PRODUCTS_EDIT,
        Permission.PRODUCTS_DELETE,
        Permission.INVENTORY_ADJUST,
        Permission.CATEGORIES_MANAGE,
        Permission.ORDERS_VIEW_ALL,
        Permission.ORDERS_PROCESS,
        Permission.ORDERS_SHIP,
        Permission.RETURNS_MANAGE,
        Permission.CUSTOMERS_VIEW,
        Permission.CUSTOMERS_MANAGE,
        Permission.SUPPORT_TICKETS,
        Permission.COUPONS_MANAGE,
        Permission.ANALYTICS_VIEW,
        Permission.SETTINGS_MANAGE,
        Permission.AUDIT_LOGS_VIEW,
    },
    Role.ORDER_MANAGER: {
        Permission.VIEW_CATALOG,
        Permission.ORDERS_VIEW_ALL,
        Permission.ORDERS_PROCESS,
        Permission.ORDERS_SHIP,
        Permission.RETURNS_MANAGE,
        Permission.CUSTOMERS_VIEW,
    },
    Role.INVENTORY_MANAGER: {
        Permission.VIEW_CATALOG,
        Permission.PRODUCTS_VIEW,
        Permission.PRODUCTS_CREATE,
        Permission.PRODUCTS_EDIT,
        Permission.INVENTORY_ADJUST,
        Permission.CATEGORIES_MANAGE,
    },
    Role.CUSTOMER_SUPPORT: {
        Permission.VIEW_CATALOG,
        Permission.ORDERS_VIEW_ALL,
        Permission.CUSTOMERS_VIEW,
        Permission.RETURNS_MANAGE,
        Permission.SUPPORT_TICKETS,
    },
    Role.CUSTOMER: {
        Permission.VIEW_CATALOG,
        Permission.MANAGE_OWN_CART,
        Permission.MANAGE_OWN_ORDERS,
        Permission.MANAGE_OWN_PROFILE,
    }
}

ADMIN_ROLES: Set[str] = {
    Role.SUPER_ADMIN,
    Role.ADMIN,
    Role.ORDER_MANAGER,
    Role.INVENTORY_MANAGER,
    Role.CUSTOMER_SUPPORT,
}

def has_permission(user_role: str, permission: Permission) -> bool:
    perms = ROLE_PERMISSIONS.get(user_role, set())
    return permission in perms

def is_admin_role(user_role: str) -> bool:
    return user_role in ADMIN_ROLES
