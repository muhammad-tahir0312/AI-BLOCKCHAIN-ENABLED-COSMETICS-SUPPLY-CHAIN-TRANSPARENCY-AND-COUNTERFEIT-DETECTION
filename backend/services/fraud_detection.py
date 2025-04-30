# services/fraud_detection.py

import os
import joblib
import numpy as np
import pandas as pd
from loguru import logger
from fastapi import HTTPException, status

class FraudDetectionService:
    def __init__(self):
        """Initialize the fraud detection service with model artifacts."""
        # Construct an absolute path to ml_models/skincare_counterfeit_artifacts.pkl
        base = os.path.dirname(__file__)
        models_dir = os.path.abspath(os.path.join(base, '..', 'ml_models'))
        self.model_path = os.path.join(models_dir, 'skincare_counterfeit_artifacts.pkl')

        if not os.path.isfile(self.model_path):
            logger.error(f"Model file not found at {self.model_path}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"ML artifact not found: {self.model_path}"
            )

        # These will be set in load_model()
        self.ohe = None
        self.tf_name = None
        self.tf_ing = None
        self.scaler = None
        self.clf = None
        self.median_price_map = None

        self.load_model()

    def load_model(self):
        """Load ML model and validate artifacts."""
        try:
            logger.debug(f"Loading ML artifacts from: {self.model_path}")
            artifacts = joblib.load(self.model_path)
            logger.debug(f"Artifacts keys: {list(artifacts.keys())}")

            # Required artifact keys
            required = ['ohe','tf_name','tf_ing','scaler','clf','median_price_map']
            missing = [k for k in required if k not in artifacts]
            if missing:
                raise KeyError(f"Missing keys in artifact: {missing}")

            # Assign
            self.ohe              = artifacts['ohe']
            self.tf_name          = artifacts['tf_name']
            self.tf_ing           = artifacts['tf_ing']
            self.scaler           = artifacts['scaler']
            self.clf              = artifacts['clf']
            self.median_price_map = artifacts['median_price_map']

            logger.info("ML artifacts loaded successfully.")

        except KeyError as e:
            logger.error(f"Artifact validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Invalid artifact contents: {e}"
            )
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to load ML model: {e}"
            )

    def _ml_predict(self, product_data: dict) -> dict:
        """Make prediction using ML model."""
        try:
            # 1) Extract and clean inputs
            name = product_data['product_name'].strip()
            ings = product_data['ingredients'].strip()
            price = float(product_data['price'])
            cat   = product_data['category'].strip()

            # 2) Numeric features
            price_ratio     = price / self.median_price_map.get(cat, price)
            num_ings        = len(ings.split(','))

            # 3) Category encoding
            cat_df   = pd.DataFrame([{ self.ohe.feature_names_in_[0]: cat }])
            cat_feat = self.ohe.transform(cat_df)

            # 4) TF-IDF features
            name_feat = self.tf_name.transform([name]).toarray()
            ing_feat  = self.tf_ing.transform([ings]).toarray()

            # 5) Assemble & scale
            X_num   = np.array([[num_ings, price_ratio]])
            X       = np.hstack([X_num, cat_feat, name_feat, ing_feat])
            X_scaled= self.scaler.transform(X)

            # 6) Predict
            prob = self.clf.predict_proba(X_scaled)[0,1]
            is_cf = bool(self.clf.predict(X_scaled)[0])

            return {
                'is_counterfeit': is_cf,
                'confidence':    prob,
                'price_ratio':   price_ratio,
                'ingredient_count': num_ings
            }

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            # Wrap and propagate as HTTPException to the API layer
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"ML prediction error: {e}"
            )

    def get_counterfeit_confidence(self, product_data: dict) -> Tuple[bool, float, str]:
        """Detect if a product might be counterfeit using ML model."""
        result = self._ml_predict(product_data)

        # Build a human-readable reason
        p = result['confidence']
        if p < 0.3:
            reason = "Characteristics consistent with legitimate items"
        elif p < 0.5:
            reason = "Some suspicious signals but likely genuine"
        elif p < 0.7:
            reason = "Multiple suspicious indicators detected"
        else:
            reason = "High confidence counterfeit based on multiple factors"

        return result['is_counterfeit'], p, reason
