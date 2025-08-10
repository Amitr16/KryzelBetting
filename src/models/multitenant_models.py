"""
Updated database models for multi-tenant sports betting platform
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
import json

# Import db instance from betting.py to avoid conflicts
from .betting import db

# BetStatus and BetType enums are imported from betting.py to avoid conflicts

class SportsbookOperator(db.Model):
    """Sportsbook operators (admins) who run their own betting sites"""
    __tablename__ = 'sportsbook_operators'
    
    id = db.Column(db.Integer, primary_key=True)
    sportsbook_name = db.Column(db.String(100), unique=True, nullable=False)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120))
    subdomain = db.Column(db.String(50), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    total_revenue = db.Column(db.Float, default=0.0)
    commission_rate = db.Column(db.Float, default=0.05)
    settings = db.Column(db.Text)  # JSON field for operator-specific settings
    
    # Relationships
    users = db.relationship('User', backref='sportsbook_operator', lazy=True)
    bets = db.relationship('Bet', backref='sportsbook_operator', lazy=True)
    transactions = db.relationship('Transaction', backref='sportsbook_operator', lazy=True)
    bet_slips = db.relationship('BetSlip', backref='sportsbook_operator', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sportsbook_name': self.sportsbook_name,
            'login': self.login,
            'email': self.email,
            'subdomain': self.subdomain,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'total_revenue': self.total_revenue,
            'commission_rate': self.commission_rate,
            'settings': json.loads(self.settings) if self.settings else {}
        }
    
    def get_settings(self):
        """Get operator settings as dictionary"""
        return json.loads(self.settings) if self.settings else {}
    
    def set_settings(self, settings_dict):
        """Set operator settings from dictionary"""
        self.settings = json.dumps(settings_dict)

class SuperAdmin(db.Model):
    """Super administrators with global access"""
    __tablename__ = 'super_admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    permissions = db.Column(db.Text)  # JSON field for granular permissions
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'permissions': json.loads(self.permissions) if self.permissions else {}
        }
    
    def get_permissions(self):
        """Get permissions as dictionary"""
        return json.loads(self.permissions) if self.permissions else {}
    
    def set_permissions(self, permissions_dict):
        """Set permissions from dictionary"""
        self.permissions = json.dumps(permissions_dict)

# User model is imported from betting.py to avoid conflicts
# The User model already has multi-tenant support with sportsbook_operator_id field

# Bet model is imported from betting.py to avoid conflicts
# The Bet model already has multi-tenant support with sportsbook_operator_id field

# Transaction model is imported from betting.py to avoid conflicts
# The Transaction model already has multi-tenant support with sportsbook_operator_id field

class BetSlip(db.Model):
    """Updated BetSlip model with multi-tenant support"""
    __tablename__ = 'bet_slips'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Multi-tenant support
    sportsbook_operator_id = db.Column(db.Integer, db.ForeignKey('sportsbook_operators.id'), nullable=True)
    
    total_stake = db.Column(db.Float, nullable=False)
    total_odds = db.Column(db.Float, nullable=False)
    potential_return = db.Column(db.Float, nullable=False)
    bet_type = db.Column(db.String(8))  # single, multiple
    status = db.Column(db.String(10))  # pending, won, lost, void
    actual_return = db.Column(db.Float)
    settled_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sportsbook_operator_id': self.sportsbook_operator_id,
            'total_stake': self.total_stake,
            'total_odds': self.total_odds,
            'potential_return': self.potential_return,
            'bet_type': self.bet_type,
            'status': self.status,
            'actual_return': self.actual_return,
            'settled_at': self.settled_at.isoformat() if self.settled_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Association table for bet slips and bets (many-to-many)
bet_slip_bets = db.Table('bet_slip_bets',
    db.Column('bet_slip_id', db.Integer, db.ForeignKey('bet_slips.id'), primary_key=True),
    db.Column('bet_id', db.Integer, db.ForeignKey('bets.id'), primary_key=True)
)

class SportsbookTheme(db.Model):
    """Theme customization for sportsbook operators"""
    __tablename__ = 'sportsbook_themes'
    
    id = db.Column(db.Integer, primary_key=True)
    sportsbook_operator_id = db.Column(db.Integer, db.ForeignKey('sportsbook_operators.id'), nullable=False)
    theme_name = db.Column(db.String(100), default='default')
    primary_color = db.Column(db.String(7), default='#1e40af')
    secondary_color = db.Column(db.String(7), default='#3b82f6')
    accent_color = db.Column(db.String(7), default='#f59e0b')
    background_color = db.Column(db.String(7), default='#ffffff')
    text_color = db.Column(db.String(7), default='#1f2937')
    font_family = db.Column(db.String(100), default='Inter, sans-serif')
    logo_url = db.Column(db.String(500))
    banner_image_url = db.Column(db.String(500))
    custom_css = db.Column(db.Text)
    layout_style = db.Column(db.String(50), default='modern')
    button_style = db.Column(db.String(50), default='rounded')
    card_style = db.Column(db.String(50), default='shadow')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - handled by backref in SportsbookOperator model

class ThemeTemplate(db.Model):
    """Pre-built theme templates for sportsbook operators"""
    __tablename__ = 'theme_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    template_name = db.Column(db.String(100), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    preview_image_url = db.Column(db.String(500))
    primary_color = db.Column(db.String(7), nullable=False)
    secondary_color = db.Column(db.String(7), nullable=False)
    accent_color = db.Column(db.String(7), nullable=False)
    background_color = db.Column(db.String(7), nullable=False)
    text_color = db.Column(db.String(7), nullable=False)
    font_family = db.Column(db.String(100), nullable=False)
    layout_style = db.Column(db.String(50), nullable=False)
    button_style = db.Column(db.String(50), nullable=False)
    card_style = db.Column(db.String(50), nullable=False)
    custom_css = db.Column(db.Text)
    is_premium = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'template_name': self.template_name,
            'display_name': self.display_name,
            'description': self.description,
            'preview_image_url': self.preview_image_url,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'accent_color': self.accent_color,
            'background_color': self.background_color,
            'text_color': self.text_color,
            'font_family': self.font_family,
            'layout_style': self.layout_style,
            'button_style': self.button_style,
            'card_style': self.card_style,
            'custom_css': self.custom_css,
            'is_premium': self.is_premium,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

