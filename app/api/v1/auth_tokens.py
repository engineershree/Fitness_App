from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.jwt_utils import create_access_token, create_refresh_token, decode_refresh_token, verify_refresh_token
from app.core.auth_dependencies import get_current_user
from app.models.user import User
from app.models.refresh_token import RefreshToken

# Configure logging for logout debugging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> RefreshTokenResponse:
    try:
        # Decode and validate the refresh token
        payload = decode_refresh_token(request.refresh_token)
        user_id = int(payload.get("sub"))
        jti = payload.get("jti")
        
        # Find the specific refresh token in database using JTI
        db_token = db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.jti == jti,  # Match specific JWT ID
            RefreshToken.is_revoked == False
        ).first()
        
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Verify the token hash
        if not verify_refresh_token(request.refresh_token, db_token.token_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if token is still valid
        if not db_token.is_valid():
            # Revoke token if it's expired
            db_token.revoke()
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )
        
        # Rotate refresh token using JTI tracking (prevents old token reuse)
        new_access_token = create_access_token(user_id)
        new_refresh_token, new_refresh_token_hash = create_refresh_token(user_id)
        
        # Extract JTI from new refresh token
        new_payload = decode_refresh_token(new_refresh_token)
        new_jti = new_payload.get("jti")
        
        # Update existing refresh token record with new token info
        db_token.token_hash = new_refresh_token_hash
        db_token.jti = new_jti  # Update to new JTI
        db_token.expires_at = datetime.utcnow() + timedelta(days=7)
        db_token.last_used_at = datetime.utcnow()
        db.commit()
        
        return RefreshTokenResponse(
            access_token=create_access_token(user_id),
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


def logout(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> Dict:
    print("=== LOGOUT REQUEST STARTED ===")
    print(f"[CONSOLE] Request type: {type(request)}")
    print(f"[CONSOLE] Request object: {request}")
    
    logger.info("=== LOGOUT REQUEST STARTED ===")
    logger.debug(f"Request received: {type(request)}")
    
    try:
        # Log incoming request details
        print("[CONSOLE] Validating request structure...")
        logger.debug("Logging request details...")
        
        if hasattr(request, 'refresh_token'):
            token_length = len(request.refresh_token) if request.refresh_token else 0
            print(f"[CONSOLE] Refresh token present: {bool(request.refresh_token)}")
            print(f"[CONSOLE] Refresh token length: {token_length}")
            print(f"[CONSOLE] Refresh token type: {type(request.refresh_token)}")
            print(f"[CONSOLE] Refresh token preview: {request.refresh_token[:20]}..." if request.refresh_token and token_length > 20 else "N/A")
            print(f"[CONSOLE] Full refresh token: {request.refresh_token}")
            
            logger.debug(f"Refresh token present: {bool(request.refresh_token)}")
            logger.debug(f"Refresh token length: {token_length}")
            logger.debug(f"Refresh token preview: {request.refresh_token[:20]}..." if request.refresh_token and token_length > 20 else "N/A")
        else:
            print("[CONSOLE] ERROR: Request object missing refresh_token attribute!")
            logger.error("Request object missing refresh_token attribute!")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid request format: missing refresh_token"
            )
        
        # Validate refresh token format
        if not request.refresh_token:
            print("[CONSOLE] ERROR: Empty refresh token received!")
            logger.error("Empty refresh token received")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Refresh token cannot be empty"
            )
        
        # Check if it's a string
        if not isinstance(request.refresh_token, str):
            print(f"[CONSOLE] ERROR: Refresh token is not a string! Type: {type(request.refresh_token)}")
            logger.error(f"Refresh token is not a string! Type: {type(request.refresh_token)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Refresh token must be a string"
            )
        
        print("[CONSOLE] Request validation passed, attempting to decode token...")
        logger.debug("Attempting to decode refresh token...")
        
        # Decode and validate the refresh token
        payload = decode_refresh_token(request.refresh_token)
        print(f"[CONSOLE] Token decoded successfully! Payload: {payload}")
        logger.debug(f"Token decoded successfully. Payload: {payload}")
        
        user_id = payload.get("sub")
        print(f"[CONSOLE] Extracted user_id: {user_id} (type: {type(user_id)})")
        logger.debug(f"Extracted user_id: {user_id}")
        
        if not user_id:
            print("[CONSOLE] ERROR: No user_id found in token payload!")
            logger.error("No user_id found in token payload")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid token format: missing user_id"
            )
        
        try:
            user_id = int(user_id)
            print(f"[CONSOLE] Converted user_id to int: {user_id}")
            logger.debug(f"Converted user_id to int: {user_id}")
        except (ValueError, TypeError) as e:
            print(f"[CONSOLE] ERROR: Invalid user_id format: {user_id} - Exception: {e}")
            logger.error(f"Invalid user_id format: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid user_id format in token"
            )
        
        print("[CONSOLE] Querying database for refresh tokens...")
        logger.debug("Querying database for refresh tokens...")
        
        # Find and revoke the specific refresh token
        db_tokens = db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        ).all()
        
        print(f"[CONSOLE] Found {len(db_tokens)} active refresh tokens for user {user_id}")
        logger.debug(f"Found {len(db_tokens)} active refresh tokens for user {user_id}")
        
        revoked_count = 0
        for i, db_token in enumerate(db_tokens):
            print(f"[CONSOLE] Checking token {i+1}/{len(db_tokens)} - Token ID: {db_token.id}")
            logger.debug(f"Checking token {i+1}/{len(db_tokens)} - Token ID: {db_token.id}")
            print(f"[CONSOLE] Token expires_at: {db_token.expires_at}")
            print(f"[CONSOLE] Token is_revoked: {db_token.is_revoked}")
            logger.debug(f"Token expires_at: {db_token.expires_at}")
            logger.debug(f"Token is_revoked: {db_token.is_revoked}")
            
            try:
                is_valid = verify_refresh_token(request.refresh_token, db_token.token_hash)
                print(f"[CONSOLE] Token {i+1} verification result: {is_valid}")
                logger.debug(f"Token {i+1} verification result: {is_valid}")
                
                if is_valid:
                    print(f"[CONSOLE] Revoking token {i+1}...")
                    logger.debug(f"Revoking token {i+1}...")
                    db_token.revoke()
                    revoked_count += 1
                    print(f"[CONSOLE] Successfully revoked token {i+1} for user {user_id}")
                    logger.info(f"Successfully revoked token {i+1} for user {user_id}")
                    break
            except Exception as e:
                print(f"[CONSOLE] Error verifying token {i+1}: {str(e)}")
                logger.error(f"Error verifying token {i+1}: {str(e)}")
                continue
        
        print(f"[CONSOLE] Total tokens revoked: {revoked_count}")
        logger.debug(f"Total tokens revoked: {revoked_count}")
        
        if revoked_count == 0:
            print(f"[CONSOLE] WARNING: No valid tokens found to revoke for user {user_id}")
            logger.warning(f"No valid tokens found to revoke for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        print("[CONSOLE] Committing database changes...")
        logger.debug("Committing database changes...")
        db.commit()
        
        print(f"[CONSOLE] Logout successful for user {user_id}")
        logger.info(f"Logout successful for user {user_id}")
        print("=== LOGOUT REQUEST COMPLETED SUCCESSFULLY ===")
        logger.info("=== LOGOUT REQUEST COMPLETED SUCCESSFULLY ===")
        
        return {"message": "Logout successful"}
        
    except HTTPException as http_ex:
        print(f"[CONSOLE] HTTP Exception in logout: {http_ex.status_code} - {http_ex.detail}")
        logger.error(f"HTTP Exception in logout: {http_ex.status_code} - {http_ex.detail}")
        print("=== LOGOUT REQUEST FAILED WITH HTTP EXCEPTION ===")
        logger.info("=== LOGOUT REQUEST FAILED WITH HTTP EXCEPTION ===")
        raise
    except Exception as e:
        print(f"[CONSOLE] UNEXPECTED ERROR in logout: {type(e).__name__}: {str(e)}")
        print(f"[CONSOLE] Exception details: {repr(e)}")
        print(f"[CONSOLE] Exception args: {e.args}")
        logger.error(f"Unexpected error in logout: {type(e).__name__}: {str(e)}")
        logger.error(f"Exception details: {repr(e)}")
        print("=== LOGOUT REQUEST FAILED WITH UNEXPECTED ERROR ===")
        logger.info("=== LOGOUT REQUEST FAILED WITH UNEXPECTED ERROR ===")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Logout processing error: {type(e).__name__}"
        )


def logout_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    try:
        # Revoke all refresh tokens for the user
        db_tokens = db.query(RefreshToken).filter(
            RefreshToken.user_id == current_user.id,
            RefreshToken.is_revoked == False
        ).all()
        
        for token in db_tokens:
            token.revoke()
        
        db.commit()
        return {"message": "Logged out from all devices successfully"}
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout from all devices"
        )
