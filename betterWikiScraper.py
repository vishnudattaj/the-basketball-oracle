from tqdm import tqdm
import wikipediaapi
import time
import os

wiki_wiki = wikipediaapi.Wikipedia(
    user_agent='The Basketball Oracle (in progress) (vishnudattaj@gmail.com)', language='en'
)

visited = set()
BASKETBALL_KEYWORDS = [
    " basketball ", " nba ", " national basketball association "
]

def is_relevant(page):
    title = page.title.lower()
    text = page.text.lower()
    title_match = any(k in title for k in BASKETBALL_KEYWORDS)
    text_match = any(k in text for k in BASKETBALL_KEYWORDS)
    category_match = any("basketball" in c.lower() for c in page.categories.keys())
    return title_match or text_match or category_match

def save_links(page, depth, max_depth):
    if depth > max_depth or page.title in visited:
        return

    filename = f'betterNBA/{page.title}.md'
    if os.path.exists(filename):
        return

    visited.add(page.title)

    if page.exists() and is_relevant(page):
        try:
            with open(f'betterNBA/{page.title}.md', 'w', encoding="utf-8") as file:
                file.write(page.text)
        except:
            print(f"Invalid File: {page.title}")
            return

        link_titles = sorted(page.links.keys())
        if depth < max_depth:
            for title in tqdm(link_titles, desc=f"Crawling from {page.title} (depth {depth})", leave=False):
                save_links(wiki_wiki.page(title), depth=depth+1, max_depth=max_depth)


directory_path = "betterNBA"

start_page = wiki_wiki.page("National Basketball Association")
links = start_page.links
file_names = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
saved_titles = set(os.path.splitext(f)[0] for f in file_names)

for link in links.keys():
    page = wiki_wiki.page(link)
    if page.exists() and page.title not in saved_titles:
        save_links(page, depth=0, max_depth=2)
