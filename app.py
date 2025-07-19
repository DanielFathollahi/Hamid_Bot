from flask import Flask, jsonify

app = Flask(__name__)

resume_data = {
    "name": "Hamid",
    "age": 17,
    "skills": ["Swimming", "Water Polo", "Programming"],
    "goals": "Become a millionaire",
}

@app.route('/')
def home():
    return "Welcome to Hamid_Bot!"

@app.route('/resume')
def resume():
    return jsonify(resume_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
