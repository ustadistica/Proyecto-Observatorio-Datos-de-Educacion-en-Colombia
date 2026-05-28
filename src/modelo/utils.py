"""
Módulo de utilidades para persistencia de modelos de Machine Learning
Sprint 7 - Issue 7.4: Serialización y Persistencia de Modelos
"""

import joblib
import json
import pickle
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Rutas base
PROJECT_ROOT = Path(__file__).parent.parent.parent
MODELS_DIR = PROJECT_ROOT / 'models'
ARTIFACTS_DIR = PROJECT_ROOT / 'artifacts'
METRICS_DIR = ARTIFACTS_DIR / 'metricas'

# Asegurar que los directorios existan
MODELS_DIR.mkdir(parents=True, exist_ok=True)
METRICS_DIR.mkdir(parents=True, exist_ok=True)


def save_model(model: Any, filename: str, metadata: Optional[Dict] = None) -> Path:
    """
    Guarda un modelo de machine learning en formato joblib.
    
    Args:
        model: Objeto del modelo a guardar
        filename: Nombre del archivo (sin extensión)
        metadata: Diccionario opcional con metadatos del modelo
        
    Returns:
        Ruta del archivo guardado
    """
    filepath = MODELS_DIR / f"{filename}.joblib"
    
    # Si hay metadata, guardar también como JSON
    if metadata:
        metadata_path = MODELS_DIR / f"{filename}_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"Metadata guardada: {metadata_path}")
    
    # Guardar modelo
    joblib.dump(model, filepath)
    logger.info(f"Modelo guardado: {filepath}")
    
    return filepath


def load_model(filename: str) -> Any:
    """
    Carga un modelo de machine learning desde archivo joblib.
    
    Args:
        filename: Nombre del archivo (sin extensión)
        
    Returns:
        Objeto del modelo cargado
    """
    filepath = MODELS_DIR / f"{filename}.joblib"
    
    if not filepath.exists():
        raise FileNotFoundError(f"Modelo no encontrado: {filepath}")
    
    model = joblib.load(filepath)
    logger.info(f"Modelo cargado: {filepath}")
    
    return model


