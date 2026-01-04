import os
import re
import markdown
from ebooklib import epub
from bs4 import BeautifulSoup

def parse_summary(summary_path):
    chapters = []
    with open(summary_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # Find all markdown links [Title](file.md)
        matches = re.finditer(r'\[([^\]]+)\]\(([^)]+\.md)\)', content)
        for match in matches:
            title = match.group(1)
            file_path = match.group(2)
            chapters.append({'title': title, 'file': file_path})
    return chapters

def markdown_to_html(md_content):
    # Convert markdown to HTML
    html = markdown.markdown(md_content, extensions=['extra', 'toc', 'tables'])
    return html

def create_epub(chapters, output_path, title='儿童安全书', author='Contributors'):
    book = epub.EpubBook()

    # set metadata
    book.set_identifier('children-safety-book-id-2026')
    book.set_title(title)
    book.set_language('zh')
    book.add_author(author)

    epub_chapters = []
    
    # Add CSS
    style = 'body { font-family: sans-serif; } img { max-width: 100%; }'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    for i, chapter_info in enumerate(chapters):
        file_name = chapter_info['file']
        chapter_title = chapter_info['title']
        
        if not os.path.exists(file_name):
            print(f"Warning: {file_name} not found, skipping.")
            continue

        with open(file_name, 'r', encoding='utf-8') as f:
            md_content = f.read()

        html_content = markdown_to_html(md_content)
        
        # Process images
        soup = BeautifulSoup(html_content, 'lxml')
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and not src.startswith('http'):
                # Handle relative paths like assets/image.png
                img_path = os.path.join(os.path.dirname(file_name), src)
                if os.path.exists(img_path):
                    img_id = src.replace('/', '_').replace('.', '_')
                    # check if already added
                    found = False
                    for item in book.get_items_of_type(7): # 7 is image type in ebooklib
                        if item.file_name == src:
                            found = True
                            break
                    
                    if not found:
                        with open(img_path, 'rb') as img_f:
                            image_content = img_f.read()
                            # Guess media type
                            ext = os.path.splitext(src)[1].lower()
                            media_type = 'image/png' if ext == '.png' else 'image/jpeg'
                            epub_img = epub.EpubItem(uid=img_id, file_name=src, media_type=media_type, content=image_content)
                            book.add_item(epub_img)
        
        # Create chapter
        c = epub.EpubHtml(title=chapter_title, file_name=f'chap_{i}.xhtml', lang='zh')
        c.content = f'<h1>{chapter_title}</h1>' + str(soup.body.decode_contents())
        c.add_item(nav_css)
        book.add_item(c)
        epub_chapters.append(c)

    # define Table Of Contents
    book.toc = tuple(epub_chapters)

    # add default NCX and Nav pages
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # define spine
    book.spine = ['nav'] + epub_chapters

    # write to the file
    epub.write_epub(output_path, book, {})
    print(f"Successfully created EPUB: {output_path}")

if __name__ == "__main__":
    summary_file = 'SUMMARY.md'
    output_epub = 'er_tong_an_quan_shu.epub'
    
    if os.path.exists(summary_file):
        print(f"Parsing {summary_file}...")
        chapters = parse_summary(summary_file)
        print(f"Found {len(chapters)} chapters. Starting conversion...")
        create_epub(chapters, output_epub)
    else:
        print(f"Error: {summary_file} not found.")
