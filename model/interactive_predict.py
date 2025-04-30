# interactive_predict.py

import re
import joblib
import pandas as pd
import numpy as np

# --- Load model artifacts once ---
art = joblib.load('skincare_counterfeit_artifacts.pkl')
ohe              = art['ohe']
tf_name          = art['tf_name']
tf_ing           = art['tf_ing']
scaler           = art['scaler']
clf              = art['clf']
median_price_map = art['median_price_map']

def clean_price(price_str: str) -> float:
    """Strip non-numeric characters and convert to float."""
    cleaned = re.sub(r'[^\d\.]', '', price_str)
    return float(cleaned) if cleaned else 0.0

def clean_ingredients(ings_str: str) -> str:
    """Normalize comma-separated list: strip whitespace."""
    tokens = [tok.strip() for tok in ings_str.split(',') if tok.strip()]
    return ','.join(tokens)

def clean_text(txt: str) -> str:
    """Generic text cleanup."""
    return txt.strip()

def predict_counterfeit(product_name: str,
                        ingredients:   str,
                        price:         float,
                        category:      str) -> dict:
    """Return counterfeit prediction and probability."""
    price_ratio    = price / median_price_map.get(category, price)
    num_ings       = len(ingredients.split(','))
    
    # One-hot encode category
    cat_df  = pd.DataFrame([{ohe.feature_names_in_[0]: category}])
    cat_feat = ohe.transform(cat_df)
    
    # TF-IDF features
    name_feat = tf_name.transform([product_name]).toarray()
    ing_feat  = tf_ing.transform([ingredients]).toarray()
    
    # Assemble, scale, predict
    X_num  = np.array([[num_ings, price_ratio]])
    X      = np.hstack([X_num, cat_feat, name_feat, ing_feat])
    Xs     = scaler.transform(X)
    prob   = clf.predict_proba(Xs)[0,1]
    pred   = bool(clf.predict(Xs)[0])
    return {"is_counterfeit": pred, "probability": prob}

def main():
    print("=== Counterfeit Prediction ===")
    pn = clean_text(input("Enter Product Name: "))
    ings = clean_ingredients(input("Enter Ingredients (comma-separated): "))
    price = clean_price(input("Enter Price (e.g. 29.99): "))
    cat = clean_text(input("Enter Category: "))
    
    result = predict_counterfeit(pn, ings, price, cat)
    status = "COUNTERFEIT" if result["is_counterfeit"] else "LEGITIMATE"
    print(f"\nPrediction: {status}")
    print(f"Confidence: {result['probability']:.2%}")

if __name__ == "__main__":
    main()
