import os
import joblib
import numpy as np
import pandas as pd
from loguru import logger
from fastapi import HTTPException, status
from typing import Tuple, Dict


class FraudDetectionService:
    """
    Service class for loading a counterfeit detection model and
    performing fraud detection on cosmetics products.
    """

    def __init__(self):
        # Determine model artifact path
        base_dir = os.path.dirname(__file__)
        models_dir = os.path.abspath(os.path.join(base_dir, '..', 'ml_models'))
        self.model_path = os.path.join(models_dir, 'skincare_counterfeit_artifacts.pkl')

        if not os.path.isfile(self.model_path):
            logger.error(f"ML artifact not found at {self.model_path}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"ML artifact not found: {self.model_path}"
            )

        # Initialize placeholders
        self.ohe = None
        self.tf_name = None
        self.tf_ing = None
        self.scaler = None
        self.clf = None
        self.median_price_map = None

        self.load_model()

    def load_model(self):
        """Load the pickled ML artifacts and validate presence of all components."""
        try:
            logger.debug(f"Loading ML artifacts from {self.model_path}")
            artifacts = joblib.load(self.model_path)

            required_keys = ['ohe', 'tf_name', 'tf_ing', 'scaler', 'clf', 'median_price_map']
            for key in required_keys:
                if key not in artifacts:
                    raise KeyError(f"Missing expected key '{key}' in model artifacts")

            # Assign artifacts safely
            self.ohe = artifacts.get('ohe')
            self.tf_name = artifacts.get('tf_name')
            self.tf_ing = artifacts.get('tf_ing')
            self.scaler = artifacts.get('scaler')
            self.clf = artifacts.get('clf')
            self.median_price_map = artifacts.get('median_price_map')

            # Validate that none of the critical components are None
            if self.ohe is None:
                raise ValueError("OneHotEncoder ('ohe') was None after loading")
            if self.tf_name is None:
                raise ValueError("TF-IDF vectorizer for names ('tf_name') was None after loading")
            if self.tf_ing is None:
                raise ValueError("TF-IDF vectorizer for ingredients ('tf_ing') was None after loading")
            if self.scaler is None:
                raise ValueError("Scaler ('scaler') was None after loading")
            if self.clf is None:
                raise ValueError("Classifier ('clf') was None after loading")
            if self.median_price_map is None:
                raise ValueError("Median price map was None after loading")

            logger.info("ML artifacts loaded successfully.")

        except Exception as e:
            logger.error(f"Failed to load ML model: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to load ML model: {str(e)}"
            )

    def _ml_predict(self, product_data: Dict) -> Dict:
        """
        Run the ML model on a single product's data.
        Returns a dict with raw prediction details.
        """
        try:
            # Extract and clean inputs
            name = product_data.get('product_name', '').strip()
            ings = product_data.get('ingredients', '').strip()
            price = float(product_data.get('price', 0))
            cat = product_data.get('category', '').strip()

            if not name or not ings or not cat:
                raise ValueError("Missing required fields in product data")

            # Numeric features
            price_ratio = price / self.median_price_map.get(cat, price)
            num_ings = len(ings.split(','))

            # Category encoding
            feature_name = self.ohe.feature_names_in_[0]
            cat_df = pd.DataFrame([{feature_name: cat}])
            cat_feat = self.ohe.transform(cat_df)

            # Handle TF-IDF transforms safely
            def safe_transform(vectorizer, text):
                result = vectorizer.transform([text])
                if hasattr(result, 'toarray'):
                    return result.toarray()
                return result  # Already a numpy array

            name_feat = safe_transform(self.tf_name, name)
            ing_feat = safe_transform(self.tf_ing, ings)

            # Combine and scale
            x_num = np.array([[num_ings, price_ratio]])
            X = np.hstack([x_num, cat_feat, name_feat, ing_feat])
            X_scaled = self.scaler.transform(X)

            # Predict
            prob = self.clf.predict_proba(X_scaled)[0, 1]
            is_cf = bool(self.clf.predict(X_scaled)[0])

            return {
                'is_counterfeit': is_cf,
                'confidence': prob,
                'price_ratio': price_ratio,
                'ingredient_count': num_ings
            }

        except Exception as e:
            logger.error(f"Prediction error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"ML prediction failed: {str(e)}"
            )

    def get_counterfeit_confidence(self, product_data: Dict) -> Tuple[bool, float, str]:
        """
        Public method to get a boolean flag, confidence score, and human-readable reason.
        """
        result = self._ml_predict(product_data)
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