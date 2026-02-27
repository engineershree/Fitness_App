from fastapi import APIRouter
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.admin import Admin
from .schemas import (
    AdminRegister, AdminLogin, AdminResponse, TokenResponse,
    AdminForgotPasswordEmailSchema, AdminForgotPasswordVerifySchema, AdminForgotPasswordResetSchema,
    UserRegisterSchema, UserRegisterResponse, UserResponse, UserUpdate, UserBlockResponse,
    WorkoutResponse, WorkoutCreate, WorkoutUpdate,
    MealResponse, MealCreate, MealUpdate,
    BMIClassificationResponse, BMIClassificationCreate, BMIClassificationUpdate,
    PaginatedResponse, PaginationInfo, AdminRefreshTokenRequest, AdminLogoutRequest, AdminRefreshTokenResponse
)
from .auth import register_admin, login_admin, admin_forgot_password_send_otp, admin_forgot_password_verify_otp, admin_forgot_password_reset
from .auth_tokens import refresh_admin_access_token, logout_admin
from .users import (
    register_user, get_users_paginated, get_user_by_id, update_user, delete_user
)
from .workouts import (
    create_workout, get_workouts_paginated, get_workout_by_id, update_workout, delete_workout
)
from .meals import (
    create_meal, get_meals_paginated, get_meal_by_id, update_meal, delete_meal
)
from .bmi_classification import (
    create_bmi_classification, get_bmi_classifications_paginated, get_bmi_classification_by_id, 
    update_bmi_classification, delete_bmi_classification
)


admin_router = APIRouter()

# Admin Authentication Routes
admin_router.post("/register", response_model=AdminResponse)(register_admin)
admin_router.post("/login", response_model=TokenResponse)(login_admin)
admin_router.post("/refresh-token", response_model=AdminRefreshTokenResponse)(refresh_admin_access_token)
admin_router.post("/logout", response_model=None)(logout_admin)

# Admin Forgot Password Routes
admin_router.post("/auth/forgot-password/send")(admin_forgot_password_send_otp)
admin_router.post("/auth/forgot-password/verify")(admin_forgot_password_verify_otp)
admin_router.post("/auth/forgot-password/reset")(admin_forgot_password_reset)


# User Management Routes
admin_router.post("/register-user", response_model=UserRegisterSchema)(register_user)
admin_router.get("/users", response_model=dict)(get_users_paginated)
admin_router.get("/users/{user_id}", response_model=UserResponse)(get_user_by_id)
admin_router.put("/users/{user_id}", response_model=UserResponse)(update_user)
admin_router.delete("/users/{user_id}")(delete_user)


# Workout Management Routes
admin_router.post("/workouts", response_model=WorkoutResponse)(create_workout)
admin_router.get("/workouts", response_model=dict)(get_workouts_paginated)
admin_router.get("/workouts/{workout_id}", response_model=WorkoutResponse)(get_workout_by_id)
admin_router.put("/workouts/{workout_id}", response_model=WorkoutResponse)(update_workout)
admin_router.delete("/workouts/{workout_id}")(delete_workout)


# Meal Management Routes
admin_router.post("/meals", response_model=MealResponse)(create_meal)
admin_router.get("/meals", response_model=dict)(get_meals_paginated)
admin_router.get("/meals/{meal_id}", response_model=MealResponse)(get_meal_by_id)
admin_router.put("/meals/{meal_id}", response_model=MealResponse)(update_meal)
admin_router.delete("/meals/{meal_id}")(delete_meal)


# BMI Classification Management Routes
admin_router.post("/bmi-classifications", response_model=BMIClassificationResponse)(create_bmi_classification)
admin_router.get("/bmi-classifications", response_model=dict)(get_bmi_classifications_paginated)
admin_router.get("/bmi-classifications/{bmi_id}", response_model=BMIClassificationResponse)(get_bmi_classification_by_id)
admin_router.put("/bmi-classifications/{bmi_id}", response_model=BMIClassificationResponse)(update_bmi_classification)
admin_router.delete("/bmi-classifications/{bmi_id}")(delete_bmi_classification)
