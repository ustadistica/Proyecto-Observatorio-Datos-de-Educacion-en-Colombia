"""
Script para generar capturas de pantalla del dashboard de Streamlit
y exportarlas para incluirlas en el informe EDA.

Este script:
1. Ejecuta el dashboard de Streamlit en modo headless
2. Navega por las diferentes secciones
3. Genera capturas de pantalla de cada visualización
4. Guarda las imágenes en una carpeta para el informe

Autor: Equipo de Análisis
Fecha: Abril 2026
"""

import os
import time
from pathlib import Path
import pandas as pd
import plotly.io as pio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import streamlit as st

# Configuración
RUTA_PROYECTO = Path(__file__).parent.parent.parent
RUTA_DASHBOARD = RUTA_PROYECTO / "Códigos" / "procesamiento_saber_pro" / "app_streamlit.py"
RUTA_SALIDA_IMAGENES = RUTA_PROYECTO / "Códigos" / "procesamiento_saber_pro" / "imagenes_informe"

# Crear directorio de salida
RUTA_SALIDA_IMAGENES.mkdir(parents=True, exist_ok=True)

def configurar_driver():
    """Configura el WebDriver de Chrome para modo headless"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def capturar_seccion(driver, url, nombre_archivo, espera=5):
    """Captura una sección específica del dashboard"""
    driver.get(url)
    time.sleep(espera)  # Esperar a que cargue
    
    # Hacer scroll para cargar todo el contenido
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    
    # Capturar screenshot
    ruta_guardado = RUTA_SALIDA_IMAGENES / f"{nombre_archivo}.png"
    driver.save_screenshot(str(ruta_guardado))
    print(f"✅ Captura guardada: {ruta_guardado}")

def main():
    """Función principal"""
    print("="*60)
    print("GENERANDO CAPTURAS DEL DASHBOARD STREAMLIT")
    print("="*60)
    
    # Iniciar Streamlit en segundo plano
    print("🚀 Iniciando Streamlit...")
    os.system(f"start streamlit run {RUTA_DASHBOARD} --server.headless true --server.port 8501")
    time.sleep(5)  # Esperar a que inicie
    
    # Configurar driver
    print("🔧 Configurando WebDriver...")
    driver = configurar_driver()
    
    # URL base del dashboard
    base_url = "http://localhost:8501"
    
    try:
        # 1. Capturar página principal (Inicio)
        print("📸 Capturando: Inicio...")
        capturar_seccion(driver, base_url, "01_inicio", espera=8)
        
        # 2. Capturar Métricas de Procesamiento
        print("📸 Capturando: Métricas de Procesamiento...")
        # Hacer clic en el menú lateral para ir a Métricas
        driver.get(f"{base_url}?section=metricas")
        capturar_seccion(driver, driver.current_url, "02_metricas_procesamiento", espera=5)
        
        # 3. Capturar Análisis por Año
        print("📸 Capturando: Análisis por Año...")
        driver.get(f"{base_url}?section=analisis_anio")
        capturar_seccion(driver, driver.current_url, "03_analisis_por_anio", espera=5)
        
        # 4. Capturar Análisis Descriptivo
        print("📸 Capturando: Análisis Descriptivo...")
        driver.get(f"{base_url}?section=analisis_descriptivo")
        capturar_seccion(driver, driver.current_url, "04_analisis_descriptivo", espera=8)
        
        # 5. Capturar Ciudades Internacionales
        print("📸 Capturando: Ciudades Internacionales...")
        driver.get(f"{base_url}?section=ciudades_internacionales")
        capturar_seccion(driver, driver.current_url, "05_ciudades_internacionales", espera=8)
        
        # 6. Capturar Detalle de Limpieza
        print("📸 Capturando: Detalle de Limpieza...")
        driver.get(f"{base_url}?section=detalle_limpieza")
        capturar_seccion(driver, driver.current_url, "06_detalle_limpieza", espera=5)
        
        # 7. Capturar Muestra de Datos
        print("📸 Capturando: Muestra de Datos...")
        driver.get(f"{base_url}?section=muestra_datos")
        capturar_seccion(driver, driver.current_url, "07_muestra_datos", espera=5)
        
        print("\n" + "="*60)
        print("✅ ¡CAPTURAS GENERADAS EXITOSAMENTE!")
        print("="*60)
        print(f"\n📁 Imágenes guardadas en: {RUTA_SALIDA_IMAGENES}")
        print("\n📋 Lista de archivos:")
        for img in sorted(RUTA_SALIDA_IMAGENES.glob("*.png")):
            print(f"   - {img.name}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()
        # Cerrar Streamlit
        os.system("taskkill /F /IM streamlit.exe")

if __name__ == "__main__":
    # Verificar dependencias
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError:
        print("❌ Error: Se requiere selenium para capturar pantallas")
        print("Instalar con: pip install selenium")
        exit(1)
    
    main()