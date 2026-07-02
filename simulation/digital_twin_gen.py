import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. PHYSICAL CONSTANTS (Change these based on your ESP32 tests) ---
FLOW_RATE_LPS = 0.025
NOISE_STD_DEV = 0.05  # 5% random sensor jitter

# --- 2. CONFIGURATION ---
DAYS_TO_GENERATE = 90  # 3 months of historical data
START_DATE = datetime.now() - timedelta(days=DAYS_TO_GENERATE)

def get_usage_seconds(hour, is_weekend):
    """
    Simulates INDUSTRIAL/COMMERCIAL valve state.
    Max capacity is 3600 seconds per hour.
    """
    usage = 0

    if not is_weekend:
        # WEEKDAY INDUSTRIAL PROFILE
        if 0 <= hour <= 4:
            # Night Baseline: Automated systems, leaks, minor HVAC (e.g., 5-10 mins/hr)
            usage = np.random.normal(500, 150) #16.25L to 8.75L

        elif 5 <= hour <= 7:
            # Morning Spin-up: Systems turn on, first shift arrives (e.g., 20-30 mins/hr)
            usage = np.random.normal(1700, 250) #49L to 36.25L

        elif 8 <= hour <= 17:
            # Peak Operations: Heavy, sustained industrial usage (e.g., 45-55 mins/hr)
            # Notice the high mean (3000 seconds)
            usage = np.random.normal(2900, 200) #77.5L to 67.5L

        elif 18 <= hour <= 19:
            # Shift End / Washdown: Heavy cleaning, second shift (e.g., 30-40 mins/hr)
            usage = np.random.normal(2400, 300) #67.5L to 52.5L

        else: # 20 to 23
            # Winding down to night baseline
            usage = np.random.normal(800, 200) #25L to 15L

    else:
        # WEEKEND PROFILE (Skeleton crew or basic maintenance)
        if 8 <= hour <= 16:
            # Daytime skeleton crew (e.g., 10-15 mins/hr)
            usage = np.random.normal(650, 200) #21.25L to 11.25L
        else:
            # Weekend night baseline
            usage = np.random.normal(200, 100) #7.5L to 2.5L

    # CRITICAL: We still clamp the usage. A valve CANNOT be open for more
    # than 3600 seconds in a 1-hour window. Physics won't allow it.
    return max(0, min(3600, int(usage)))

# --- 3. GENERATE THE DATASET ---
data = []
current_time = START_DATE

# Loop hour by hour for the total number of days
for _ in range(DAYS_TO_GENERATE * 24):
    hour = current_time.hour
    day_of_week = current_time.weekday() # 0 = Monday, 6 = Sunday
    is_weekend = day_of_week >= 5

    # Get simulated human behavior (seconds valve is open)
    valve_seconds = get_usage_seconds(hour, is_weekend)

    # Calculate pure physical volume
    base_volume = valve_seconds * FLOW_RATE_LPS

    # Inject real-world sensor noise (Only if water actually flowed)
    if base_volume > 0:
        noise = np.random.normal(0, base_volume * NOISE_STD_DEV)
        final_volume = round(base_volume + noise, 2)
    else:
        final_volume = 0.0

    # Append to our dataset
    data.append({
        'timestamp': current_time,
        'hour_of_day': hour,
        'day_of_week': day_of_week,
        'is_weekend': int(is_weekend),
        'valve_open_seconds': valve_seconds,
        'total_volume_liters': final_volume
    })

    # Move to the next hour
    current_time += timedelta(hours=1)

# --- 4. EXPORT TO CSV ---
df = pd.DataFrame(data)
df.set_index('timestamp', inplace=True)

filename = 'synthetic_water_data.csv'
df.to_csv(filename)

print(f"✅ Successfully generated {len(df)} rows of data.")
print(f"✅ Saved as '{filename}'")
print("\nFirst 5 rows:")
print(df.head())

import pandas as pd
import numpy as np

# 1. Load the generated data
# Make sure 'synthetic_water_data.csv' is in the same folder as this script
df = pd.read_csv('synthetic_water_data.csv', parse_dates=['timestamp'], index_col='timestamp')

print(f"Original dataset size: {len(df)} rows")

# 2. FEATURE ENGINEERING: Creating Lag Features
# We shift the target variable ('total_volume_liters') down to create past context.
# We MUST predict the future based on the past, so we use shift()

# How much water was used exactly 1 hour ago?
df['volume_1h_ago'] = df['total_volume_liters'].shift(1)

# How much water was used exactly 2 hours ago?
df['volume_2h_ago'] = df['total_volume_liters'].shift(2)

