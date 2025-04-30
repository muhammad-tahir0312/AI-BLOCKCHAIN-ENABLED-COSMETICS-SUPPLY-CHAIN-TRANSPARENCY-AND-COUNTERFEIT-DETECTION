import pandas as pd
import joblib
import numpy as np

# Load serialized artifacts
art = joblib.load('skincare_counterfeit_artifacts.pkl')
ohe = art['ohe']
tf_name = art['tf_name']
tf_ing = art['tf_ing']
scaler = art['scaler']
clf = art['clf']
median_price_map = art['median_price_map']

def predict_counterfeit(product_name: str,
                        ingredients: str,
                        price: float,
                        category: str) -> dict:
    """Return a dict with 'is_counterfeit' and 'probability'."""
    # Numeric features
    price_ratio = price / median_price_map.get(category, price)
    num_ingredients = len(ingredients.split(','))

    # One-hot encode category
    cat_df = pd.DataFrame([{ohe.feature_names_in_[0]: category}])
    cat_feat = ohe.transform(cat_df)

    # TF-IDF features
    name_feat = tf_name.transform([product_name]).toarray()
    ing_feat = tf_ing.transform([ingredients]).toarray()

    # Assemble and scale
    X_num = np.array([[num_ingredients, price_ratio]])
    X = np.hstack([X_num, cat_feat, name_feat, ing_feat])
    X_scaled = scaler.transform(X)

    # Predict
    prob = clf.predict_proba(X_scaled)[0, 1]
    pred = bool(clf.predict(X_scaled)[0])
    return {"is_counterfeit": pred, "probability": prob}

if __name__ == "__main__":
    # Load the 30-entry test dataset
    df_test = pd.read_csv('../dataset/skincare_test_dataset.csv')

    # Apply inference
    results = df_test.apply(
        lambda row: pd.Series(predict_counterfeit(
            row['product_name'],
            row['ingredients'],
            row['price'],
            row['category']
        )),
        axis=1
    )

    # Combine and save
    df_out = pd.concat([df_test, results], axis=1)
    df_out.to_csv('skincare_test_results.csv', index=False)

    # Display summary
    print(df_out[['product_name', 'is_counterfeit', 'probability']])
