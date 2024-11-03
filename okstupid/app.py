import os
import random

from flask import Flask, render_template
import json
import markdown
import yaml


app = Flask(__name__)


_TRACKS = {
    "space lion": "WKnVaDwUg5s",  # Yoko Kanno
    "welcome to my life": "r0U0AlLVqpk",
    "mr rogers theme": "FhAJnx5uwUU"
}


@app.route("/")
def main():
    with open("okstupid/static/main_splash.md", 'r') as fh:
        html = markdown.markdown(fh.read())
    return render_template(
        "main.html",
        mkd_text=html,
        music_id=_TRACKS["welcome to my life"]
    )


@app.route("/cat")
def cat():
    with open("okstupid/static/cat.md", 'r') as fh:
        html = markdown.markdown(fh.read())

    return render_template(
        "main.html",
        mkd_text=html,
        music_id=_TRACKS["space lion"]
    )


@app.route("/cat/freddi")
def freddi():
    """
    Serve random images of Freddi
    """
    return render_template(
        "cat.html",
        music_id=_TRACKS["mr rogers theme"]
    )


@app.route("/cat/freddi/new_image")
def get_new_freddi_image():
    """
    API endpoint to just get a filename of freddi
    """
    filepath_base = "okstupid/static/freddi-images/"
    all_images = [
        fname for fname in os.listdir(filepath_base)
        if not fname.endswith(".yml")
    ]

    with open("okstupid/static/freddi-images/captions.yml", 'r') as fh:
        captions = yaml.load(fh, yaml.SafeLoader)

    img_to_captions = {img_spec["path"]: img_spec for img_spec in captions}
    img_to_return = all_images[random.randint(0, len(all_images) - 1)]
    img_spec = img_to_captions.get(
        img_to_return,
        {"path": img_to_return, "caption": "Freddi luvs u"}
    )

    return json.dumps(img_spec)


@app.route("/ev")
def ev():
    with open("okstupid/static/ev_conversion.md", 'r') as fh:
        html = markdown.markdown(fh.read())

    return render_template(
        "main.html",
        mkd_text=html,
        music_id=_TRACKS["space lion"]
    )
