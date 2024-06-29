import requests
import os
import base64
from flask import Flask, request, render_template, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

def identify_plant(image_path, api_key):
    api_url = "https://api.plant.id/v2/identify"
    headers = {
        "Content-Type": "application/json",
        "Api-Key": api_key
    }

    with open(image_path, 'rb') as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')

    payload = {
        "images": [image_data],
        "organs": ["leaf"]
    }

    response = requests.post(api_url, json=payload, headers=headers)

    if response.status_code == 429:
        return None, "Error: Received status code 429. The specified API key does not have sufficient number of available credits."

    if response.status_code != 200:
        return None, f"Error: Received status code {response.status_code}. Response content: {response.text}"

    try:
        result = response.json()
    except requests.exceptions.JSONDecodeError:
        return None, f"Error: Unable to parse JSON response. Response content: {response.text}"

    return result, None

def display_results(results):
    if not results:
        return "No results found or there was an error."

    result_text = ""
    for suggestion in results['suggestions']:
        result_text += f"<strong>Plant Name:</strong> {suggestion['plant_name']}<br>"
        result_text += f"<strong>Probability:</strong> {suggestion['probability'] * 100:.2f}%<br>"
        if 'wiki_description' in suggestion['plant_details']:
            result_text += f"<strong>Description:</strong> {suggestion['plant_details']['wiki_description']['value']}<br><br>"
    return result_text

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            api_key = os.getenv("PLANT_ID_API_KEY")
            if not api_key:
                flash("API key not found. Please set the PLANT_ID_API_KEY environment variable.")
                return redirect(request.url)
            
            file_path = os.path.join('static', file.filename)
            file.save(file_path)
            
            results, error = identify_plant(file_path, api_key)
            if error:
                flash(error)
                return redirect(request.url)
            
            result_text = display_results(results)
            return render_template('index.html', result=result_text)
    
    return render_template('index.html', result='')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