# How much water was used exactly 24 hours ago? (Crucial for learning daily routines!)
df['volume_24h_ago'] = df['total_volume_liters'].shift(24)

# What was the average water usage over the last 6 hours? (Rolling average)
# Notice we shift(1) first so we don't accidentally include the CURRENT hour in the past average
df['rolling_avg_6h'] = df['total_volume_liters'].shift(1).rolling(window=6).mean()

# 3. CLEAN UP: Drop NaN Values
# Because we shifted data by 24 hours, the first 24 rows of our dataset now have "NaN"
# (Not a Number) in the 'volume_24h_ago' column. AI models crash if they see NaNs.
df = df.dropna()

print(f"Dataset size after dropping NaNs: {len(df)} rows")

# 4. DEFINE FEATURES (X) AND TARGET (y)
# 'y' is what we want to predict. 'X' is the context we use to predict it.
# We DROP 'valve_open_seconds' because in the real world, you won't know how long
# the valve will be open tomorrow!
target = 'total_volume_liters'
features = [
    'hour_of_day',
    'day_of_week',
    'is_weekend',
    'volume_1h_ago',
    'volume_2h_ago',
    'volume_24h_ago',
    'rolling_avg_6h'
]

X = df[features]
y = df[target]

# 5. TIME-SERIES TRAIN/TEST SPLIT
# CRITICAL CAPSTONE RULE: Never use "train_test_split" from sklearn blindly,
# because it randomizes data. You cannot use data from Friday to predict Wednesday.
# We must split chronologically. The first 80% of days is for training, the last 20% for testing.

split_index = int(len(df) * 0.8)

X_train, X_test = X.iloc[:split_index], X.iloc[split_index:]
y_train, y_test = y.iloc[:split_index], y.iloc[split_index:]

print(f"Training on {len(X_train)} hours, Testing on {len(X_test)} hours.")

df.info() #df = file. info gives info ya fasal

from google.colab import drive
drive.mount('/content/drive')

from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

# --- Model 1: The Baseline (Random Forest) ---
print("\n--- Training Random Forest ---")
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

# Make predictions on the unseen test data
rf_predictions = rf_model.predict(X_test)

# Calculate Error (Mean Absolute Error)
rf_mae = mean_absolute_error(y_test, rf_predictions)
print(f"Random Forest MAE: {rf_mae:.2f} Liters")


# --- Model 2: The Optimizer (XGBoost) ---
print("\n--- Training XGBoost ---")
xgb_model = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
xgb_model.fit(X_train, y_train)

# Make predictions on the unseen test data
xgb_predictions = xgb_model.predict(X_test)

# Calculate Error
xgb_mae = mean_absolute_error(y_test, xgb_predictions)
print(f"XGBoost MAE: {xgb_mae:.2f} Liters")

# --- The Capstone Conclusion ---
print("\n--- CAPSTONE RESULTS ---")
if xgb_mae < rf_mae:
    improvement = ((rf_mae - xgb_mae) / rf_mae) * 100
    print(f"XGBoost outperformed Random Forest by {improvement:.1f}%!")
else:
    print("Random Forest provided a more robust baseline for this specific dataset.")

#OPTIMIZATION OF TRAINING
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from xgboost import XGBRegressor

print("\n--- Starting XGBoost Hyperparameter Tuning ---")

# 1. Define the grid of parameters you want to test
# The model will test EVERY combination of these numbers.
param_grid = {
    'n_estimators': [50, 100, 200],       # Number of trees
    'learning_rate': [0.01, 0.05, 0.1],   # How aggressively it corrects errors
    'max_depth': [3, 5, 7]                # How deep/complex each tree is allowed to get
}

# 2. Set up the Time Series Cross-Validation
# This ensures we test chronological chunks safely (e.g., train on week 1, test week 2)
tscv = TimeSeriesSplit(n_splits=3)

# 3. Set up the Grid Search
# We use 'neg_mean_absolute_error' because GridSearchCV always tries to MAXIMIZE the score,
# so we give it negative errors to maximize (getting closer to 0).
grid_search = GridSearchCV(
    estimator=XGBRegressor(random_state=42),
    param_grid=param_grid,
    cv=tscv,
    scoring='neg_mean_absolute_error',
    verbose=1 # This will print out the progress so you know it's working
)

# 4. Run the Search (This might take a minute!)
print("Searching for the best parameters. Please wait...")
grid_search.fit(X_train, y_train)

# 5. Get the best results
best_xgb_model = grid_search.best_estimator_

