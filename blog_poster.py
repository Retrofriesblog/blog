import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
from datetime import datetime
import re

# ── config ──────────────────────────────────────────────────────────────────
BLOG_DIR = r"C:\Users\blexe\OneDrive\Desktop\blog"
POSTS_DIR = os.path.join(BLOG_DIR, "posts")
INDEX_PATH = os.path.join(BLOG_DIR, "index.html")
TEMPLATE_PATH = os.path.join(BLOG_DIR, "template.html")
# ────────────────────────────────────────────────────────────────────────────


def slugify(title):
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug.strip())
    return slug


def body_to_html(raw):
    lines = raw.split("\n")
    html_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            html_lines.append(stripped + "<br>")
        else:
            html_lines.append("<br>")
    return "\n            ".join(html_lines)


def build_dropdown_html(entries):
    tree = {}
    for year, month, title, url in entries:
        tree.setdefault(year, {}).setdefault(month, []).append((title, url))

    lines = []
    for year in sorted(tree.keys(), reverse=True):
        lines.append('<div class="dropdown-year">')
        lines.append('  <span>' + year + ' ▾</span>')
        lines.append('  <div class="submenu">')
        for month in sorted(tree[year].keys(), key=lambda m: datetime.strptime(m, "%B").month, reverse=True):
            lines.append('    <div class="dropdown-month">')
            lines.append('      <span>' + month + ' ▾</span>')
            lines.append('      <div class="submenu">')
            for title, url in tree[year][month]:
                lines.append('        <a href="' + url + '">' + title + '</a>')
            lines.append('      </div>')
            lines.append('    </div>')
        lines.append('  </div>')
        lines.append('</div>')

    return "\n                        ".join(lines)


