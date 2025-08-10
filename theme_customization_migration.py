#!/usr/bin/env python3
"""
Database migration to add theme customization support
"""

import sqlite3
import os
import sys

def create_theme_customization_tables():
    """Create tables for theme customizations"""
    
    # Path to the database
    db_path = "src/database/app.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create sportsbook_themes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sportsbook_themes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sportsbook_operator_id INTEGER NOT NULL,
                theme_name VARCHAR(100) DEFAULT 'default',
                primary_color VARCHAR(7) DEFAULT '#1e40af',
                secondary_color VARCHAR(7) DEFAULT '#3b82f6',
                accent_color VARCHAR(7) DEFAULT '#f59e0b',
                background_color VARCHAR(7) DEFAULT '#ffffff',
                text_color VARCHAR(7) DEFAULT '#1f2937',
                font_family VARCHAR(100) DEFAULT 'Inter, sans-serif',
                logo_url VARCHAR(500),
                banner_image_url VARCHAR(500),
                custom_css TEXT,
                layout_style VARCHAR(50) DEFAULT 'modern',
                button_style VARCHAR(50) DEFAULT 'rounded',
                card_style VARCHAR(50) DEFAULT 'shadow',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sportsbook_operator_id) REFERENCES sportsbook_operators (id)
            )
        ''')
        
        # Create theme_templates table for pre-built themes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS theme_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name VARCHAR(100) NOT NULL,
                display_name VARCHAR(100) NOT NULL,
                description TEXT,
                preview_image_url VARCHAR(500),
                primary_color VARCHAR(7) NOT NULL,
                secondary_color VARCHAR(7) NOT NULL,
                accent_color VARCHAR(7) NOT NULL,
                background_color VARCHAR(7) NOT NULL,
                text_color VARCHAR(7) NOT NULL,
                font_family VARCHAR(100) NOT NULL,
                layout_style VARCHAR(50) NOT NULL,
                button_style VARCHAR(50) NOT NULL,
                card_style VARCHAR(50) NOT NULL,
                custom_css TEXT,
                is_premium BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default theme templates
        default_themes = [
            {
                'template_name': 'classic_blue',
                'display_name': 'Classic Blue',
                'description': 'Professional blue theme with clean design',
                'primary_color': '#1e40af',
                'secondary_color': '#3b82f6',
                'accent_color': '#f59e0b',
                'background_color': '#ffffff',
                'text_color': '#1f2937',
                'font_family': 'Inter, sans-serif',
                'layout_style': 'modern',
                'button_style': 'rounded',
                'card_style': 'shadow'
            },
            {
                'template_name': 'sports_green',
                'display_name': 'Sports Green',
                'description': 'Dynamic green theme for sports betting',
                'primary_color': '#059669',
                'secondary_color': '#10b981',
                'accent_color': '#f59e0b',
                'background_color': '#ffffff',
                'text_color': '#1f2937',
                'font_family': 'Roboto, sans-serif',
                'layout_style': 'modern',
                'button_style': 'rounded',
                'card_style': 'shadow'
            },
            {
                'template_name': 'premium_dark',
                'display_name': 'Premium Dark',
                'description': 'Elegant dark theme for premium experience',
                'primary_color': '#7c3aed',
                'secondary_color': '#8b5cf6',
                'accent_color': '#f59e0b',
                'background_color': '#1f2937',
                'text_color': '#f9fafb',
                'font_family': 'Poppins, sans-serif',
                'layout_style': 'modern',
                'button_style': 'rounded',
                'card_style': 'glow'
            },
            {
                'template_name': 'orange_energy',
                'display_name': 'Orange Energy',
                'description': 'Vibrant orange theme with high energy',
                'primary_color': '#ea580c',
                'secondary_color': '#fb923c',
                'accent_color': '#1d4ed8',
                'background_color': '#ffffff',
                'text_color': '#1f2937',
                'font_family': 'Montserrat, sans-serif',
                'layout_style': 'modern',
                'button_style': 'sharp',
                'card_style': 'border'
            },
            {
                'template_name': 'minimal_white',
                'display_name': 'Minimal White',
                'description': 'Clean minimal design with focus on content',
                'primary_color': '#374151',
                'secondary_color': '#6b7280',
                'accent_color': '#3b82f6',
                'background_color': '#ffffff',
                'text_color': '#111827',
                'font_family': 'Source Sans Pro, sans-serif',
                'layout_style': 'minimal',
                'button_style': 'minimal',
                'card_style': 'minimal'
            }
        ]
        
        for theme in default_themes:
            cursor.execute('''
                INSERT OR IGNORE INTO theme_templates 
                (template_name, display_name, description, primary_color, secondary_color, 
                 accent_color, background_color, text_color, font_family, layout_style, 
                 button_style, card_style)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                theme['template_name'], theme['display_name'], theme['description'],
                theme['primary_color'], theme['secondary_color'], theme['accent_color'],
                theme['background_color'], theme['text_color'], theme['font_family'],
                theme['layout_style'], theme['button_style'], theme['card_style']
            ))
        
        # Create default theme customizations for existing operators
        cursor.execute('''
            INSERT OR IGNORE INTO sportsbook_themes (sportsbook_operator_id)
            SELECT id FROM sportsbook_operators 
            WHERE id NOT IN (SELECT sportsbook_operator_id FROM sportsbook_themes)
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ Theme customization tables created successfully")
        print("✅ Default theme templates added")
        print("✅ Default themes assigned to existing operators")
        return True
        
    except Exception as e:
        print(f"❌ Error creating theme tables: {e}")
        return False

if __name__ == "__main__":
    print("🎨 Creating theme customization database tables...")
    success = create_theme_customization_tables()
    if success:
        print("🎉 Theme customization system ready!")
    else:
        print("💥 Failed to set up theme customization system")
        sys.exit(1)

