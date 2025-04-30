import sys
import joblib
import pandas as pd
import numpy as np

# Load serialized artifacts
artifacts = joblib.load('skincare_counterfeit_artifacts.pkl')
ohe = artifacts['ohe']
tf_name = artifacts['tf_name']
tf_ing = artifacts['tf_ing']
scaler = artifacts['scaler']
clf = artifacts['clf']
median_price_map = artifacts['median_price_map']

def predict_counterfeit(product_name: str,
                        ingredients: str,
                        price: float,
                        category: str) -> dict:
    """
    Predict whether a product is counterfeit.

    Returns:
        dict: {
            "is_counterfeit": bool,
            "probability": float
        }
    """
    # Compute numeric features
    price_ratio = price / median_price_map.get(category, price)
    num_ingredients = len(ingredients.split(','))

    # Encode category
    cat_df = pd.DataFrame([{ohe.feature_names_in_[0]: category}])
    cat_feat = ohe.transform(cat_df)

    # TF-IDF features
    name_feat = tf_name.transform([product_name]).toarray()
    ing_feat = tf_ing.transform([ingredients]).toarray()

    # Assemble feature vector
    X_num = np.array([[num_ingredients, price_ratio]])
    X = np.hstack([X_num, cat_feat, name_feat, ing_feat])
    X_scaled = scaler.transform(X)

    # Model prediction
    prob = clf.predict_proba(X_scaled)[0, 1]
    pred = bool(clf.predict(X_scaled)[0])

    return {"is_counterfeit": pred, "probability": float(prob)}

if __name__ == "__main__":
    # Example usage from command line:
    # python infer_counterfeit.py "Product Name" "ing1,ing2,..." 19.99 "moisturizer"
    if len(sys.argv) != 5:
        print("Usage: python infer_counterfeit.py <product_name> <ingredients> <price> <category>")
        sys.exit(1)

    pn, ings, pr, cat = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
    result = predict_counterfeit(pn, ings, pr, cat)
    print(f"Result: {result['is_counterfeit']}, probability = {result['probability']:.4f}")
