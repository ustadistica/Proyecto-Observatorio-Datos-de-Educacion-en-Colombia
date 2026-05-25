# 🐳 Capacitación Docker - Sprint 0
## Guía completa de Docker para el Observatorio de Datos de Educación

---

## 📋 Tabla de Contenidos

1. [Introducción a Docker](#introducción-a-docker)
2. [Conceptos Fundamentales](#conceptos-fundamentales)
3. [Nuestro Dockerfile](#nuestro-dockerfile)
4. [Comandos Esenciales](#comandos-esenciales)
5. [Construcción y Ejecución](#construcción-y-ejecución)
6. [Troubleshooting](#troubleshooting)
7. [Mejores Prácticas](#mejores-prácticas)
8. [Ejercicios Prácticos](#ejercicios-prácticos)

---

## 🎯 Introducción a Docker

### ¿Qué es Docker?

Docker es una plataforma de **contenerización** que nos permite empaquetar una aplicación con todas sus dependencias (librerías, configuraciones, etc.) en un **contenedor** estandarizado. Esto garantiza que la aplicación funcione de manera idéntica en cualquier entorno: desarrollo, pruebas o producción.

### ¿Por qué usamos Docker en este proyecto?

Nuestro Observatorio de Datos de Educación maneja:
- **3,384,532 registros** de Saber Pro (2012-2024)
- **676,587 registros** de SNIES (2015-2024)
- **36,888 registros** de PTE (2015-2024)
- Múltiples librerías Python (pandas, streamlit, dvc, etc.)

Docker nos permite:
✅ **Reproducibilidad**: Cualquier persona puede ejecutar el proyecto exactamente igual
✅ **Portabilidad**: Funciona en Windows, Mac, Linux sin cambios
✅ **Aislamiento**: No interfiere con otras instalaciones de Python
✅ **Despliegue**: Fácil de llevar a producción o servidores en la nube

---

## 🧱 Conceptos Fundamentales

### 1. **Imagen** vs **Contenedor**

| Concepto | Definición | Analogía |
|----------|------------|----------|
| **Imagen** | Plantilla de solo lectura con la aplicación y dependencias | Receta de cocina |
| **Contenedor** | Instancia ejecutable de una imagen | Plato cocinado con esa receta |

### 2. **Dockerfile**

Es el archivo de configuración que define cómo construir una imagen. Nuestro proyecto usa:

```dockerfile
FROM python:3.12-slim          # Imagen base (Python 3.12 ligero)
WORKDIR /app                   # Directorio de trabajo dentro del contenedor
RUN apt-get update && ...      # Instalar dependencias del sistema
RUN pip install poetry         # Instalar Poetry (gestor de dependencias)
COPY pyproject.toml ./         # Copiar configuración del proyecto
RUN poetry install ...         # Instalar dependencias Python
COPY . .                       # Copiar todo el código
EXPOSE 8501                    # Puerto para Streamlit
CMD ["streamlit", "run", ...]  # Comando de inicio
```

### 3. **Volúmenes**

Los contenedores son efímeros (se borran al detenerse). Los volúmenes permiten:
- **Persistencia**: Guardar datos entre ejecuciones
- **Compartir**: Acceder a archivos del host desde el contenedor

---

## 📄 Nuestro Dockerfile

Analicemos línea por línea nuestro `Dockerfile`:

```dockerfile
# Línea 1: Imagen base oficial de Python 3.12 (versión ligera)
FROM python:3.12-slim

# Línea 3: Establece /app como directorio de trabajo
WORKDIR /app

# Líneas 5-7: Actualiza sistema e instala herramientas de compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Línea 9: Instala Poetry (gestor de dependencias moderno)
RUN pip install --no-cache-dir poetry

# Líneas 11-14: Copia archivos de configuración e instala dependencias
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --without dev

# Líneas 16-17: Instala DVC (Data Version Control) para gestión de datos
RUN pip install --no-cache-dir dvc[s3,azure,gdrive,ossfs]

# Líneas 19-21: Copia el código fuente y datos
COPY src/ ./src/
COPY app/ ./app/
COPY datos/ ./datos/

# Línea 23: Expone puerto 8501 (Streamlit por defecto)
EXPOSE 8501

# Línea 25: Comando para iniciar la aplicación Streamlit
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## ⌨️ Comandos Esenciales

### Verificación de instalación
```bash
docker --version          # Verificar Docker instalado
docker info               # Información del sistema Docker
docker images             # Listar imágenes descargadas
docker ps                 # Listar contenedores en ejecución
docker ps -a              # Listar todos los contenedores (incl. detenidos)
```

### Construcción de imagen
```bash
# Construir imagen desde Dockerfile
docker build -t observatorio-educacion:latest .

# Construir sin caché (útil para debugging)
docker build --no-cache -t observatorio-educacion:latest .
```

### Ejecución de contenedor
```bash
# Ejecutar contenedor (modo detach - segundo plano)
docker run -d -p 8501:8501 --name observatorio observatorio-educacion:latest

# Ejecutar en modo interactivo (ver logs en tiempo real)
docker run -it -p 8501:8501 --name observatorio observatorio-educacion:latest

# Ejecutar con volumen (montar directorio local)
docker run -d -p 8501:8501 -v $(pwd)/datos:/app/datos --name observatorio observatorio-educacion:latest
```

### Gestión de contenedores
```bash
docker stop observatorio        # Detener contenedor
docker start observatorio       # Iniciar contenedor detenido
docker restart observatorio     # Reiniciar contenedor
docker rm observatorio          # Eliminar contenedor
docker logs observatorio        # Ver logs del contenedor
docker exec -it observatorio bash  # Entrar al contenedor (shell interactivo)
```

### Limpieza
```bash
docker system prune -a          # Eliminar todo lo no usado (imágenes, contenedores, volúmenes)
docker rmi observatorio-educacion  # Eliminar imagen específica
```

---

## 🚀 Construcción y Ejecución

### Paso a paso para nuestro proyecto

#### 1. **Preparación**
```bash
# Navegar al directorio del proyecto
cd "c:\Users\jhona\Desktop\corte 3 consultoria\Proyecto-Observatorio-Datos-de-Educacion-en-Colombia"

# Verificar que exista Dockerfile
dir Dockerfile
```

#### 2. **Construcción de la imagen**
```bash
# Construir imagen (tarda ~5-10 minutos la primera vez)
docker build -t observatorio-educacion:latest .

# Verificar imagen creada
docker images | findstr observatorio
```

**Salida esperada:**
```
observatorio-educacion    latest    abc123def456    2 minutes ago    1.2GB
```

#### 3. **Ejecución del contenedor**
```bash
# Ejecutar contenedor
docker run -d -p 8501:8501 --name observatorio-app observatorio-educacion:latest

# Verificar que está corriendo
docker ps | findstr observatorio
```

**Salida esperada:**
```
CONTAINER ID   IMAGE                      STATUS          PORTS
abc123def456   observatorio-educacion     Up 10 seconds   0.0.0.0:8501->8501/tcp
```

#### 4. **Acceso a la aplicación**
Abrir navegador en: `http://localhost:8501`

#### 5. **Detener y limpiar**
```bash
# Detener contenedor
docker stop observatorio-app

# Eliminar contenedor
docker rm observatorio-app

# (Opcional) Eliminar imagen
docker rmi observatorio-educacion:latest
```

---

## 🔧 Troubleshooting

### Problema 1: "Cannot connect to the Docker daemon"
**Solución:**
```bash
# Windows: Reiniciar Docker Desktop
# Linux: sudo systemctl start docker
# Verificar que Docker esté corriendo
docker info
```

### Problema 2: "Port 8501 already in use"
**Solución:**
```bash
# Matar proceso usando puerto 8501
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# O cambiar puerto en docker run
docker run -d -p 8502:8501 --name observatorio observatorio-educacion:latest
```

### Problema 3: "No space left on device"
**Solución:**
```bash
# Limpiar Docker
docker system prune -a --volumes

# Verificar espacio
docker system df
```

### Problema 4: "Permission denied" al montar volúmenes
**Solución (Windows):**
- Compartir drive en Docker Desktop Settings → Resources → File Sharing

**Solución (Linux/Mac):**
```bash
# Asegurar permisos correctos
sudo chmod -R 755 ./datos
```

### Problema 5: La aplicación no carga o da error
**Solución:**
```bash
# Ver logs del contenedor
docker logs observatorio-app

# Entrar al contenedor para debugging
docker exec -it observatorio-app bash

# Dentro del contenedor:
ls -la                    # Verificar archivos
pip list                  # Verificar dependencias
python -c "import pandas" # Verificar importaciones
```

---

## 🏆 Mejores Prácticas

### 1. **Optimización del Dockerfile**
```dockerfile
# ❌ MAL: Muchas capas innecesarias
RUN apt-get update
RUN apt-get install -y package1
RUN apt-get install -y package2
RUN rm -rf /var/lib/apt/lists/*

# ✅ BIEN: Una sola capa
RUN apt-get update && apt-get install -y \
    package1 \
    package2 \
    && rm -rf /var/lib/apt/lists/*
```

### 2. **Uso de .dockerignore**
Crear archivo `.dockerignore` para excluir archivos innecesarios:
```
__pycache__/
*.pyc
.env
.git/
venv/
datos/raw/*.parquet  # Datos crudos grandes
```

### 3. **Versionamiento de imágenes**
```bash
# Etiquetar con versión específica
docker build -t observatorio-educacion:1.0.0 .
docker build -t observatorio-educacion:latest .

# Push a registry (Docker Hub, ECR, etc.)
docker tag observatorio-educacion:1.0.0 usuario/observatorio:1.0.0
docker push usuario/observatorio:1.0.0
```

### 4. **Seguridad**
```dockerfile
# ❌ MAL: Correr como root
USER root

# ✅ BIEN: Crear usuario no privilegiado
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
```

### 5. **Healthcheck**
```dockerfile
# Verificar que la aplicación esté saludable
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1
```

---

## 📝 Ejercicios Prácticos

### Ejercicio 1: Construcción básica
```bash
# 1. Construir imagen
docker build -t mi-observatorio:ejercicio1 .

# 2. Ejecutar contenedor
docker run -d -p 8501:8501 --name ejercicio1 mi-observatorio:ejercicio1

# 3. Verificar que funciona
docker ps
# Abrir http://localhost:8501

# 4. Limpieza
docker stop ejercicio1
docker rm ejercicio1
```

### Ejercicio 2: Volúmenes y persistencia
```bash
# 1. Crear directorio de datos
mkdir datos-test
echo "datos de prueba" > datos-test/test.txt

# 2. Ejecutar con volumen
docker run -d -p 8501:8501 \
  -v $(pwd)/datos-test:/app/datos-test \
  --name ejercicio2 \
  observatorio-educacion:latest

# 3. Verificar desde dentro del contenedor
docker exec ejercicio2 cat /app/datos-test/test.txt

# 4. Limpieza
docker stop ejercicio2
docker rm ejercicio2
rm -rf datos-test
```

### Ejercicio 3: Multi-stage build (avanzado)
```dockerfile
# Etapa 1: Build
FROM python:3.12 as builder
COPY . .
RUN pip install --user -r requirements.txt

# Etapa 2: Runtime (más ligero)
FROM python:3.12-slim
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app
ENV PATH=/root/.local/bin:$PATH
CMD ["streamlit", "run", "app/streamlit_app.py"]
```

### Ejercicio 4: Docker Compose (orquestación)
```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./datos:/app/datos
    environment:
      - STREAMLIT_SERVER_PORT=8501
  db:
    image: postgres:13
    environment:
      POSTGRES_PASSWORD: password
```

```bash
# Ejecutar todo el stack
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener todo
docker-compose down
```

---

## 📚 Recursos Adicionales

### Documentación Oficial
- [Docker Documentation](https://docs.docker.com/)
- [Dockerfile Reference](https://docs.docker.com/engine/reference/builder/)
- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

### Para nuestro proyecto específico
- **Streamlit en Docker**: [Streamlit Docker Guide](https://docs.streamlit.io/knowledge-base/tutorials/deploy/docker)
- **Python en Docker**: [Python Docker Images](https://hub.docker.com/_/python)
- **DVC con Docker**: [DVC Docker Setup](https://dvc.org/doc/start/data-management)

### Comandos útiles de referencia rápida
```bash
# Ver uso de recursos
docker stats

# Inspeccionar contenedor
docker inspect observatorio-app

# Copiar archivos desde/a contenedor
docker cp observatorio-app:/app/datos/processed ./backup
docker cp ./nuevo_script.py observatorio-app:/app/src/

# Ejecutar comando en contenedor existente
docker exec observatorio-app python src/ingesta/procesar_saber_pro.py

# Ver historial de cambios en imagen
docker history observatorio-educacion:latest
```

---

## 🎓 Evaluación de Conocimientos

### Preguntas de repaso:

1. **¿Cuál es la diferencia entre imagen y contenedor?**
   - Imagen: plantilla de solo lectura
   - Contenedor: instancia ejecutable de una imagen

2. **¿Qué hace el comando `docker build`?**
   - Construye una imagen desde un Dockerfile

3. **¿Para qué sirve `-p 8501:8501` en `docker run`?**
   - Mapea puerto 8501 del contenedor al puerto 8501 del host

4. **¿Cómo eliminamos todos los contenedores detenidos?**
   - `docker container prune`

5. **¿Qué es un volumen en Docker?**
   - Mecanismo para persistir datos fuera del contenedor

---

## ✅ Checklist de Competencias

Al finalizar esta capacitación, debes poder:

- [ ] Explicar qué es Docker y por qué lo usamos
- [ ] Diferenciar entre imagen y contenedor
- [ ] Leer y entender nuestro Dockerfile
- [ ] Construir una imagen desde cero
- [ ] Ejecutar un contenedor con nuestra aplicación
- [ ] Manejar volúmenes para persistencia de datos
- [ ] Solucionar problemas comunes de Docker
- [ ] Aplicar mejores prácticas de contenerización
- [ ] Limpieza adecuada de recursos Docker

---

**🎉 ¡Felicidades! Has completado la capacitación de Docker para el Observatorio de Datos de Educación.**

*Próximo paso: Practicar con ejercicios y aplicar estos conocimientos en el desarrollo del proyecto.*

---

*Documento creado para el Sprint 0 - Capacitación del equipo*  
*Proyecto Observatorio de Datos de Educación en Colombia*  
*Última actualización: Mayo 2026*