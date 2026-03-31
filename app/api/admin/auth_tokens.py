
#Admin JWT Token Management APIs - Refresh and Logout endpoints

from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.models.admin import Admin, AdminRefreshToken
from .auth import decode_refresh_token, create_access_token, create_refresh_token, verify_refresh_token

# Configure logging for admin logout debugging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AdminRefreshTokenRequest(BaseModel):
    """Request schema for admin token refresh"""
    refresh_token: str


class AdminRefreshTokenResponse(BaseModel):
    """Response schema for admin token refresh"""
    access_token: str
    refresh_token: str  # Optional: new refresh token if rotation is enabled
    token_type: str = "bearer"


class AdminLogoutRequest(BaseModel):
    """Request schema for admin logout"""
    refresh_token: str


def refresh_admin_access_token(
        request: AdminRefreshTokenRequest,
        db: Session = Depends(get_db)
):

    refresh_token_str = request.refresh_token

    # Decode and validate refresh token structure
    try:
        payload = decode_refresh_token(refresh_token_str)
        admin_id = payload.get("admin_id")
        jti = payload.get("jti")
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token format"
        )

    # Find the specific refresh token in database using JTI
    db_refresh_token = db.query(AdminRefreshToken).filter(
        AdminRefreshToken.admin_id == admin_id,
        AdminRefreshToken.jti == jti,
        AdminRefreshToken.is_revoked == False
    ).first()

    if not db_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or revoked"
        )

    # Verify the refresh token hash matches stored hash
    if not verify_refresh_token(refresh_token_str, db_refresh_token.token_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Check if refresh token has expired
    if db_refresh_token.is_expired():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )

    try:
        # STEP 1: Generate new access token
        new_access_token = create_access_token(data={"admin_id": admin_id})

        # STEP 2: Generate new refresh token
        new_refresh_token, new_token_hash = create_refresh_token(admin_id=admin_id)

        # STEP 3: Extract JTI from new refresh token
        new_payload = decode_refresh_token(new_refresh_token)
        new_jti = new_payload.get("jti")

        # STEP 4: Update the existing refresh token record (like user system)
        db_refresh_token.token_hash = new_token_hash
        db_refresh_token.jti = new_jti  # Update to new JTI
        db_refresh_token.expires_at = datetime.utcnow() + timedelta(days=7)
        db_refresh_token.last_used_at = datetime.utcnow()

        # STEP 5: Commit changes
        db.commit()

        return AdminRefreshTokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    except Exception as e:
        # Rollback on any error
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


