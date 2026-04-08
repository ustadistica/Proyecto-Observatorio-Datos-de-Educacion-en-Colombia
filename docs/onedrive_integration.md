# Integración con OneDrive para Observatorio de Datos de Educación

## Descripción

Este documento describe cómo integrar OneDrive como almacenamiento remoto para los datos raw del Observatorio de Datos de Educación en Colombia.

## Configuración de OneDrive como Remote Storage en DVC

### 1. Instalación de dependencias

```bash
pip install dvc[ossfs]
```

### 2. Configuración del remote storage

```bash
# Inicializar DVC si no está inicializado
dvc init

# Configurar OneDrive como remote storage
dvc remote add -d onedrive onedrive://root/observatorio-datos-educacion

# Configurar credenciales (se pueden guardar en variables de entorno)
dvc remote modify onedrive client_id $ONEDRIVE_CLIENT_ID
dvc remote modify onedrive client_secret $ONEDRIVE_CLIENT_SECRET
dvc remote modify onedrive tenant_id $ONEDRIVE_TENANT_ID
```

### 3. Variables de entorno necesarias

Crear un archivo `.env` con las siguientes variables:

```bash
ONEDRIVE_CLIENT_ID="tu_client_id"
ONEDRIVE_CLIENT_SECRET="tu_client_secret"
ONEDRIVE_TENANT_ID="tu_tenant_id"
```

## Estructura de carpetas en OneDrive

```
OneDrive/
├── observatorio-datos-educacion/
│   ├── raw/
│   │   ├── icfes/
│   │   │   ├── saber_11/
│   │   │   └── saber_pro/
│   │   ├── pte/
│   │   └── snies/
│   └── processed/
```

## Comandos DVC para OneDrive

### Subir datos al OneDrive

```bash
# Agregar datos al DVC
dvc add datos/raw/

# Subir al OneDrive
dvc push -r onedrive
```

### Descargar datos del OneDrive

```bash
# Descargar datos del OneDrive
dvc pull -r onedrive
```

### Verificar estado de los datos

```bash
# Verificar qué datos están disponibles localmente
dvc status

# Verificar qué datos están disponibles en el remote
dvc status -r onedrive
```

## Pipeline DVC con OneDrive

### Ejecutar pipeline completa

```bash
# Ejecutar todos los stages de la pipeline
dvc repro

# Ejecutar pipeline con OneDrive como remote
dvc repro -r onedrive
```

### Ejecutar stages específicos

```bash
# Ejecutar solo la descarga de ICFES Saber 11
dvc repro descargar_icfes_saber11

# Ejecutar solo la transformación de datos
dvc repro transformar_datos
```

## Automatización con GitHub Actions

### Workflow para sincronización con OneDrive

```yaml
name: Sync with OneDrive
on:
  push:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # Ejecutar diariamente a las 2 AM

jobs:
  sync-onedrive:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configurar Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Instalar dependencias
        run: |
          pip install dvc[ossfs]
          pip install -r requirements.txt
      
      - name: Configurar DVC
        run: |
          dvc remote add -d onedrive onedrive://root/observatorio-datos-educacion
          dvc remote modify onedrive client_id ${{ secrets.ONEDRIVE_CLIENT_ID }}
          dvc remote modify onedrive client_secret ${{ secrets.ONEDRIVE_CLIENT_SECRET }}
          dvc remote modify onedrive tenant_id ${{ secrets.ONEDRIVE_TENANT_ID }}
      
      - name: Sincronizar con OneDrive
        run: dvc push -r onedrive
```

## Consideraciones de seguridad

1. **No subir credenciales al repositorio**: Las credenciales de OneDrive deben guardarse en variables de entorno o en el gestor de secretos del CI/CD.

2. **Permisos mínimos**: Configurar las credenciales de OneDrive con los permisos mínimos necesarios para el funcionamiento del observatorio.

3. **Rotación de credenciales**: Establecer un calendario para rotar las credenciales de acceso.

## Resolución de problemas

### Error de autenticación

```bash
# Verificar credenciales
dvc remote list
dvc remote modify onedrive --show

# Regenerar credenciales si es necesario
dvc remote remove onedrive
dvc remote add -d onedrive onedrive://root/observatorio-datos-educacion
```

### Espacio insuficiente en OneDrive

```bash
# Verificar uso de espacio
dvc gc --dry-run -r onedrive

# Limpiar datos antiguos
dvc gc -r onedrive
```

### Conexión lenta

```bash
# Configurar número de hilos para transferencia
dvc remote modify onedrive jobs 10

# Configurar tiempo de espera
dvc remote modify onedrive timeout 300
```

## Documentación adicional

- [Documentación oficial de DVC](https://dvc.org/doc)
- [Documentación de OneDrive API](https://docs.microsoft.com/en-us/onedrive/developer/)
- [Guía de configuración de remotes en DVC](https://dvc.org/doc/command-reference/remote)