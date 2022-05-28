from url_grouper import UrlGrouper


EXAMPLES = [
    ('http://www.visualcapitalist.com', 'examples/visualcapitalist_dot_com.txt')
]


if __name__ == '__main__':
    example = EXAMPLES[0]

    # Get URLs from an example website.
    filename = example[1]
    urls = []
    with open(filename, 'r') as f:
        for line in f.readlines():
            urls.append(line.strip().rstrip())
    
    # Group URLs.
    root_url = example[0]
    groups = UrlGrouper(urls, root_url).group()
    print('num groups: {}'.format(len(groups)))
    for i, group in enumerate(groups):
        print('group {}:'.format(i + 1))
        for url in group:
            print('  * {}'.format(url))

