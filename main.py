from scraper import extract
import argparse
import json
import csv

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Facebook Page Scraper")
    required_parser = parser.add_argument_group("required arguments")
    required_parser.add_argument('-page', '-p', help="The Facebook Public Page you want to scrape", required=True)
    required_parser.add_argument('-len', '-l', help="Number of Posts you want to scrape", type=int, required=True)
    optional_parser = parser.add_argument_group("optional arguments")
    optional_parser.add_argument('-infinite', '-i',
                                 help="Scroll until the end of the page (1 = infinite) (Default is 0)", type=int,
                                 default=0)
    optional_parser.add_argument('-usage', '-u', help="What to do with the data: "
                                                      "Print on Screen (PS), "
                                                      "Write to Text File (WT) (Default is WT)", default="CSV")

    optional_parser.add_argument('-comments', '-c', help="Scrape ALL Comments of Posts (y/n) (Default is n). When "
                                                         "enabled for pages where there are a lot of comments it can "
                                                         "take a while", default="No")
    args = parser.parse_args()

    infinite = False
    if args.infinite == 1:
        infinite = True

    scrape_comment = False
    if args.comments == 'y':
        scrape_comment = True

    postBigDict = extract(page=args.page, numOfPost=args.len, infinite_scroll=infinite, scrape_comment=scrape_comment)


    #TODO: rewrite parser
    if args.usage == "WT":
        with open('output.txt', 'w') as file:
            for post in postBigDict:
                file.write(json.dumps(post))  # use json load to recover

    elif args.usage == "CSV":
        with open('data.csv', 'w',) as csvfile:
           writer = csv.writer(csvfile)
           #writer.writerow(['Post', 'Link', 'Image', 'Comments', 'Reaction'])
           writer.writerow(['Post', 'Link', 'Image', 'Comments', 'Shares'])

           for post in postBigDict:
              writer.writerow([post['Post'], post['Link'],post['Image'], post['Comments'], post['Shares']])
              #writer.writerow([post['Post'], post['Link'],post['Image'], post['Comments'], post['Reaction']])

    else:
        for post in postBigDict:
            print(post)

    print("Finished")