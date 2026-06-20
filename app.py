from flask import Flask, render_template, request
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Gemini設定
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():

    prompt = request.form["prompt"]

    try:
        model = genai.GenerativeModel("gemini-2.5-flash-lite")

        response = model.generate_content(prompt)

        return render_template(
            "index.html",
            prompt=prompt,
            result=response.text
        )

    except Exception as e:

        return render_template(
            "index.html",
            prompt=prompt,
            result=f"ERROR: {str(e)}"
        )

if __name__ == "__main__":
    app.run(debug=True)