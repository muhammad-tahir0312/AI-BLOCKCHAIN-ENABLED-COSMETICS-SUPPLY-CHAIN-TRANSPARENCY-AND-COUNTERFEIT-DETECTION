from typing import Tuple, Optional, Dict
import joblib
import os
import numpy as np
import pandas as pd
from loguru import logger
from fastapi import HTTPException, status

class FraudDetectionService:
    def __init__(self):
        """Initialize the fraud detection service with model artifacts."""
        models_dir = os.path.join(os.path.dirname(__file__), '../ml_models')
        os.makedirs(models_dir, exist_ok=True)
        self.model_path = os.path.join(models_dir, 'skincare_counterfeit_artifacts.pkl')
        self.artifacts = None
        self.load_model()

    def _validate_artifacts(self):
        """Ensure all required model components are present."""
        required = ['ohe', 'tf_name', 'tf_ing', 'scaler', 'clf', 'median_price_map']
        if not self.artifacts:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ML model not loaded"
            )
        if not all(k in self.artifacts and self.artifacts[k] is not None for k in required):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ML model components missing"
            )
        return True

    def load_model(self):
        """Load ML model and validate artifacts."""
        try:
            logger.debug(f"Attempting to load model from: {self.model_path}")
            self.artifacts = joblib.load(self.model_path)
            logger.debug(f"Loaded artifacts keys: {self.artifacts.keys()}")
            self._validate_artifacts()
            logger.info("Loaded and validated existing model successfully")
        except Exception as e:
            logger.error(f"Failed to load ML model: {str(e)}")
            logger.error(f"Model path: {self.model_path}")
            logger.error(f"Current working directory: {os.getcwd()}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to load ML model: {str(e)}"
            )
    def get_counterfeit_confidence(self, product_data: dict) -> Tuple[bool, float, str]:
        """Detect if a product might be counterfeit using ML model."""
        try:
            self._validate_artifacts()
            result = self._ml_predict(product_data)
            return self._format_result(result)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Fraud detection failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"ML prediction failed: {str(e)}"
            )

    def _ml_predict(self, product_data: dict) -> Dict:
        """Make prediction using ML model."""
        result = {
            'is_counterfeit': False,
            'confidence': 0.0,
            'price_ratio': 1.0,
            'ingredient_count': 0
        }

        # Transform features
        cat_features = self.artifacts['ohe'].transform(
            pd.DataFrame([{
                self.artifacts['ohe'].feature_names_in_[0]: product_data['category']
            }])
        )
        name_features = self.artifacts['tf_name'].transform(
            [product_data['product_name']]
        ).toarray()
        ing_features = self.artifacts['tf_ing'].transform(
            [product_data['ingredients']]
        ).toarray()
        
        # Calculate numerical features
        price_ratio = float(product_data['price']) / self.artifacts['median_price_map'].get(
            product_data['category'], 
            float(product_data['price'])
        )
        ingredient_count = len(product_data['ingredients'].split(','))
        
        # Combine and scale features
        x_num = np.array([[ingredient_count, price_ratio]])
        X = np.hstack([x_num, cat_features, name_features, ing_features])
        X_scaled = self.artifacts['scaler'].transform(X)
        
        # Get prediction
        probability = self.artifacts['clf'].predict_proba(X_scaled)[0, 1]
        
        result.update({
            'is_counterfeit': probability >= 0.5,
            'confidence': probability,
            'price_ratio': price_ratio,
            'ingredient_count': ingredient_count
        })
            
        return result

    def _format_result(self, result: Dict) -> Tuple[bool, float, str]:
        """Format ML prediction result to match API expectations."""
        confidence = result['confidence']
        
        if confidence < 0.3:
            reason = "Product characteristics consistent with legitimate items"
        elif confidence < 0.5:
            reason = "Some suspicious characteristics but likely legitimate"
        elif confidence < 0.7:
            reason = "Multiple suspicious indicators detected"
        else:
            reason = "High confidence counterfeit based on multiple factors"
            
        return result['is_counterfeit'], confidence, reason