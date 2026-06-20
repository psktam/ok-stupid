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


def generate_nav_buttons(entry: data.BlogEntry):
    nav_html = ""
    prev_entry = get_previous_blog_entry(entry)
    if prev_entry is not None:
        nav_html += get_prev_entry_button_html(prev_entry)

    next_entry = get_next_blog_entry(entry)
    if next_entry is not None:
        nav_html += get_next_entry_button_html(next_entry)

    return nav_html


def get_previous_blog_entry(current_entry: data.BlogEntry) -> data.BlogEntry | None:
    db = data.get_sql_connection()
    all_entries = data.load_blog_entries(db)
    for entry in sorted(all_entries, key=lambda e: (e.create_date, e.id))[::-1]:
        if (entry.create_date, entry.id) < (
            current_entry.create_date,
            current_entry.id,
        ):
            return entry
    return None


def get_next_blog_entry(current_entry: data.BlogEntry) -> data.BlogEntry | None:
    db = data.get_sql_connection()
    all_entries = data.load_blog_entries(db)
    for entry in sorted(all_entries, key=lambda e: (e.create_date, e.id)):
        if (entry.create_date, entry.id) >= (
            current_entry.create_date,
            current_entry.id,
        ):
            return entry
    return None