def save_metrics(metrics_dict: Dict, filename: str) -> Path:
    """
    Guarda métricas del modelo en formato JSON.
    
    Args:
        metrics_dict: Diccionario con las métricas
        filename: Nombre del archivo (sin extensión)
        
    Returns:
        Ruta del archivo guardado
    """
    filepath = METRICS_DIR / f"{filename}.json"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(metrics_dict, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Métricas guardadas: {filepath}")
    return filepath


def load_metrics(filename: str) -> Dict:
    """
    Carga métricas del modelo desde archivo JSON.
    
    Args:
        filename: Nombre del archivo (sin extensión)
        
    Returns:
        Diccionario con las métricas
    """
    filepath = METRICS_DIR / f"{filename}.json"
    
    if not filepath.exists():
        raise FileNotFoundError(f"Métricas no encontradas: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        metrics = json.load(f)
    
    logger.info(f"Métricas cargadas: {filepath}")
    return metrics


def get_model_info(filename: str) -> Dict:
    """
    Obtiene información de un modelo guardado.
    
    Args:
        filename: Nombre del archivo (sin extensión)
        
    Returns:
        Diccionario con información del modelo
    """
    model_path = MODELS_DIR / f"{filename}.joblib"
    metadata_path = MODELS_DIR / f"{filename}_metadata.json"
    
    info = {
        'model_path': str(model_path),
        'exists': model_path.exists(),
        'metadata': None
    }
    
    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            info['metadata'] = json.load(f)
    
    return info


def list_models() -> list:
    """
    Lista todos los modelos guardados en el directorio models/.
    
    Returns:
        Lista de nombres de archivos de modelos
    """
    if not MODELS_DIR.exists():
        return []
    
    models = [f.stem for f in MODELS_DIR.glob('*.joblib')]
    return models


def create_experiment_metadata(
    experiment_name: str,
    model_type: str,
    description: str,
    author: str,
    issue: str,
    hyperparameters: Dict,
    metrics: Dict,
    data_info: Optional[Dict] = None,
    notes: Optional[str] = None
) -> Dict:
    """
    Crea un diccionario de metadatos estandarizado para un experimento.
    
    Args:
        experiment_name: Nombre del experimento
        model_type: Tipo de modelo (PCA, KMeans, DBSCAN, etc.)
        description: Descripción del experimento
        author: Autor del experimento
        issue: Issue asociado (ej: "Sprint 7.1")
        hyperparameters: Diccionario con hiperparámetros
        metrics: Diccionario con métricas del modelo
        data_info: Información adicional sobre los datos
        notes: Notas adicionales
        
    Returns:
        Diccionario de metadatos
    """
    metadata = {
        "metadata": {
            "experiment_name": experiment_name,
            "model_type": model_type,
            "description": description,
            "author": author,
            "issue": issue,
            "fecha_creacion": datetime.now().isoformat(),
            "notas": notes
        },
        "datos": data_info or {},
        "hiperparametros": hyperparameters,
        "metricas": metrics
    }
    
    return metadata


def save_experiment(
    model: Any,
    filename: str,
    metadata: Dict,
    visualizations: Optional[Dict[str, Path]] = None
) -> Dict[str, Path]:
    """
    Guarda un experimento completo (modelo, metadatos y visualizaciones).
    
    Args:
        model: Objeto del modelo
        filename: Nombre base del archivo
        metadata: Metadatos del experimento
        visualizations: Diccionario con rutas de visualizaciones
        
    Returns:
        Diccionario con rutas de archivos guardados
    """
    saved_files = {}
    
    # Guardar modelo
    model_path = save_model(model, filename, metadata)
    saved_files['model'] = model_path
    
    # Guardar métricas separadamente para fácil acceso
    if 'metricas' in metadata:
        metrics_path = save_metrics(metadata['metricas'], filename)
        saved_files['metrics'] = metrics_path
    
    # Guardar visualizaciones (si se proporcionan)
    if visualizations:
        viz_dir = ARTIFACTS_DIR / 'visualizaciones'
        viz_dir.mkdir(parents=True, exist_ok=True)
        
        for viz_name, viz_path in visualizations.items():
            if viz_path.exists():
                dest_path = viz_dir / viz_path.name
                # Copiar archivo (simple lectura/escritura)
                with open(viz_path, 'rb') as src:
                    with open(dest_path, 'wb') as dst:
                        dst.write(src.read())
                saved_files[f'viz_{viz_name}'] = dest_path
    
    logger.info(f"Experimento '{filename}' guardado exitosamente")
    return saved_files


# Funciones específicas para cada Issue del Sprint 7

def save_pca_model(pca, scaler, feature_names: list, metadata: Dict) -> Dict[str, Path]:
    """Guarda modelo PCA completo con scaler y metadata."""
    return save_experiment(
        model={'pca': pca, 'scaler': scaler, 'feature_names': feature_names},
        filename='pca_saber_pro',
        metadata=metadata
    )


def save_kmeans_model(kmeans, scaler, feature_names: list, metadata: Dict) -> Dict[str, Path]:
    """Guarda modelo K-Means completo con scaler y metadata."""
    return save_experiment(
        model={'kmeans': kmeans, 'scaler': scaler, 'feature_names': feature_names},
        filename='kmeans_departamentos',
        metadata=metadata
    )


def save_dbscan_model(dbscan, scaler, feature_names: list, metadata: Dict) -> Dict[str, Path]:
    """Guarda modelo DBSCAN completo con scaler y metadata."""
    return save_experiment(
        model={'dbscan': dbscan, 'scaler': scaler, 'feature_names': feature_names},
        filename='dbscan_saturacion',
        metadata=metadata
    )