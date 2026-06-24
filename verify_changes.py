#!/usr/bin/env python3
"""
Script de verificación - Confirma que todos los cambios se hayan implementado correctamente
"""

import os
import sqlite3
import sys

def check_file_exists(path, name):
    """Verifica si un archivo existe"""
    if os.path.exists(path):
        print(f"✅ {name}")
        return True
    else:
        print(f"❌ {name} - NO ENCONTRADO")
        return False

def check_app_content():
    """Verifica que app.py contiene los cambios necesarios"""
    checks = []
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Credenciales actualizadas
    if "ADMIN_USER = os.environ.get('ADMIN_USER', 'adm')" in content:
        print("✅ Credencial de usuario (adm) - Correcta")
        checks.append(True)
    else:
        print("❌ Credencial de usuario - NO ACTUALIZADA")
        checks.append(False)
    
    if "ADMIN_PASS = os.environ.get('ADMIN_PASSWORD', 'admin123456789')" in content:
        print("✅ Credencial de contraseña (admin123456789) - Correcta")
        checks.append(True)
    else:
        print("❌ Credencial de contraseña - NO ACTUALIZADA")
        checks.append(False)
    
    # Tablas en la base de datos
    if "CREATE TABLE IF NOT EXISTS users" in content:
        print("✅ Tabla 'users' - Definida")
        checks.append(True)
    else:
        print("❌ Tabla 'users' - NO ENCONTRADA")
        checks.append(False)
    
    if "CREATE TABLE IF NOT EXISTS action_history" in content:
        print("✅ Tabla 'action_history' - Definida")
        checks.append(True)
    else:
        print("❌ Tabla 'action_history' - NO ENCONTRADA")
        checks.append(False)
    
    # Nuevas rutas
    if "@app.route('/user/register'" in content:
        print("✅ Ruta /user/register - Definida")
        checks.append(True)
    else:
        print("❌ Ruta /user/register - NO ENCONTRADA")
        checks.append(False)
    
    if "@app.route('/ticket/<int:ticket_number>/print')" in content:
        print("✅ Ruta /ticket/print - Definida")
        checks.append(True)
    else:
        print("❌ Ruta /ticket/print - NO ENCONTRADA")
        checks.append(False)
    
    if "@app.route('/admin/history')" in content:
        print("✅ Ruta /admin/history - Definida")
        checks.append(True)
    else:
        print("❌ Ruta /admin/history - NO ENCONTRADA")
        checks.append(False)
    
    # Funciones de historial
    if "def log_action(" in content:
        print("✅ Función log_action() - Definida")
        checks.append(True)
    else:
        print("❌ Función log_action() - NO ENCONTRADA")
        checks.append(False)
    
    if "def get_action_history(" in content:
        print("✅ Función get_action_history() - Definida")
        checks.append(True)
    else:
        print("❌ Función get_action_history() - NO ENCONTRADA")
        checks.append(False)
    
    return all(checks)

def check_templates():
    """Verifica que todos los templates nuevos existen"""
    templates = [
        ('templates/register_user.html', 'Template de registro'),
        ('templates/print_ticket.html', 'Template de impresión'),
        ('templates/admin_history.html', 'Template de historial'),
    ]
    
    results = []
    for path, name in templates:
        results.append(check_file_exists(path, name))
    
    return all(results)

def check_env_example():
    """Verifica que .env.example tiene las credenciales correctas"""
    with open('.env.example', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = []
    
    if "ADMIN_USER=adm" in content:
        print("✅ .env.example - Usuario correcto")
        checks.append(True)
    else:
        print("❌ .env.example - Usuario no actualizado")
        checks.append(False)
    
    if "ADMIN_PASSWORD=admin123456789" in content:
        print("✅ .env.example - Contraseña correcta")
        checks.append(True)
    else:
        print("❌ .env.example - Contraseña no actualizada")
        checks.append(False)
    
    return all(checks)

def check_docs():
    """Verifica que existen los archivos de documentación"""
    docs = [
        ('CHANGES.md', 'Documento de cambios'),
        ('QUICK_START.md', 'Guía rápida'),
    ]
    
    results = []
    for path, name in docs:
        results.append(check_file_exists(path, name))
    
    return all(results)

def main():
    """Ejecuta todas las verificaciones"""
    print("\n" + "="*60)
    print("🔍 VERIFICACIÓN DE CAMBIOS - RIFA APP v2.0")
    print("="*60 + "\n")
    
    print("📄 Verificando backend (app.py)...")
    print("-" * 60)
    backend_ok = check_app_content()
    
    print("\n🎨 Verificando templates...")
    print("-" * 60)
    templates_ok = check_templates()
    
    print("\n⚙️  Verificando configuración (.env.example)...")
    print("-" * 60)
    env_ok = check_env_example()
    
    print("\n📚 Verificando documentación...")
    print("-" * 60)
    docs_ok = check_docs()
    
    print("\n" + "="*60)
    
    if backend_ok and templates_ok and env_ok and docs_ok:
        print("✅ ¡TODAS LAS VERIFICACIONES PASARON!")
        print("\nLa aplicación está lista para usar con:")
        print("  • Usuario: adm")
        print("  • Contraseña: admin123456789")
        print("  • URL: http://localhost:5000/admin/login")
        print("\nNuevas características:")
        print("  1. Registro de usuarios (/user/register)")
        print("  2. Impresión de boletos (/ticket/<id>/print)")
        print("  3. Historial de acciones (/admin/history)")
        print("\nArchivos agregados:")
        print("  • CHANGES.md - Detalles de cambios")
        print("  • QUICK_START.md - Guía rápida de uso")
        print("  • templates/register_user.html")
        print("  • templates/print_ticket.html")
        print("  • templates/admin_history.html")
        print("="*60 + "\n")
        return 0
    else:
        print("❌ ALGUNAS VERIFICACIONES FALLARON")
        print("Por favor revisa los errores arriba.")
        print("="*60 + "\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
