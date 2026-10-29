from fastapi import APIRouter, Depends, HTTPException, status, Request
from datetime import datetime, timezone
import uuid
from bson import ObjectId
from app.database import get_db, db_manager
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.permissions import Role, is_admin_role
from app.core.logging import AuditLogger
from app.schemas.auth import (
    UserCreate, AdminUserCreate, UserLogin, TokenResponse, RefreshTokenRequest,
    Address, ProfileUpdate, PasswordChange
)
from app.api.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
def register_customer(payload: UserCreate, request: Request, db = Depends(get_db)):
    # Check if user already exists
    existing = db.users.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists"
        )
    
    user_doc = {
        "email": payload.email.lower(),
        "full_name": payload.full_name,
        "phone": payload.phone,
        "role": Role.CUSTOMER,
        "hashed_password": get_password_hash(payload.password),
        "addresses": [],
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    result = db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    db_manager.persist_to_disk()

    AuditLogger.log_event(
        db,
        action="CUSTOMER_REGISTRATION",
        resource_type="USER",
        resource_id=user_id,
        user_id=user_id,
        user_email=payload.email,
        ip_address=request.client.host if (request and getattr(request, "client", None)) else None
    )

    access_token = create_access_token(user_id, role=Role.CUSTOMER)
    refresh_token = create_refresh_token(user_id)

    user_info = {
        "id": user_id,
        "email": payload.email.lower(),
        "full_name": payload.full_name,
        "phone": payload.phone,
        "role": Role.CUSTOMER
    }
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_info
    )

@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, request: Request, db = Depends(get_db)):
    user = db.users.find_one({"email": payload.email.lower()})
    if not user or not verify_password(payload.password, user.get("hashed_password", "")):
        AuditLogger.log_event(
            db,
            action="LOGIN_FAILED",
            resource_type="USER",
            user_email=payload.email,
            ip_address=request.client.host if (request and getattr(request, "client", None)) else None,
            status="FAILURE"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact support."
        )

    user_id = str(user["_id"])
    role = user.get("role", Role.CUSTOMER)

    # Record login
    db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login_at": datetime.now(timezone.utc)}}
    )
    db_manager.persist_to_disk()

    AuditLogger.log_event(
        db,
        action="USER_LOGIN",
        resource_type="USER",
        resource_id=user_id,
        user_id=user_id,
        user_email=user.get("email"),
        ip_address=request.client.host if (request and getattr(request, "client", None)) else None
    )

    access_token = create_access_token(user_id, role=role)
    refresh_token = create_refresh_token(user_id)

    user_info = {
        "id": user_id,
        "email": user["email"],
        "full_name": user.get("full_name", ""),
        "phone": user.get("phone"),
        "role": role
    }
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_info
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshTokenRequest, db = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    user_id = data.get("sub")
    user = None
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        pass
    if not user:
        user = db.users.find_one({"_id": user_id})

    if not user or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    role = user.get("role", Role.CUSTOMER)
    new_access_token = create_access_token(user_id, role=role)
    new_refresh_token = create_refresh_token(user_id)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user={
            "id": user_id,
            "email": user["email"],
            "full_name": user.get("full_name", ""),
            "phone": user.get("phone"),
            "role": role
        }
    )

@router.get("/me")
def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    user_data = dict(current_user)
    user_data.pop("hashed_password", None)
    return user_data

@router.put("/me")
def update_profile(
    payload: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    update_fields = {}
    if payload.full_name is not None:
        update_fields["full_name"] = payload.full_name
    if payload.phone is not None:
        update_fields["phone"] = payload.phone
    update_fields["updated_at"] = datetime.now(timezone.utc)

    db.users.update_one({"_id": current_user["_id"]}, {"$set": update_fields})
    db_manager.persist_to_disk()
    return {"message": "Profile updated successfully"}

@router.post("/addresses")
def add_address(
    address: Address,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    addr_dict = address.model_dump()
    addr_dict["id"] = str(uuid.uuid4())
    
    addresses = current_user.get("addresses", [])
    if addr_dict.get("is_default") or len(addresses) == 0:
        addr_dict["is_default"] = True
        for a in addresses:
            a["is_default"] = False
    
    addresses.append(addr_dict)
    db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"addresses": addresses, "updated_at": datetime.now(timezone.utc)}}
    )
    db_manager.persist_to_disk()
    return {"message": "Address added successfully", "address": addr_dict}

@router.delete("/addresses/{address_id}")
def delete_address(
    address_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    addresses = [a for a in current_user.get("addresses", []) if a.get("id") != address_id]
    db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"addresses": addresses, "updated_at": datetime.now(timezone.utc)}}
    )
    db_manager.persist_to_disk()
    return {"message": "Address removed successfully"}

@router.post("/change-password")
def change_password(
    payload: PasswordChange,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    if not verify_password(payload.old_password, current_user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password does not match"
        )
    db.users.update_one(
        {"_id": current_user["_id"]},
        {
            "$set": {
                "hashed_password": get_password_hash(payload.new_password),
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    db_manager.persist_to_disk()
    return {"message": "Password updated successfully"}

@router.post("/admin/create-staff", dependencies=[Depends(require_roles([Role.SUPER_ADMIN]))])
def create_staff_user(payload: AdminUserCreate, db = Depends(get_db)):
    if payload.role not in [Role.SUPER_ADMIN, Role.ADMIN, Role.ORDER_MANAGER, Role.INVENTORY_MANAGER, Role.CUSTOMER_SUPPORT]:
        raise HTTPException(status_code=400, detail="Invalid staff role")
    
    existing = db.users.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    doc = {
        "email": payload.email.lower(),
        "full_name": payload.full_name,
        "phone": payload.phone,
        "role": payload.role,
        "hashed_password": get_password_hash(payload.password),
        "is_active": True,
        "created_at": datetime.now(timezone.utc)
    }
    res = db.users.insert_one(doc)
    db_manager.persist_to_disk()
    return {"message": f"Staff user {payload.full_name} created with role {payload.role}", "id": str(res.inserted_id)}
