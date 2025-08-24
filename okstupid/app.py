from datetime import datetime
import os
import random

from flask import Flask, render_template
import json
import markdown
import plotly.graph_objects as go
from werkzeug.middleware.proxy_fix import ProxyFix
import yaml

from . import blog
from .dank_memes import MEMES


app = Flask(__name__)
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)
app.register_blueprint(MEMES, url_prefix="/memes")


_TRACKS = {
    "space lion": "WKnVaDwUg5s",  # Yoko Kanno
    "welcome to my life": "r0U0AlLVqpk",
    "mr rogers theme": "FhAJnx5uwUU"
}


@app.route("/")
def main():
    with open("okstupid/static/markdowns/main_splash.md", 'r') as fh:
        html = markdown.markdown(fh.read())
    return render_template(
        "main.html",
        title="welcome to a life",
        mkd_text=html,
        music_id=_TRACKS["welcome to my life"]
    )


@app.route("/cat")
def cat():
    with open("okstupid/static/markdowns/cat.md", 'r') as fh:
        html = markdown.markdown(fh.read())

    return render_template(
        "main.html",
        title="mah boi",
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
    with open("okstupid/static/markdowns/ev_conversion.md", 'r') as fh:
        html = markdown.markdown(fh.read())

    return render_template(
        "main.html",
        title="EV",
        mkd_text=html,
        music_id=_TRACKS["space lion"]
    )


@app.route("/blog")
def blog_():

    # Generate a markdown string of a list of links of blog entries
    link_list = blog.generate_blog_nav_md()

    return render_template(
        "main.html",
        title="my blog",
        mkd_text=markdown.markdown(link_list),
        music_id=_TRACKS["space lion"]
    )


@app.route("/blog/<blog_date>")
def get_blog_page(blog_date):
    with open(os.path.join("okstupid/blog", blog_date) + ".md", 'r') as fh:
        html = markdown.markdown(fh.read())

    blog_date_dt = datetime.strptime(blog_date, "%m-%d-%Y")
    blog_nav_txt = markdown.markdown(blog.generate_blog_nav_md())
    blog_nav_buttons = blog.generate_nav_buttons(blog_date_dt)

    song = random.choice(list(_TRACKS.keys()))

    return render_template(
        "blog.html",
        title="EV blog",
        nav_text=blog_nav_txt,
        mkd_text=html,
        nav_buttons=blog_nav_buttons,
        music_id=_TRACKS[song]
    )


@app.route("/more-about-me")
def more_about_me():
    with open("okstupid/static/markdowns/more_about_me.md", 'r') as fh:
        html = markdown.markdown(fh.read())

    return render_template(
        "main.html",
        title="more sincere",
        mkd_text=html,
        music_id=_TRACKS["space lion"]
    )

@app.route("/plotly-demo")
def plotly_demo():
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[0, 1, 2],
            y=[2, 1, 1]
        )
    )

    figjson = fig.to_json()

    return render_template(
        "plotly_page.html",
        title="plotly demo",
        graph_json=figjson,
        music_id=_TRACKS["space lion"]
    )