"""Persisted accounts and expiring, revocable browser sessions."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.database import Base, get_db

router = APIRouter(prefix='/auth', tags=['Accounts'])
COOKIE = 'boli_session'
SESSION_SECONDS = 60 * 60 * 24 * 7

class Account(Base):
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(254), nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)

class AccountSession(Base):
    __tablename__ = 'account_sessions'
    token_hash = Column(String(64), primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    expires_at = Column(DateTime, nullable=False)

class Credentials(BaseModel):
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)

class Registration(Credentials):
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)

def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600000).hex()
    return salt + ':' + digest

def public_user(account):
    return {'id': account.id, 'name': account.name, 'email': account.email}

def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()

def begin_session(account, request, response, db):
    old = request.cookies.get(COOKIE)
    if old:
        db.query(AccountSession).filter_by(token_hash=token_hash(old)).delete()
    db.query(AccountSession).filter(AccountSession.expires_at <= datetime.utcnow()).delete()
    token = secrets.token_urlsafe(32)
    db.add(AccountSession(token_hash=token_hash(token), account_id=account.id,
                          expires_at=datetime.utcnow() + timedelta(seconds=SESSION_SECONDS)))
    db.commit()
    response.set_cookie(COOKIE, token, max_age=SESSION_SECONDS, httponly=True,
                        secure=request.url.scheme == 'https', samesite='lax', path='/')
    response.headers['Cache-Control'] = 'no-store'
    return public_user(account)

@router.post('/signup', status_code=201)
def signup(payload: Registration, request: Request, response: Response, db: Session = Depends(get_db)):
    name = ' '.join(payload.name.split())
    if not name:
        raise HTTPException(422, 'Enter your full name.')
    account = Account(name=name, email=str(payload.email).casefold(), password_hash=password_hash(payload.password))
    db.add(account)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'An account with this email already exists. Please sign in.')
    return begin_session(account, request, response, db)

@router.post('/login')
def login(payload: Credentials, request: Request, response: Response, db: Session = Depends(get_db)):
    account = db.query(Account).filter_by(email=str(payload.email).casefold()).first()
    # Perform the same expensive hash even for an unknown email.
    salt = account.password_hash.split(':')[0] if account else '0' * 32
    candidate = password_hash(payload.password, salt)
    if not account or not hmac.compare_digest(candidate, account.password_hash):
        raise HTTPException(401, 'Email or password is incorrect. New here? Create an account.')
    return begin_session(account, request, response, db)

@router.get('/me')
def me(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE, '')
    session = db.get(AccountSession, token_hash(token)) if token else None
    account = db.get(Account, session.account_id) if session and session.expires_at > datetime.utcnow() else None
    if not account:
        raise HTTPException(401, 'Please sign in.')
    response.headers['Cache-Control'] = 'no-store'
    return public_user(account)

@router.post('/logout', status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE)
    if token:
        db.query(AccountSession).filter_by(token_hash=token_hash(token)).delete()
        db.commit()
    response.delete_cookie(COOKIE, path='/')