def logout_admin(
        request: AdminLogoutRequest,
        db: Session = Depends(get_db)
):
    print("=== ADMIN LOGOUT REQUEST STARTED ===")
    print(f"[CONSOLE] Admin logout request type: {type(request)}")
    print(f"[CONSOLE] Admin logout request object: {request}")
    
    logger.info("=== ADMIN LOGOUT REQUEST STARTED ===")
    logger.debug(f"Admin logout request received: {type(request)}")

    try:
        # Log incoming request details
        print("[CONSOLE] Validating admin logout request structure...")
        logger.debug("Logging admin logout request details...")
        
        if hasattr(request, 'refresh_token'):
            token_length = len(request.refresh_token) if request.refresh_token else 0
            print(f"[CONSOLE] Admin refresh token present: {bool(request.refresh_token)}")
            print(f"[CONSOLE] Admin refresh token length: {token_length}")
            print(f"[CONSOLE] Admin refresh token type: {type(request.refresh_token)}")
            print(f"[CONSOLE] Admin refresh token preview: {request.refresh_token[:20]}..." if request.refresh_token and token_length > 20 else "N/A")
            print(f"[CONSOLE] Full admin refresh token: {request.refresh_token}")
            
            logger.debug(f"Admin refresh token present: {bool(request.refresh_token)}")
            logger.debug(f"Admin refresh token length: {token_length}")
            logger.debug(f"Admin refresh token preview: {request.refresh_token[:20]}..." if request.refresh_token and token_length > 20 else "N/A")
        else:
            print("[CONSOLE] ERROR: Admin request object missing refresh_token attribute!")
            logger.error("Admin request object missing refresh_token attribute!")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid request format: missing refresh_token"
            )

        refresh_token_str = request.refresh_token

        # Validate refresh token format
        if not refresh_token_str:
            print("[CONSOLE] ERROR: Empty admin refresh token received!")
            logger.error("Empty admin refresh token received")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Refresh token cannot be empty"
            )

        # Check if it's a string
        if not isinstance(refresh_token_str, str):
            print(f"[CONSOLE] ERROR: Admin refresh token is not a string! Type: {type(refresh_token_str)}")
            logger.error(f"Admin refresh token is not a string! Type: {type(refresh_token_str)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Refresh token must be a string"
            )

        print("[CONSOLE] Admin request validation passed, attempting to decode token...")
        # Decode and validate refresh token structure
        logger.debug("Attempting to decode admin refresh token...")
        try:
            payload = decode_refresh_token(refresh_token_str)
            print(f"[CONSOLE] Admin token decoded successfully! Payload: {payload}")
            logger.debug(f"Admin token decoded successfully. Payload: {payload}")
            
            admin_id = payload.get("admin_id")
            jti = payload.get("jti")
            
            print(f"[CONSOLE] Extracted admin_id: {admin_id} (type: {type(admin_id)})")
            print(f"[CONSOLE] Extracted jti: {jti} (type: {type(jti)})")
            logger.debug(f"Extracted admin_id: {admin_id}")
            logger.debug(f"Extracted jti: {jti}")
            
            if not admin_id:
                print("[CONSOLE] ERROR: No admin_id found in token payload!")
                logger.error("No admin_id found in token payload")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid token format: missing admin_id"
                )
            
            if not jti:
                print("[CONSOLE] ERROR: No jti found in token payload!")
                logger.error("No jti found in token payload")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid token format: missing jti"
                )
                
        except HTTPException:
            raise
        except Exception as decode_ex:
            print(f"[CONSOLE] ERROR: Error decoding admin refresh token: {type(decode_ex).__name__}: {str(decode_ex)}")
            logger.error(f"Error decoding admin refresh token: {type(decode_ex).__name__}: {str(decode_ex)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid refresh token format"
            )

        print(f"[CONSOLE] Querying database for admin refresh token with admin_id: {admin_id}, jti: {jti}")
        logger.debug(f"Querying database for admin refresh token with admin_id: {admin_id}, jti: {jti}")
        
        # Find the specific refresh token in database using JTI
        db_refresh_token = db.query(AdminRefreshToken).filter(
            AdminRefreshToken.admin_id == admin_id,
            AdminRefreshToken.jti == jti
        ).first()

        print(f"[CONSOLE] Database query result: {db_refresh_token}")
        logger.debug(f"Database query result: {db_refresh_token}")
        
        # Strict validation: Return 401 if token not found
        if not db_refresh_token:
            print(f"[CONSOLE] WARNING: No admin refresh token found for admin_id: {admin_id}, jti: {jti}")
            logger.warning(f"No admin refresh token found for admin_id: {admin_id}, jti: {jti}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found"
            )

        print(f"[CONSOLE] Found admin token - ID: {db_refresh_token.id}, is_revoked: {db_refresh_token.is_revoked}, expires_at: {db_refresh_token.expires_at}")
        logger.debug(f"Found admin token - ID: {db_refresh_token.id}, is_revoked: {db_refresh_token.is_revoked}, expires_at: {db_refresh_token.expires_at}")

        # Strict validation: Return 401 if token already revoked
        if db_refresh_token.is_revoked:
            print(f"[CONSOLE] WARNING: Admin refresh token already revoked for admin_id: {admin_id}")
            logger.warning(f"Admin refresh token already revoked for admin_id: {admin_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token already revoked"
            )

        # Strict validation: Return 401 if token expired
        if db_refresh_token.is_expired():
            print(f"[CONSOLE] WARNING: Admin refresh token expired for admin_id: {admin_id}")
            logger.warning(f"Admin refresh token expired for admin_id: {admin_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )

        # Verify the token hash before revoking (extra security)
        print("[CONSOLE] Verifying admin refresh token hash...")
        logger.debug("Verifying admin refresh token hash...")
        try:
            is_hash_valid = verify_refresh_token(refresh_token_str, db_refresh_token.token_hash)
            print(f"[CONSOLE] Admin token hash verification result: {is_hash_valid}")
            logger.debug(f"Admin token hash verification result: {is_hash_valid}")
            
            if not is_hash_valid:
                print(f"[CONSOLE] ERROR: Admin refresh token hash verification failed for admin_id: {admin_id}")
                logger.error(f"Admin refresh token hash verification failed for admin_id: {admin_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
        except Exception as hash_ex:
            print(f"[CONSOLE] ERROR: Error during admin token hash verification: {type(hash_ex).__name__}: {str(hash_ex)}")
            logger.error(f"Error during admin token hash verification: {type(hash_ex).__name__}: {str(hash_ex)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Token verification failed"
            )

        try:
            print(f"[CONSOLE] Revoking admin refresh token for admin_id: {admin_id}")
            # Revoke the refresh token
            db_refresh_token.is_revoked = True
            
            print("[CONSOLE] Committing admin logout database changes...")
            logger.debug("Committing admin logout database changes...")
            db.commit()
            
            print(f"[CONSOLE] Admin logout successful for admin_id: {admin_id}")
            logger.info(f"Admin logout successful for admin_id: {admin_id}")
            print("=== ADMIN LOGOUT REQUEST COMPLETED SUCCESSFULLY ===")
            logger.info("=== ADMIN LOGOUT REQUEST COMPLETED SUCCESSFULLY ===")

            return {"message": "Logout successful"}

        except Exception as db_ex:
            print(f"[CONSOLE] ERROR: Database error during admin logout: {type(db_ex).__name__}: {str(db_ex)}")
            logger.error(f"Database error during admin logout: {type(db_ex).__name__}: {str(db_ex)}")
            # Rollback on any error
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout failed due to database error"
            )

    except HTTPException as http_ex:
        print(f"[CONSOLE] HTTP Exception in admin logout: {http_ex.status_code} - {http_ex.detail}")
        logger.error(f"HTTP Exception in admin logout: {http_ex.status_code} - {http_ex.detail}")
        print("=== ADMIN LOGOUT REQUEST FAILED WITH HTTP EXCEPTION ===")
        logger.info("=== ADMIN LOGOUT REQUEST FAILED WITH HTTP EXCEPTION ===")
        raise
    except Exception as e:
        print(f"[CONSOLE] UNEXPECTED ERROR in admin logout: {type(e).__name__}: {str(e)}")
        print(f"[CONSOLE] Exception details: {repr(e)}")
        print(f"[CONSOLE] Exception args: {e.args}")
        logger.error(f"Unexpected error in admin logout: {type(e).__name__}: {str(e)}")
        logger.error(f"Exception details: {repr(e)}")
        print("=== ADMIN LOGOUT REQUEST FAILED WITH UNEXPECTED ERROR ===")
        logger.info("=== ADMIN LOGOUT REQUEST FAILED WITH UNEXPECTED ERROR ===")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Admin logout processing error: {type(e).__name__}"
        )
