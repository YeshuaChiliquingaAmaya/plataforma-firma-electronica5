# Configuración de tema profesional para la aplicación de firma de PDFs
import json
import os

# Esquema de colores para tema claro - MEJORADO PARA MEJOR CONTRASTE
LIGHT_THEME = {
    "primary": "#1F2937",      # Gris oscuro profesional (mejor contraste)
    "secondary": "#6B7280",    # Gris medio
    "success": "#059669",      # Verde éxito
    "warning": "#D97706",      # Naranja advertencia  
    "error": "#DC2626",        # Rojo error
    "background": "#F9FAFB",   # Fondo muy claro
    "surface": "#FFFFFF",      # Superficie blanca
    "border": "#D1D5DB",       # Borde más visible
    "text_primary": "#111827", # Texto negro casi puro
    "text_secondary": "#6B7280", # Texto gris legible
    "canvas_bg": "#F3F4F6",    # Fondo del canvas gris muy claro
    "hover": "#F3F4F6",        # Color hover sutil
    "accent": "#3B82F6",       # Azul para acentos
    "header": "#FFFFFF"        # Header blanco para máximo contraste
}

# Esquema de colores para tema oscuro - MEJORADO PARA MEJOR CONTRASTE
DARK_THEME = {
    "primary": "#374151",      # Gris oscuro con mejor contraste
    "secondary": "#9CA3AF",    # Gris medio claro
    "success": "#10B981",      # Verde más brillante
    "warning": "#F59E0B",      # Naranja más brillante
    "error": "#EF4444",        # Rojo más brillante
    "background": "#111827",   # Fondo negro profundo
    "surface": "#1F2937",      # Superficie gris oscuro
    "border": "#374151",       # Borde gris oscuro
    "text_primary": "#F9FAFB", # Texto blanco casi puro
    "text_secondary": "#D1D5DB", # Texto gris claro legible
    "canvas_bg": "#374151",    # Fondo del canvas gris oscuro
    "hover": "#4B5563",        # Color hover
    "accent": "#60A5FA",       # Azul claro para acentos
    "header": "#1F2937"        # Header gris oscuro
}

# Configuración por defecto
COLORS = LIGHT_THEME.copy()

# Configuración de fuentes
FONTS = {
    "title": {"size": 24, "weight": "bold"},
    "subtitle": {"size": 18, "weight": "bold"},
    "section": {"size": 16, "weight": "bold"},
    "label": {"size": 14, "weight": "bold"},
    "body": {"size": 13},
    "small": {"size": 12},
    "button": {"size": 16, "weight": "bold"}
}

# Configuración de espaciado
SPACING = {
    "small": 5,
    "medium": 10,
    "large": 15,
    "xlarge": 20
}

# Configuración de bordes
BORDERS = {
    "radius": 8,
    "width": 1
}

# Configuración de botones
BUTTONS = {
    "height": 35,
    "large_height": 45,
    "width": 120
}

# Iconos para diferentes acciones
ICONS = {
    "certificate": "📋",
    "password": "🔒",
    "pdf": "📄",
    "folder": "📁",
    "save": "💾",
    "sign": "🔐",
    "preview": "👁️",
    "settings": "⚙️",
    "position": "📍",
    "dimensions": "📏",
    "page": "📖",
    "batch": "📁",
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "progress": "📊",
    "loading": "⏳",
    "location": "🌍",
    "reason": "💼",
    "validate": "🔍",
    "export": "📤",
    "refresh": "🔄",
    "user": "👤",
    "organization": "🏢",
    "calendar": "📅",
    "technical": "🔧",
    "key": "🔑",
    "theme_light": "☀️",
    "theme_dark": "🌙",
    "settings_gear": "⚙️"
}

# Configuración de usuario
USER_CONFIG_FILE = "user_config.json"

def load_user_config():
    """Cargar configuración del usuario desde archivo"""
    if os.path.exists(USER_CONFIG_FILE):
        try:
            with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_user_config(config):
    """Guardar configuración del usuario a archivo"""
    try:
        with open(USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

def set_theme(theme_name):
    """Cambiar el tema actual"""
    global COLORS
    if theme_name == "dark":
        COLORS.clear()
        COLORS.update(DARK_THEME)
    else:
        COLORS.clear()
        COLORS.update(LIGHT_THEME)
    
    # Guardar preferencia
    config = load_user_config()
    config['theme'] = theme_name
    save_user_config(config)

def get_current_theme():
    """Obtener el tema actual"""
    config = load_user_config()
    return config.get('theme', 'light')

# Cargar tema guardado al inicializar
saved_theme = get_current_theme()
set_theme(saved_theme) 