def parse_entries_from_posts():
    entries = []
    if not os.path.exists(POSTS_DIR):
        return entries
    for fname in os.listdir(POSTS_DIR):
        if not fname.endswith(".html"):
            continue
        fpath = os.path.join(POSTS_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        title_match = re.search(r"<h2>(.*?)</h2>", content)
        date_match = re.search(r'<p class="date">(.*?)</p>', content)
        if not title_match or not date_match:
            continue
        title = title_match.group(1)
        date_str = date_match.group(1)
        try:
            date_obj = datetime.strptime(date_str, "%m/%d/%Y")
        except ValueError:
            continue
        year = str(date_obj.year)
        month = date_obj.strftime("%B")
        url = f"/blog/posts/{fname}"
        entries.append((year, month, title, url, date_obj))
    entries.sort(key=lambda e: e[4], reverse=True)
    return [(y, m, t, u) for y, m, t, u, _ in entries]


def get_all_html_files():
    files = [INDEX_PATH]
    if os.path.exists(POSTS_DIR):
        for f in os.listdir(POSTS_DIR):
            if f.endswith(".html"):
                files.append(os.path.join(POSTS_DIR, f))
    return files


def update_dropdown_in_file(filepath, dropdown_html):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    new_block = (
        "<!-- DROPDOWN_ENTRIES -->\n                        "
        + dropdown_html
        + "\n                        <!-- END_DROPDOWN_ENTRIES -->"
    )

    content = re.sub(
        r"<!-- DROPDOWN_ENTRIES -->.*?<!-- END_DROPDOWN_ENTRIES -->",
        new_block,
        content,
        flags=re.DOTALL
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def update_latest_post_on_index(title, date_str, body_html, post_url):
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    latest_block = (
        "<!-- LATEST_POST -->\n"
        f'            <h2><a href="{post_url}">{title}</a></h2>\n'
        "            <hr>\n"
        f'            <p class="date">{date_str}</p>\n'
        "            <br>\n"
        f"            {body_html}\n"
        "            <!-- END_LATEST_POST -->"
    )

    content = re.sub(
        r"<!-- LATEST_POST -->.*?<!-- END_LATEST_POST -->",
        latest_block,
        content,
        flags=re.DOTALL
    )

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def git_push(commit_message):
    cmds = [
        ["git", "-C", BLOG_DIR, "add", "."],
        ["git", "-C", BLOG_DIR, "commit", "-m", commit_message],
        ["git", "-C", BLOG_DIR, "push"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Git command failed:\n{' '.join(cmd)}\n\n{result.stderr}")


# ── GUI ──────────────────────────────────────────────────────────────────────

class BlogPoster(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Blog Poster")
        self.geometry("700x600")
        self.configure(bg="#1a1a2e")
        self.resizable(True, True)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", background="#1a1a2e", foreground="white", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("TEntry", fieldbackground="#16213e", foreground="white", insertcolor="white")

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 16, "pady": 6}

        ttk.Label(self, text="Post Title").pack(anchor="w", **pad)
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(self, textvariable=self.title_var, width=60)
        self.title_entry.pack(fill="x", **pad)

        ttk.Label(self, text="Date").pack(anchor="w", **pad)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%m/%d/%Y"))
        self.date_entry = ttk.Entry(self, textvariable=self.date_var, width=20)
        self.date_entry.pack(anchor="w", **pad)

        ttk.Label(self, text="Output filename (inside posts/)").pack(anchor="w", **pad)
        self.filepath_var = tk.StringVar()
        self.title_var.trace_add("write", self._update_filepath)
        self.date_var.trace_add("write", self._update_filepath)
        self.filepath_entry = ttk.Entry(self, textvariable=self.filepath_var, width=60)
        self.filepath_entry.pack(fill="x", **pad)

        ttk.Label(self, text="Post Body  (Enter = new line)").pack(anchor="w", **pad)
        self.body_text = tk.Text(
            self,
            height=16,
            bg="#16213e",
            fg="white",
            insertbackground="white",
            font=("Segoe UI", 10),
            wrap="word",
            relief="flat",
            padx=8,
            pady=8
        )
        self.body_text.pack(fill="both", expand=True, padx=16, pady=4)

        upload_btn = tk.Button(
            self,
            text="⬆  Upload Post",
            command=self._upload,
            bg="#0f3460",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            padx=16,
            pady=10,
            cursor="hand2",
            activebackground="#e94560",
            activeforeground="white"
        )
        upload_btn.pack(pady=12)

        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(self, textvariable=self.status_var)
        self.status_label.pack()

    def _update_filepath(self, *_):
        title = self.title_var.get()
        date_str = self.date_var.get()
        try:
            date_obj = datetime.strptime(date_str, "%m/%d/%Y")
            date_slug = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            date_slug = "0000-00-00"
        slug = slugify(title) or "post"
        self.filepath_var.set(f"{date_slug}-{slug}.html")

    def _upload(self):
        title = self.title_var.get().strip()
        date_str = self.date_var.get().strip()
        filename = self.filepath_var.get().strip()
        body_raw = self.body_text.get("1.0", "end").strip()

        if not title:
            messagebox.showerror("Missing title", "Please enter a post title.")
            return
        if not body_raw:
            messagebox.showerror("Missing body", "Post body is empty.")
            return
        try:
            date_obj = datetime.strptime(date_str, "%m/%d/%Y")
        except ValueError:
            messagebox.showerror("Bad date", "Date must be in MM/DD/YYYY format.")
            return

        os.makedirs(POSTS_DIR, exist_ok=True)

        post_path = os.path.join(POSTS_DIR, filename)
        post_url = f"/blog/posts/{filename}"

        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            template = f.read()

        body_html = body_to_html(body_raw)

        post_html = template.replace("{{TITLE}}", title)
        post_html = post_html.replace("{{DATE}}", date_str)
        post_html = post_html.replace("{{BODY}}", body_html)

        with open(post_path, "w", encoding="utf-8") as f:
            f.write(post_html)

        # update dropdown in ALL html files
        entries = parse_entries_from_posts()
        dropdown_html = build_dropdown_html(entries)
        for html_file in get_all_html_files():
            update_dropdown_in_file(html_file, dropdown_html)

        # update index latest post
        update_latest_post_on_index(title, date_str, body_html, post_url)

        self.status_var.set("Pushing to GitHub...")
        self.update()
        try:
            git_push(f"New post: {title}")
            self.status_var.set(f"✓ Posted: {title}")
            self.title_var.set("")
            self.body_text.delete("1.0", "end")
            self.date_var.set(datetime.now().strftime("%m/%d/%Y"))
        except RuntimeError as e:
            messagebox.showerror("Git error", str(e))
            self.status_var.set("Git push failed. Check error.")


if __name__ == "__main__":
    app = BlogPoster()
    app.mainloop()
