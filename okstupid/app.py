import os
from datetime import datetime
from flask import Flask, redirect, render_template, request
import json
import random

import flask
import flask_login
import markdown
import plotly.graph_objects as go
from werkzeug.middleware.proxy_fix import ProxyFix
import yaml

from . import blog
from . import login as app_login
from .dank_memes import MEMES
from . import resources


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.register_blueprint(MEMES, url_prefix="/memes")
app.secret_key = "super secret string"

login_manager = app_login.get_login_manager()
login_manager.init_app(app)


@app.route("/")
def main():
    with open("okstupid/static/markdowns/main_splash.md", "r") as fh:
        html = markdown.markdown(fh.read())
    return render_template(
        "main.html",
        title="welcome to a life",
        mkd_text=html,
        music_id=resources.TRACKS["welcome to my life"],
    )


@app.get("/login")
def login_get():
    return """
    <form method=post>
    Username: <input name="username"><br>
    Password: <input name="password" type=password><br>
    <button>Log In</button>
    </form>
    """


@app.post("/login")
def login_post():
    user = app_login.users.get(request.form["username"])
    if user is None or user.password != request.form["password"]:
        return redirect(flask.url_for("login"))

    flask_login.login_user(user)
    return flask.redirect(flask.url_for("protected"))


@app.route("/protected")
@flask_login.login_required
def protected():
    return f"""YOU ARE IN SECRET LAND! Logged in as {flask_login.current_user.id}"""


@app.route("/cat")
def cat():
    with open("okstupid/static/markdowns/cat.md", "r") as fh:
        html = markdown.markdown(fh.read())

    return render_template(
        "main.html",
        title="mah boi",
        mkd_text=html,
        music_id=resources.TRACKS["space lion"],
    )


@app.route("/cat/freddi")
def freddi():
    """
    Serve random images of Freddi
    """
    return render_template("cat.html", music_id=resources.TRACKS["mr rogers theme"])


@app.route("/blog/admin")
@flask_login.login_required
def blog_admin():
    con = blog.get_sql_connection()
    blog_entries = blog.load_blog_entries(con)

    return render_template(
        "blog_admin.html", title="blog admin page", blog_entries=blog_entries
    )


@app.route("/cat/freddi/new_image")
def get_new_freddi_image():
    """
    API endpoint to just get a filename of freddi
    """
    filepath_base = "okstupid/static/freddi-images/"
    all_images = [
        fname for fname in os.listdir(filepath_base) if not fname.endswith(".yml")
    ]

    with open("okstupid/static/freddi-images/captions.yml", "r") as fh:
        captions = yaml.load(fh, yaml.SafeLoader)

    img_to_captions = {img_spec["path"]: img_spec for img_spec in captions}
    img_to_return = all_images[random.randint(0, len(all_images) - 1)]
    img_spec = img_to_captions.get(
        img_to_return, {"path": img_to_return, "caption": "Freddi luvs u"}
    )

    return json.dumps(img_spec)


@app.route("/ev")
def ev():
    with open("okstupid/static/markdowns/ev_conversion.md", "r") as fh:
        html = markdown.markdown(fh.read())

    return render_template(
        "main.html", title="EV", mkd_text=html, music_id=resources.TRACKS["space lion"]
    )


@app.route("/blog")
def blog_():
    # Generate a markdown string of a list of links of blog entries
    link_list = blog.generate_blog_nav_md()

    return render_template(
        "main.html",
        title="my blog",
        mkd_text=markdown.markdown(link_list),
        music_id=resources.TRACKS["space lion"],
    )


