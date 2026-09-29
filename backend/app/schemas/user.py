"""AidFlow AI - User Schemas"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime


class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    occupation: Optional[str] = None
    category: Optional[str] = None  # SC/ST/OBC/General
    annual_income: Optional[float] = None
    land_holding_acres: Optional[float] = None
    is_bpl: Optional[bool] = None
    is_disabled: Optional[bool] = None


class UserProfileResponse(BaseModel):
    id: str
    user_id: str
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    occupation: Optional[str] = None
    category: Optional[str] = None
    annual_income: Optional[float] = None
    land_holding_acres: Optional[float] = None
    is_bpl: Optional[bool] = None
    is_disabled: Optional[bool] = None
    updated_at: Optional[datetime] = None


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
    email: str
