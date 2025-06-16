from flask import Blueprint, render_template
import markdown


MEMES = Blueprint("memes", __name__, template_folder="templates")


@MEMES.route("/")
def memes():
    return render_template(
        "main.html",
        title="dank memes",
        mkd_text=markdown.markdown("""
Peruse the dank memes here.

- [Selkirk](/memes/selkirk)
- [Crustard](/memes/crustard)
        """)
    )


@MEMES.route("/selkirk")
def selkirk():
    with open("okstupid/static/markdowns/selkirk.md", 'r') as fh:
        html = markdown.markdown(fh.read())

    return render_template(
        "main.html",
        title="Selkirk the cat",
        mkd_text=html
    )


@MEMES.route("/crustard")
def crustard():
    with open("okstupid/static/markdowns/crustard.md", 'r') as fh:
        html = markdown.markdown(fh.read())
    
    return render_template(
        "main.html",
        title="Crustard",
        mkd_text=html
    )
