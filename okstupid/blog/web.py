from datetime import datetime

from . import data


def generate_blog_nav_md():
    db = data.get_sql_connection()
    blog_entries = data.load_blog_entries(db)
    sorted_blog_entries = sorted(blog_entries, key=lambda e: (e.create_date, e.id))

    text = ""
    for entry in sorted_blog_entries:
        link_url = f"/blog/entry-{entry.id}"
        md_line = (
            f"- [{entry.create_date.strftime('%m-%d-%Y')}: {entry.title}]({link_url})"
        )
        text += md_line + "\n"
    return text


def get_prev_entry_button_html(prev_entry: data.BlogEntry) -> str:
    return f"""
    <a href="/blog/entry-{prev_entry.id}">
        <img src="/static/prev-button.png"
        onmouseover="this.src='/static/prev-button-active.png'"
        onmouseout="this.src='/static/prev-button.png'"
        />
    </a>
    """


def get_next_entry_button_html(next_entry: data.BlogEntry) -> str:
    return f"""
    <a href="/blog/entry-{next_entry.id}">
        <img src="/static/next-button.png"
        onmouseover="this.src='/static/next-button-active.png'"
        onmouseout="this.src='/static/next-button.png'"
        />
    </a>
    """


def render_link(blog_date: datetime):
    return f"[{blog_date.strftime('%m-%d-%Y')}'s entry]({get_blog_url(blog_date)})"


def generate_nav_buttons(blog_date: datetime):
    nav_html = ""
    prev_entry = get_previous_blog_entry(blog_date)
    if prev_entry is not None:
        nav_html += get_prev_entry_button_html(prev_entry)

    next_entry = get_next_blog_entry(blog_date)
    if next_entry is not None:
        nav_html += get_next_entry_button_html(next_entry)

    return nav_html


def get_previous_blog_entry(blog_date: datetime) -> data.BlogEntry | None:
    db = data.get_sql_connection()
    all_entries = data.load_blog_entries(db)
    for entry in sorted(all_entries, key=lambda e: e.create_date)[::-1]:
        if entry.create_date < blog_date:
            return entry
    return None


def get_next_blog_entry(blog_date: datetime) -> data.BlogEntry | None:
    db = data.get_sql_connection()
    all_entries = data.load_blog_entries(db)
    for entry in sorted(all_entries, key=lambda e: e.create_date):
        if entry.create_date > blog_date:
            return entry
    return None
