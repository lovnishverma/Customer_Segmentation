"""
Customer Segmentation Flask App
================================
Unsupervised ML Deployment using K-Means Clustering
"""

from flask import Flask, render_template, request, jsonify
import numpy as np
import joblib
import os

app = Flask(__name__)

# Load Model & Scaler 
MODEL_PATH  = os.path.join('model', 'kmeans_model.pkl')
SCALER_PATH = os.path.join('model', 'scaler.pkl')

CLUSTER_INFO = {}

try:
    kmeans = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    print("✅ Model and scaler loaded successfully!")

    # ---------------------------------------------------------
    # DYNAMIC CLUSTER MAPPING (Global Optimal Match)
    # ---------------------------------------------------------
    # 1. Get the actual cluster centers in their original scale
    centroids = scaler.inverse_transform(kmeans.cluster_centers_)
    
    # 2. Define our "Ideal" target locations (Income, Spending)
    ideal_profiles = {
        "Average": np.array([60, 50]),
        "VIP": np.array([90, 80]),
        "Impulsive": np.array([30, 80]),
        "Conservative": np.array([90, 20]),
        "Budget": np.array([30, 20])
    }
    
    # 3. Base UI templates
    templates = {
        "Average": {
            "name": "Average Customers", "emoji": "🟡", "color": "#FFC300", 
            "badge": "warning", "income_level": "Medium", "spending_level": "Medium", 
            "description": "Typical customers with moderate income and average spending habits.", 
            "strategy": "Offer loyalty programs and mid-range promotions to keep them engaged.", 
            "examples": "Regular shoppers, working professionals"
        },
        "VIP": {
            "name": "VIP / Loyal Customers", "emoji": "🟢", "color": "#28B463", 
            "badge": "success", "income_level": "High", "spending_level": "High", 
            "description": "High earners who also spend generously — your most valuable segment!", 
            "strategy": "Provide premium experiences, early access to new products, and personalized offers.", 
            "examples": "Executives, entrepreneurs, luxury shoppers"
        },
        "Impulsive": {
            "name": "Impulsive Buyers", "emoji": "🔵", "color": "#2E86C1", 
            "badge": "primary", "income_level": "Low", "spending_level": "High", 
            "description": "Despite modest income, these customers spend heavily — likely driven by trends.", 
            "strategy": "Leverage flash sales, social media trends, and FOMO-based campaigns.", 
            "examples": "Young adults, fashion-driven shoppers"
        },
        "Conservative": {
            "name": "Careful / Conservative", "emoji": "🔴", "color": "#E74C3C", 
            "badge": "danger", "income_level": "High", "spending_level": "Low", 
            "description": "High income but very selective spending — they buy only what they truly need.", 
            "strategy": "Emphasize quality, value, and ROI. Detailed product reviews work well here.", 
            "examples": "Senior professionals, savers, minimalists"
        },
        "Budget": {
            "name": "Budget Shoppers", "emoji": "🟣", "color": "#8E44AD", 
            "badge": "secondary", "income_level": "Low", "spending_level": "Low", 
            "description": "Price-conscious customers who spend carefully due to limited income.", 
            "strategy": "Target with discount offers, value bundles, and affordable alternatives.", 
            "examples": "Students, entry-level employees, retirees"
        }
    }
    
    # 4. Calculate ALL distances first to avoid greedy assignment errors
    matches = []
    for cid, center in enumerate(centroids):
        for pname, pcenter in ideal_profiles.items():
            dist = np.linalg.norm(center - pcenter)
            matches.append((dist, cid, pname))
            
    # 5. Sort matches from absolute smallest distance to largest
    matches.sort(key=lambda x: x[0])
    
    used_cids = set()
    used_pnames = set()
    
    # 6. Assign the true best matches globally
    for dist, cid, pname in matches:
        if cid not in used_cids and pname not in used_pnames:
            CLUSTER_INFO[cid] = templates[pname]
            used_cids.add(cid)
            used_pnames.add(pname)

except FileNotFoundError:
    print("⚠️  Model files not found!")
    print("   Please train the model using the Colab notebook first,")
    print("   then place kmeans_model.pkl and scaler.pkl in the model/ folder.")
    kmeans = None
    scaler = None


# Routes 

@app.route('/')
def index():
    """Main page with input form."""
    model_loaded = kmeans is not None and scaler is not None
    return render_template('index.html', model_loaded=model_loaded)


@app.route('/predict', methods=['POST'])
def predict():
    """Predict the customer segment."""
    if kmeans is None or scaler is None:
        return jsonify({'error': 'Model not loaded. Please train the model first.'}), 500

    try:
        # Get input values
        annual_income  = float(request.form.get('annual_income', 0))
        spending_score = float(request.form.get('spending_score', 0))

        # Validate inputs
        if not (1 <= annual_income <= 200):
            return jsonify({'error': 'Annual income must be between 1 and 200 (k$)'}), 400
        if not (1 <= spending_score <= 100):
            return jsonify({'error': 'Spending score must be between 1 and 100'}), 400

        # Preprocess & Predict
        features        = np.array([[annual_income, spending_score]])
        features_scaled = scaler.transform(features)
        cluster_id      = int(kmeans.predict(features_scaled)[0])

        # Get distances to all cluster centers
        distances = kmeans.transform(features_scaled)[0].tolist()

        # Get cluster info
        info = CLUSTER_INFO.get(cluster_id, {
            "name": f"Cluster {cluster_id}",
            "emoji": "⚪",
            "color": "#95A5A6",
            "badge": "secondary",
            "income_level": "Unknown",
            "spending_level": "Unknown",
            "description": "No description available.",
            "strategy": "No strategy available.",
            "examples": "N/A"
        })

        result = {
            'cluster_id':      cluster_id,
            'cluster_name':    info['name'],
            'emoji':           info['emoji'],
            'color':           info['color'],
            'badge':           info['badge'],
            'income_level':    info['income_level'],
            'spending_level':  info['spending_level'],
            'description':     info['description'],
            'strategy':        info['strategy'],
            'examples':        info['examples'],
            'annual_income':   annual_income,
            'spending_score':  spending_score,
            'distances':       [round(d, 4) for d in distances],
            'total_clusters':  kmeans.n_clusters,
        }

        return jsonify(result)

    except ValueError:
        return jsonify({'error': 'Invalid input. Please enter numeric values.'}), 400
    except Exception as e:
        return jsonify({'error': f'Prediction error: {str(e)}'}), 500


@app.route('/about')
def about():
    """About page explaining the ML concepts."""
    return render_template('about.html')


@app.route('/api/clusters')
def api_clusters():
    """API endpoint returning all cluster information."""
    if kmeans is None:
        return jsonify({'error': 'Model not loaded'}), 500
    return jsonify({
        'total_clusters': kmeans.n_clusters,
        'clusters': CLUSTER_INFO
    })


# Run the app
if __name__ == '__main__':
    print("\n" + "="*50)
    print("  🛍️  Customer Segmentation App")
    print("  Unsupervised ML with K-Means Clustering")
    print("="*50)
    print(f"\n  📍 Open: http://127.0.0.1:5000\n")
    app.run(debug=True, port=5000)