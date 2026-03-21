import pandas as pd

ruta_limpio = r'C:\Users\jhona\Desktop\UNIVERSIDAD SANTO TOMAS\CONSULTORIA PROYECTO\BASES DE DATOS\BASES_LIMPIEZA_GENERAL.csv'

def generar_reporte():
    print("--- GENERANDO REPORTE DE CALIDAD ---")
    # Leemos con el separador '|' que usamos en el paso anterior
    df = pd.read_csv(ruta_limpio, sep='|', encoding='latin1', low_memory=False)
    
    # 1. Resumen por año
    print("\n📊 Registros por año de proceso:")
    print(df['anio_proceso'].value_counts().sort_index())
    
    # 2. Verificación de Nulos
    print("\n🔍 Conteo de valores nulos por columna:")
    print(df.isnull().sum())
    
    # 3. Top 5 Instituciones con más registros
    if 'inst_nombre_institucion' in df.columns:
        print("\n🏆 Top 5 Instituciones con mayor volumen de datos:")
        print(df['inst_nombre_institucion'].value_counts().head(5))

if __name__ == "__main__":
    generar_reporte()