from datetime import datetime
import os

import markdown


def load_blog_entries():
    blog_files = os.listdir("okstupid/blog")
    dates_to_files  ={
        datetime.strptime(os.path.splitext(fname)[0], "%m-%d-%Y"): fname
        for fname in blog_files
    }

    return dates_to_files


def generate_blog_nav_md():
    dates_to_files = load_blog_entries()
    text = ""

    for date in sorted(dates_to_files.keys()):
        link_url = f"/blog/{date.strftime('%m-%d-%Y')}"
        md_line = f"- [{date.strftime('%m-%d-%Y')}'s entry]({link_url})"
        text += md_line + "\n"
    return text


def get_prev_entry_button_html(prev_date: datetime) -> str:
    return f"""
    <a href="{get_blog_url(prev_date)}">
        <img src="/static/prev-button.png"
        onmouseover="this.src='/static/prev-button-active.png'"
        onmouseout="this.src='/static/prev-button.png'"
        />
    </a>
    """


def get_next_entry_button_html(next_date: datetime) -> str:
    return f"""
    <a href="{get_blog_url(next_date)}">
        <img src="/static/next-button.png"
        onmouseover="this.src='/static/next-button-active.png'"
        onmouseout="this.src='/static/next-button.png'"
        />
    </a>
    """


def get_blog_url(blog_date: datetime) -> str:
    return f"/blog/{blog_date.strftime('%m-%d-%Y')}"


def render_link(blog_date: datetime):
    return f"[{blog_date.strftime('%m-%d-%Y')}'s entry]({get_blog_url(blog_date)})"


def generate_nav_buttons(blog_date: datetime):
    nav_html = ""
    prev_date = get_previous_blog_entry(blog_date)
    if prev_date != None:
        nav_html += get_prev_entry_button_html(prev_date)
    
    next_date = get_next_blog_entry(blog_date)
    if next_date != None:
        nav_html += get_next_entry_button_html(next_date)
    
    return nav_html


def get_next_blog_entry(blog_date: datetime) -> datetime | None:
    all_dates = load_blog_entries()
    for date in sorted(all_dates):
        if date > blog_date:
            return date
    return None


def get_previous_blog_entry(blog_date: datetime) -> datetime | None:
    all_dates = load_blog_entries()
    for date in sorted(all_dates)[::-1]:
        if date < blog_date:
            return date
    return None