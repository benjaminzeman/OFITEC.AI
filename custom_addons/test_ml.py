#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento de los modelos de Machine Learning
"""
import sys
import os
sys.path.append('/usr/lib/python3/dist-packages')

def test_ml_libraries():
    """Prueba las librerías de ML instaladas"""
    print("🔍 Probando librerías de Machine Learning...")

    try:
        import numpy as np
        print("✅ NumPy:", np.__version__)
    except ImportError as e:
        print("❌ NumPy no disponible:", e)
        return False

    try:
        import pandas as pd
        print("✅ Pandas:", pd.__version__)
    except ImportError as e:
        print("❌ Pandas no disponible:", e)
        return False

    try:
        import sklearn
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        print("✅ Scikit-learn:", sklearn.__version__)
    except ImportError as e:
        print("❌ Scikit-learn no disponible:", e)
        return False

    try:
        import xgboost as xgb
        print("✅ XGBoost:", xgb.__version__)
    except ImportError as e:
        print("❌ XGBoost no disponible:", e)
        return False

    try:
        import lightgbm as lgb
        print("✅ LightGBM:", lgb.__version__)
    except ImportError as e:
        print("❌ LightGBM no disponible:", e)
        return False

    try:
        import tensorflow as tf
        print("✅ TensorFlow:", tf.__version__)
    except ImportError as e:
        print("❌ TensorFlow no disponible:", e)
        return False

    # Prueba de funcionamiento básico
    print("\n🔬 Probando funcionamiento básico...")

    # Crear datos de prueba
    np.random.seed(42)
    X = np.random.rand(100, 4)
    y = np.random.randint(0, 2, 100)

    # Probar Random Forest
    try:
        rf = RandomForestClassifier(n_estimators=10, random_state=42)
        rf.fit(X, y)
        pred = rf.predict(X[:5])
        print("✅ Random Forest: Modelo entrenado y predicho correctamente")
    except Exception as e:
        print("❌ Error en Random Forest:", e)
        return False

    # Probar XGBoost
    try:
        dtrain = xgb.DMatrix(X, label=y)
        params = {'objective': 'binary:logistic', 'max_depth': 3}
        bst = xgb.train(params, dtrain, num_boost_round=10)
        pred = bst.predict(dtrain)[:5]
        print("✅ XGBoost: Modelo entrenado y predicho correctamente")
    except Exception as e:
        print("❌ Error en XGBoost:", e)
        return False

    # Probar LightGBM
    try:
        train_data = lgb.Dataset(X, label=y)
        params = {'objective': 'binary', 'metric': 'binary_logloss'}
        bst = lgb.train(params, train_data, num_boost_round=10)
        pred = bst.predict(X[:5])
        print("✅ LightGBM: Modelo entrenado y predicho correctamente")
    except Exception as e:
        print("❌ Error en LightGBM:", e)
        return False

    print("\n🎉 ¡Todas las librerías de ML funcionan correctamente!")
    return True

if __name__ == "__main__":
    success = test_ml_libraries()
    sys.exit(0 if success else 1)
