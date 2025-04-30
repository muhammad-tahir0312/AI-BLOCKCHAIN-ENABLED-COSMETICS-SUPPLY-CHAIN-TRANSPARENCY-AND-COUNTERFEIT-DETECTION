from typing import Tuple, Dict
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

    def load_model(self):
        """Load ML model and validate artifacts."""
        try:
            logger.debug(f"Loading model from: {self.model_path}")
            artifacts = joblib.load(self.model_path)
            
            # Extract components
            self.ohe = artifacts['ohe']
            self.tf_name = artifacts['tf_name']
            self.tf_ing = artifacts['tf_ing']
            self.scaler = artifacts['scaler']
            self.clf = artifacts['clf']
            self.median_price_map = artifacts['median_price_map']
            self.artifacts = artifacts
            
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load ML model: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to load ML model: {str(e)}"
            )

    def _ml_predict(self, product_data: dict) -> Dict:
        """Make prediction using ML model."""
        try:
            # Extract input fields
            product_name = product_data['product_name']
            ingredients = product_data['ingredients']
            price = float(product_data['price'])
            category = product_data['category']

            # Compute numeric features
            price_ratio = price / self.median_price_map.get(category, price)
            num_ingredients = len(ingredients.split(','))

            # Encode category
            cat_df = pd.DataFrame([{self.ohe.feature_names_in_[0]: category}])
            cat_feat = self.ohe.transform(cat_df)

            # TF-IDF features
            name_feat = self.tf_name.transform([product_name]).toarray()
            ing_feat = self.tf_ing.transform([ingredients]).toarray()

            # Assemble feature vector
            X_num = np.array([[num_ingredients, price_ratio]])
            X = np.hstack([X_num, cat_feat, name_feat, ing_feat])
            X_scaled = self.scaler.transform(X)

            # Model prediction
            probability = self.clf.predict_proba(X_scaled)[0, 1]

            return {
                'is_counterfeit': probability >= 0.5,
                'confidence': float(probability),
                'price_ratio': price_ratio,
                'ingredient_count': num_ingredients
            }

        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            raise

    def get_counterfeit_confidence(self, product_data: dict) -> Tuple[bool, float, str]:
        """Detect if a product might be counterfeit using ML model."""
        try:
            result = self._ml_predict(product_data)
            return self._format_result(result)
        except Exception as e:
            logger.error(f"Fraud detection failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"ML prediction failed: {str(e)}"
            )

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