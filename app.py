from flask import Flask, request, jsonify
from transcribe import process_b64_str

app = Flask(__name__)

@app.route('/transcribe', methods=['POST'])
def transcribe_endpoint():
    try:
        data = request.get_json()
        if not data or 'b64_str' not in data:
            return jsonify({'error': 'Missing base64 string (b64_str) in the request'}), 400
        b64_str = data['b64_str']
        transcription = process_b64_str(b64_str)

        return jsonify({'transcription': transcription})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1000, debug=True)

 