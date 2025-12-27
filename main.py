# main.py
import argparse
import csv
import json
import config
import crawler
import extractor

def save_to_txt(data, filename='output.txt'):
    with open(filename, 'w', encoding='utf-8') as file:
        for post in data:
            file.write(json.dumps(post, ensure_ascii=False) + "\n")

def save_to_csv(data, filename='data.csv'):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Post', 'Link', 'Image', 'Comments', 'Shares'])
        for post in data:
            # Xử lý an toàn nếu key không tồn tại
            writer.writerow([
                post.get('Post', ''), 
                post.get('Link', ''), 
                post.get('Image', ''), 
                str(post.get('Comments', '')), 
                post.get('Shares', '')
            ])

def main():
    parser = argparse.ArgumentParser(description="Facebook Page Scraper Refactored")
    req_group = parser.add_argument_group("required arguments")
    req_group.add_argument('-page', '-p', help="The Facebook Public Page URL", required=True)
    req_group.add_argument('-len', '-l', help="Number of Posts to scrape", type=int, required=True)
    
    opt_group = parser.add_argument_group("optional arguments")
    opt_group.add_argument('-infinite', '-i', type=int, default=0, help="1 = infinite scroll")
    opt_group.add_argument('-usage', '-u', default="CSV", help="Output format: CSV, WT (text), or PS (print)")
    opt_group.add_argument('-comments', '-c', default="No", help="Scrape comments (y/n)")
    
    args = parser.parse_args()

    # 1. Load Credentials
    email, password = config.load_credentials()

    # 2. Config Flags
    infinite = (args.infinite == 1)
    scrape_comment = (args.comments == 'y')

    # 3. Run Crawler
    print("Starting crawler...")
    html_source, is_group = crawler.crawl_content(
        page_url=args.page,
        num_of_post=args.len,
        email=email,
        password=password,
        infinite_scroll=infinite,
        scrape_comment=scrape_comment
    )

    if not html_source:
        print("Failed to retrieve HTML source.")
        return

    # 4. Parse Data
    print("Parsing data...")
    data = extractor.parse_html_content(html_source, is_group=is_group)
    print(f"Extracted {len(data)} posts.")

    # 5. Save Output
    if args.usage == "WT":
        save_to_txt(data)
        print("Saved to output.txt")
    elif args.usage == "CSV":
        save_to_csv(data)
        print("Saved to data.csv")
    else:
        for post in data:
            print(post)

    print("Finished.")

if __name__ == "__main__":
    main()