print("\n✅ Tuning Complete!")
print(f"Best Parameters Found: {grid_search.best_params_}")

# 6. Test the OPTIMIZED model on our final test set
optimized_predictions = best_xgb_model.predict(X_test)
optimized_mae = mean_absolute_error(y_test, optimized_predictions)

print(f"Optimized XGBoost MAE: {optimized_mae:.2f} Liters")

import matplotlib.pyplot as plt
import seaborn as sns

# 1. Get the importance scores from your optimized model
importances = best_xgb_model.feature_importances_

# 2. Match them up with our feature names
feature_importance_df = pd.DataFrame({
    'Feature': features,
    'Importance': importances
})

# 3. Sort them from most important to least important
feature_importance_df = feature_importance_df.sort_values(by='Importance', ascending=False)

# 4. Plot the graph!
plt.figure(figsize=(10, 6))
sns.barplot(x='Importance', y='Feature', data=feature_importance_df, palette='viridis')

plt.title('XGBoost Feature Importance: What Drives Water Demand?', fontsize=14, fontweight='bold')
plt.xlabel('Relative Importance (0 to 1)', fontsize=12)
plt.ylabel('Features', fontsize=12)
plt.tight_layout()

# Save the plot so you can put it in your presentation
plt.savefig('feature_importance.png', dpi=300)
plt.show()

print("\nFeature Importance Breakdown:")
print(feature_importance_df)

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

# --- 1. CALCULATE ADVANCED METRICS ---
# We already have MAE, but examiners will also look for RMSE and R-Squared
mae = mean_absolute_error(y_test, optimized_predictions)
rmse = np.sqrt(mean_squared_error(y_test, optimized_predictions))
r2 = r2_score(y_test, optimized_predictions)

print("--- MODEL BENCHMARK METRICS ---")
print(f"Mean Absolute Error (MAE): {mae:.2f} Liters")
print(f"Root Mean Squared Error (RMSE): {rmse:.2f} Liters")
print(f"R-Squared (R²): {r2:.4f} (Closer to 1.0 is better)")
print("-------------------------------\n")

# --- 2. GRAPH 1: TIME SERIES LINE CHART (Actual vs Predicted) ---
# This graph shows how well the model follows the peaks and valleys over time.
# We will only plot a slice (e.g., the first 7 days / 168 hours of the test set)
# so the graph isn't too cluttered to read.

plot_hours = 168 # 7 days * 24 hours

plt.figure(figsize=(14, 6))
# Plot actual data
plt.plot(y_test.index[:plot_hours], y_test.values[:plot_hours],
         label='Real Water Consumption', color='#1f77b4', linewidth=2, alpha=0.8)

# Plot AI predictions
plt.plot(y_test.index[:plot_hours], optimized_predictions[:plot_hours],
         label='AI Predicted Consumption', color='#ff7f0e', linewidth=2, linestyle='--')

plt.title('Time Series Benchmark: Real vs. AI Predicted Water Usage (1 Week Sample)', fontsize=14, fontweight='bold')
plt.xlabel('Date and Time', fontsize=12)
plt.ylabel('Water Volume (Liters)', fontsize=12)
plt.legend(loc='upper right', fontsize=11)
plt.grid(True, linestyle=':', alpha=0.7)
plt.tight_layout()

# Save for your presentation
plt.savefig('timeseries_benchmark.png', dpi=300)
plt.show()

# --- 3. GRAPH 2: SCATTER PLOT (Prediction Accuracy Distribution) ---
# This graph shows variance. If the AI is perfect, all dots will form a perfect 45-degree line.

plt.figure(figsize=(8, 8))
plt.scatter(y_test, optimized_predictions, alpha=0.4, color='purple', edgecolors='k', s=50)

# Draw the "Perfect Prediction" reference line
max_val = max(max(y_test), max(optimized_predictions))
plt.plot([0, max_val], [0, max_val], color='red', linestyle='--', linewidth=2, label='Perfect Prediction Line')

plt.title('Model Accuracy: Predicted vs. Actual Values', fontsize=14, fontweight='bold')
plt.xlabel('Actual Volume (Liters)', fontsize=12)
plt.ylabel('AI Predicted Volume (Liters)', fontsize=12)
plt.legend(fontsize=11)
plt.grid(True, linestyle=':', alpha=0.7)
plt.tight_layout()

# Save for your presentation
plt.savefig('scatter_benchmark.png', dpi=300)
plt.show()

# Save the optimized XGBoost model to a JSON file
filename = "water_demand_xgboost_model.json"
best_xgb_model.save_model(filename)

print(f"✅ Model successfully exported as '{filename}'!")