@app.route("/blog/<blog_id_slug>")
def get_blog_page(blog_id_slug: str):
    blog_id = int(blog_id_slug[6:])
    con = blog.get_sql_connection()
    blog_entry, raw_text = blog.BlogEntry.load(con, blog_id)

    html = markdown.markdown(raw_text)
    blog_nav_txt = markdown.markdown(blog.generate_blog_nav_md())
    blog_nav_buttons = blog.generate_nav_buttons(blog_entry.create_date)

    if blog_entry.track_tag is None:
        song = random.choice(list(resources.TRACKS.keys()))
    else:
        song = blog_entry.track_tag

    return render_template(
        "blog.html",
        title=blog_entry.title,
        nav_text=blog_nav_txt,
        mkd_text=html,
        nav_buttons=blog_nav_buttons,
        music_id=resources.TRACKS[song],
    )


@app.route("/blog/<blog_id_slug>/edit")
@flask_login.login_required
def edit_blog_page(blog_id_slug: str):
    blog_id = int(blog_id_slug[6:])
    con = blog.get_sql_connection()
    blog_entry, raw_text = blog.BlogEntry.load(con, blog_id)
    return render_template(
        "blog_edit_page.html",
        title=blog_entry.title,
        track_tag=blog_entry.track_tag,
        create_date=blog_entry.create_date.strftime("%Y-%m-%d"),
        available_tracks=sorted(resources.TRACKS.keys()),
        blog_id=blog_id_slug,
        initial_text=raw_text,
    )


@app.route("/blog/<blog_id_slug>/save", methods=["POST"])
@flask_login.login_required
def save_blog_page(blog_id_slug: str):
    blog_id = int(blog_id_slug[6:])
    con = blog.get_sql_connection()
    blog_entry = blog.BlogEntry.load_only_blog_entry(con, blog_id)
    blog_entry.title = request.form["title"]
    blog_entry.create_date = datetime.strptime(request.form["create_date"], "%Y-%m-%d")
    if request.form["track"] not in resources.TRACKS:
        track_tag = None
    else:
        track_tag = request.form["track"]
    blog_entry.track_tag = track_tag

    blog_entry.update_blog_entry(con, request.form["content"])

    return redirect(
        flask.url_for("edit_blog_page", blog_id_slug=blog_id_slug), code=302
    )


@app.route("/blog/add")
def add_blog_page():
    return render_template(
        "blog_edit_page.html",
        title="Title",
        track_tag=None,
        create_date=datetime.now().strftime("%Y-%m-%d"),
        available_tracks=sorted(resources.TRACKS.keys()),
        blog_id="",
        initial_text="",
    )


@app.route("/blog/create_new", methods=["POST"])
@flask_login.login_required
def create_blog_post():
    con = blog.get_sql_connection()
    if request.form["track"] not in resources.TRACKS:
        track_tag = None
    else:
        track_tag = request.form["track"]
    entry = blog.BlogEntry(
        create_date=datetime.now(), title=request.form["title"], track_tag=track_tag
    )
    entry.insert_new_blog_entry(con, request.form["content"])
    return redirect(
        flask.url_for("edit_blog_page", blog_id_slug=f"entry-{entry.id}"), code=302
    )


@app.route("/blog/<blog_id_slug>/delete")
@flask_login.login_required
def delete_blog_entry(blog_id_slug: str):
    blog_id = int(blog_id_slug[6:])
    con = blog.get_sql_connection()
    blog.delete_blog_entry(con, blog_id)
    return redirect("/blog/admin")


@app.route("/karaoke-list")
def karaoke_list():
    return redirect(
        "https://music.youtube.com/playlist?list=PLowuBbuIg1YINrsTBchxyk0eB-0pT3OYp&si=x-teddp5rRcUjyVg",
        code=307,
    )


@app.route("/more-about-me")
def more_about_me():
    with open("okstupid/static/markdowns/more_about_me.md", "r") as fh:
        html = markdown.markdown(fh.read())

    return render_template(
        "main.html",
        title="more sincere",
        mkd_text=html,
        music_id=resources.TRACKS["space lion"],
    )


@app.route("/plotly-demo")
def plotly_demo():
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 1, 2], y=[2, 1, 1]))

    figjson = fig.to_json()

    return render_template(
        "plotly_page.html",
        title="plotly demo",
        graph_json=figjson,
        music_id=resources.TRACKS["space lion"],
    )
