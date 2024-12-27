import json
from flask import Flask, render_template, request, jsonify
import pandas as pd

# Initialize Flask app
app = Flask(__name__)

# Load datasets from CSV files
try:
    gov_dataset = pd.read_csv('government.csv')
    prediction_dataset = pd.read_csv('prediction.csv')
except FileNotFoundError:
    print("Error: One or more CSV files not found!")
    gov_dataset = prediction_dataset = pd.DataFrame()  # Empty DataFrame as fallback

# Clean column names if necessary (remove extra spaces)
gov_dataset.columns = gov_dataset.columns.str.strip()
prediction_dataset.columns = prediction_dataset.columns.str.strip()


# Home Route
@app.route('/')
def index():
    return render_template('index.html')

# Market Insight Page (for rendering graphs)
@app.route('/market-insight')
def market_insight():
    return render_template('market_insight.html')

# About Us Page
@app.route('/about-us')
def about_us():
    return render_template('about_us.html')

# Contact Us Page (with form submission)
@app.route('/contact-us', methods=['GET', 'POST'])
def contact_us():
    if request.method == 'POST':
        query = request.json.get('query') if request.is_json else request.form.get('query')
        print(f"Received Query: {query}")
        return jsonify({"message": "Your query has been submitted successfully!"})
    return render_template('contact_us.html')

# Assuming you have a function to make predictions
def get_predicted_price(village, street_name, sub_registrar_office):
    # Filter the dataset based on user selections
    filtered_data = prediction_dataset[
        (prediction_dataset['Village'] == village) &
        (prediction_dataset['Street Name'] == street_name) &
        (prediction_dataset['Sub-Registrar-Office'] == sub_registrar_office)
    ]
    
    # Fetch the predicted price from the filtered dataset (assuming 'Predicted Price' is a column in your dataset)
    if not filtered_data.empty:
        return filtered_data[['Predicted Price']].values[0][0]
    else:
        return "No data available for the selected filters."

@app.route('/get-property', methods=['GET', 'POST'])
def get_property():
    if request.method == 'POST':
        village = request.form.get('village')
        street_name = request.form.get('street_name')
        sub_registrar_office = request.form.get('sub_registrar_office')

        # Get predicted price for selected filters
        predicted_price = get_predicted_price(village, street_name, sub_registrar_office)

        return jsonify({'predicted_price': predicted_price})

    # GET request handling (initial load)
    villages = prediction_dataset['Village'].unique().tolist()
    street_names = prediction_dataset['Street Name'].unique().tolist()
    sub_registrar_offices = prediction_dataset['Sub-Registrar-Office'].unique().tolist()

    return render_template(
        'get_property.html',
        villages=villages,
        street_names=street_names,
        sub_registrar_offices=sub_registrar_offices
    )
@app.route('/get-villages', methods=['GET'])
def get_villages():
    sub_registrar_office = request.args.get('sub_registrar_office')
    villages = prediction_dataset[prediction_dataset['Sub-Registrar-Office'] == sub_registrar_office]['Village'].unique().tolist()
    return jsonify({'villages': villages})

@app.route('/get-streets', methods=['GET'])
def get_streets():
    sub_registrar_office = request.args.get('sub_registrar_office')
    village = request.args.get('village')
    streets = prediction_dataset[
        (prediction_dataset['Sub-Registrar-Office'] == sub_registrar_office) & 
        (prediction_dataset['Village'] == village)
    ]['Street Name'].unique().tolist()
    return jsonify({'streets': streets})

@app.route('/get-predicted-price', methods=['GET'])
def get_predicted_price():
    sub_registrar_office = request.args.get('sub_registrar_office')
    village = request.args.get('village')
    street_name = request.args.get('street_name')

    # Filter the prediction dataset
    filtered_data = prediction_dataset[
        (prediction_dataset['Sub-Registrar-Office'] == sub_registrar_office) &
        (prediction_dataset['Village'] == village) &
        (prediction_dataset['Street Name'] == street_name)
    ]

    # Fetch predicted price
    if not filtered_data.empty:
        predicted_price = filtered_data[['Year', 'Projected Price']].sort_values(by='Year').to_dict(orient='records')
    else:
        predicted_price = []

    # Filter the government dataset to get prices year-wise
    gov_prices = gov_dataset[
        (gov_dataset['Sub-Registrar-Office'] == sub_registrar_office) &
        (gov_dataset['Village'] == village) &
        (gov_dataset['Street Name'] == street_name)
    ]

    # Get the year-wise price from the government dataset
    gov_price_yearwise = gov_prices[['Year', 'Price']].sort_values(by='Year').to_dict(orient='records')

    return jsonify({
        'predicted_price': predicted_price,
        'gov_price_yearwise': gov_price_yearwise
    })

@app.route('/filter-properties', methods=['POST'])
def filter_properties():
    village = request.form.get('village')
    street_name = request.form.get('street_name')
    sub_registrar_office = request.form.get('sub_registrar_office')

    filtered_data = prediction_dataset
    if village:
        filtered_data = filtered_data[filtered_data['Village'] == village]
    if street_name:
        filtered_data = filtered_data[filtered_data['Street Name'] == street_name]
    if sub_registrar_office:
        filtered_data = filtered_data[filtered_data['Sub-Registrar-Office'] == sub_registrar_office]

    properties = filtered_data[['Village', 'Street Name', 'Sub-Registrar-Office', 'Year', 'Projected Price']].to_dict(orient='records')
    return jsonify(properties)

if __name__ == '__main__':
    app.run(debug=True, port=5005)
