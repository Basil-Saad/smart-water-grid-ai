from flask import Flask, request, jsonify
from flask_cors import CORS
import xgboost as xgb
import numpy as np
from datetime import datetime
import random

app = Flask(__name__)
CORS(app)

# Load the XGBoost model
model = xgb.Booster()
model.load_model('water_demand_xgboost_model.json')

# Feature names (must match training)
FEATURE_NAMES = [
    'hour_of_day',
    'day_of_week', 
    'is_weekend',
    'volume_1h_ago',
    'volume_2h_ago',
    'volume_24h_ago',
    'rolling_avg_6h'
]

def get_base_demand(hour):
    """
    Generate base water demand based on time of day.
    Returns expected liters per hour.
    """
    if 0 <= hour <= 4:
        return random.uniform(8.75, 16.25) 
    
    elif 5 <= hour <= 7:
        return random.uniform(36.25, 49)
    
    elif 8 <= hour <= 17:
        return random.uniform(67.5, 77.5)
    
    elif 18 <= hour <= 19:
        return random.uniform(52.5, 67)
    
    else:
        return random.uniform(15, 25)

def blend_values(time_based, consumption_based, time_weight=0.5):
    """
    Blend time-based and consumption-based values.
    time_weight: 0.0 = all consumption, 1.0 = all time, 0.5 = equal mix
    """
    return (time_based * time_weight) + (consumption_based * (1 - time_weight))

def generate_fake_history(hour, day_of_week, is_weekend, current_consumption):
    """
    Generate fake historical data based on BOTH time patterns AND current consumption.
    """
    # Get time-based values
    time_base = get_base_demand(hour)
    
    # Weekend adjustment for time-based
    if is_weekend:
        if 8 <= hour <= 16:
            time_base = random.uniform(11.25, 21.25)
        else:
            time_base = random.uniform(2.5, 7.5)
    
    # If no current consumption, use only time-based
    if current_consumption <= 0:
        consumption_factor = 1.0
    else:
        # Scale factor: how current consumption compares to time-based expectation
        # If consuming more than expected, factor > 1
        # If consuming less than expected, factor < 1
        consumption_factor = current_consumption / max(time_base, 1)
        # Limit the factor to reasonable range
        consumption_factor = max(0.3, min(consumption_factor, 3.0))
    
    # ----- VOLUME 1 HOUR AGO -----
    hour_1h_ago = (hour - 1) % 24
    time_value_1h = get_base_demand(hour_1h_ago)
    consumption_value_1h = current_consumption * random.uniform(0.85, 1.15)
    volume_1h_ago = blend_values(time_value_1h, consumption_value_1h, time_weight=0.4)
    
    # ----- VOLUME 2 HOURS AGO -----
    hour_2h_ago = (hour - 2) % 24
    time_value_2h = get_base_demand(hour_2h_ago)
    consumption_value_2h = current_consumption * random.uniform(0.75, 1.25)
    volume_2h_ago = blend_values(time_value_2h, consumption_value_2h, time_weight=0.5)
    
    # ----- VOLUME 24 HOURS AGO -----
    # Same hour yesterday - more weight on time pattern
    time_value_24h = time_base * random.uniform(0.8, 1.2)
    consumption_value_24h = current_consumption * random.uniform(0.7, 1.3)
    volume_24h_ago = blend_values(time_value_24h, consumption_value_24h, time_weight=0.6)
    
    # ----- ROLLING AVERAGE 6 HOURS -----
    # Calculate time-based rolling average
    rolling_sum_time = 0
    for i in range(1, 7):
        h = (hour - i) % 24
        rolling_sum_time += get_base_demand(h)
    time_rolling = rolling_sum_time / 6
    
    # Consumption-based rolling
    consumption_rolling = current_consumption * random.uniform(0.8, 1.2)
    
    rolling_avg_6h = blend_values(time_rolling, consumption_rolling, time_weight=0.5)
    
    # Weekend adjustment for all values
    if is_weekend:
        weekend_factor = random.uniform(0.7, 0.9)
        volume_1h_ago *= weekend_factor
        volume_2h_ago *= weekend_factor
        volume_24h_ago *= weekend_factor
        rolling_avg_6h *= weekend_factor
    
    return volume_1h_ago, volume_2h_ago, volume_24h_ago, rolling_avg_6h

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get current consumption from request
        data = request.json
        current_consumption = data.get('consumption', 0)
        
        # Check if manual time is provided
        manual_hour = data.get('hour', None)
        manual_day = data.get('day', None)
        
        # Use manual values or get from system clock
        if manual_hour is not None:
            hour_of_day = int(manual_hour)
        else:
            hour_of_day = datetime.now().hour
        
        if manual_day is not None:
            day_of_week = int(manual_day)
        else:
            day_of_week = datetime.now().weekday()
        
        is_weekend = 1 if day_of_week >= 5 else 0
        
        # Generate fake historical data based on TIME + CONSUMPTION
        volume_1h_ago, volume_2h_ago, volume_24h_ago, rolling_avg_6h = generate_fake_history(
            hour_of_day, day_of_week, is_weekend, current_consumption
        )
        
        # Create feature array
        features = np.array([[
            hour_of_day,
            day_of_week,
            is_weekend,
            volume_1h_ago,
            volume_2h_ago,
            volume_24h_ago,
            rolling_avg_6h
        ]])
        
        # Create DMatrix WITH feature names
        dmatrix = xgb.DMatrix(features, feature_names=FEATURE_NAMES)
        
        # Make prediction
        prediction = model.predict(dmatrix)[0]
        
        # Get time period name
        if 0 <= hour_of_day <= 4:
            period = "Night Baseline"
        elif 5 <= hour_of_day <= 7:
            period = "Morning Spin-up"
        elif 8 <= hour_of_day <= 17:
            period = "Peak Operations"
        elif 18 <= hour_of_day <= 19:
            period = "Shift End"
        else:
            period = "Winding down to night baseline"
        
        # Day names
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Return result
        return jsonify({
            'success': True,
            'prediction': float(prediction),
            'current_consumption': current_consumption,
            'time_info': {
                'hour': hour_of_day,
                'day_of_week': day_of_week,
                'day_name': day_names[day_of_week],
                'is_weekend': bool(is_weekend),
                'period': period,
                'manual_time': manual_hour is not None or manual_day is not None
            },
            'features_used': {
                'hour_of_day': hour_of_day,
                'day_of_week': day_of_week,
                'is_weekend': is_weekend,
                'volume_1h_ago': round(volume_1h_ago, 2),
                'volume_2h_ago': round(volume_2h_ago, 2),
                'volume_24h_ago': round(volume_24h_ago, 2),
                'rolling_avg_6h': round(rolling_avg_6h, 2)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'running'})

if __name__ == '__main__':
    print("Starting AquaGrid Prediction Server...")
    print("Model loaded successfully!")
    print("Using TIME + CONSUMPTION based demand patterns")
    app.run(host='0.0.0.0', port=5000, debug=True)