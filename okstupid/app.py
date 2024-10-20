from flask import Flask, render_template
import markdown
import os


app = Flask(__name__)


@app.route("/")
def main():
    with open("okstupid/static/main_splash.md", 'r') as fh:
        html = markdown.markdown(fh.read())
    return render_template("main.html", mkd_text=html)


@app.route("/cat")
def cat():
    with open("okstupid/static/cat.md", 'r') as fh:
        html = markdown.markdown(fh.read())

    return render_template("main.html", mkd_text=html)


@app.route("/ev")
def ev():
    with open("okstupid/static/ev_conversion.md", 'r') as fh:
        html = markdown.markdown(fh.read())

    return render_template("main.html", mkd_text=html)
