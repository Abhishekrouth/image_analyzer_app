from flask import Flask, jsonify, request, abort
import requests
import base64
import os
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")

@app.errorhandler(400)
def bad_request(e):
    return jsonify({
        "status": "error",
        "code": 400,
        "message": "Bad Request. Image file is missing."
    }), 400
@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "status": "error",
        "code": 404,
        "message": "Target language is missing."
    }), 404
@app.route("/image_analyzer", methods=["POST"])
def image_analyzer():
    if "image_file" not in request.files:
        abort(400)
    image_file = request.files["image_file"]
    image_content = base64.b64encode(image_file.read())
    img= image_content.decode("utf-8")

    url = f"https://vision.googleapis.com/v1/images:annotate?key={google_api_key}"
    url_for_translation = f"https://translation.googleapis.com/language/translate/v2?key={google_api_key}"

    body = {
        "requests": [
            {
                "image": {
                    "content": img
                    },
                "features": [
                    {
                        "type": "LABEL_DETECTION",
                        "maxResults": 1
                    },
                    {
                        "type": "TEXT_DETECTION",
                        "maxResults": 1
                    },
                    {
                        "type": "FACE_DETECTION",
                        "maxResults": 2
                    }
                    
                        ]
            }
        ]
    }
    response = requests.post(url, json=body)
    result = response.json()
    text = result["responses"][0].get("textAnnotations",[])
    face = result["responses"][0].get("faceAnnotations",[])
    if face:
        exp1 = face[0]["joyLikelihood"]
        exp2 = face[0]["sorrowLikelihood"]
        exp3= face[0]["angerLikelihood"]
        exp4= face[0]["surpriseLikelihood"]
        return jsonify ({"Likelihoods:"  : {
                        "joyLikelihood": exp1,
                        "sorrowLikelihood": exp2,
                        "angerLikelihood": exp3,
                        "supriseLikelihood": exp4
                        },
                        "message": "No text or labels detected in the image"
                        })
    elif text:
        text = result["responses"][0].get("textAnnotations",[])
        des = text[0]["description"]
        final_des = des.replace('\n', ' ').replace('\r', '')
        target_language = request.form.get("target_language")
        if not target_language:
            abort(404)
        body_translation = {
            "q": final_des,
            "target": target_language,
            "format": "text"
            }
        response_translation = requests.post(url_for_translation, json=body_translation)
        result_translation = response_translation.json()
        translated = result_translation["data"]["translations"][0]["translatedText"]
        final_translated = translated.replace('\n', '').replace('\r', '')
        return jsonify({
            "Original_text": final_des,
            "target language": target_language,
            "Translated_text": final_translated,
            "message": "No face or label detected in the image"         
        })
    else:
        labels = result["responses"][0].get("labelAnnotations",[])
        return jsonify({
            "Labels": labels,
            "message": "No text or faces detected in the image"
    })


if __name__ == "__main__":
    app.run(debug=True)