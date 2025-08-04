from flask import Flask, request, jsonify

app = Flask(__name__)

# Temporary storage for one submitted JSON
stored_data = {}

# POST: Receive and store JSON
@app.route('/submit', methods=['POST'])
def submit_data():
    global stored_data
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    stored_data = data  # Save the submitted JSON
    return jsonify({"message": "Data stored successfully"}), 200

# GET: Return the stored JSON
@app.route('/view', methods=['GET'])
def view_data():
    if not stored_data:
        return jsonify({"message": "No data found"}), 404
    return jsonify(stored_data), 200

if __name__ == '__main__':
    app.run(debug=True, port= 8080)
