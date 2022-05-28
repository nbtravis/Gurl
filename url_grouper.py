import random
import re
from urllib.parse import urlparse
from collections import defaultdict

RE_ALL_CHARS = re.compile(r'^[a-zA-Z]*$')
RE_ALL_NUMS = re.compile(r'^[0-9]*$')
RE_ALL_CHARS_OR_NUMS = re.compile(r'^[a-zA-Z0-9]*$')

POST_KEYWORDS = {'/post/', '/posts/', '/blog/', '/news/', '/publications/', '/p/'}


def all_chars(s):
    return len(re.findall(RE_ALL_CHARS, s)) > 0

def all_nums(s):
    return len(re.findall(RE_ALL_NUMS, s)) > 0

def all_chars_or_nums(s):
    return len(re.findall(RE_ALL_CHARS_OR_NUMS, s)) > 0

class ParsedSection:
  """One section of a URL."""
  def __init__(self, section):
    self.section = section

    self.all_chars = all_chars(section)
    self.all_nums = all_nums(section)
    self.all_chars_or_nums = all_chars_or_nums(section)

    self.punc = []
    if '.' in section: self.punc.append('.')
    if '-' in section: self.punc.append('-')
    if '_' in section: self.punc.append('_')

    without_punc = section.replace('.', '').replace('-', '').replace('_', '')
    self.without_punc_all_chars_or_nums = all_chars_or_nums(without_punc)
    
class ParsedUrl:
  """One parsed URL (i.e. split into its domain and sections)."""
  def __init__(self, url, root_url):
    self.url = url
    parsed = urlparse(self.url)
    self.domain = parsed.netloc
    # Note: make sure to strip the trailing slash here...
    section_strs = parsed.path.rstrip('/').split('/')[1:]
    self.sections = [ParsedSection(s) for s in section_strs]

    # Look at the shared prefix between the root_url and url.
    self.root_url_shared_prefix_len = self.shared_prefix_length(url, root_url)

  def shared_prefix_length(self, u1, u2):
    """Get length of the shared prefix between 2 URLs.
    
    Example:
      u1 = 'espn.com/nba/news/archive'
      u2 = 'www.espn.com/nba/story/this-team-wins-championship'
  
      The shared prefix is 'espn.com/nba/'.
  
    This is useful because in the case that a URL shares a prefix with the 
    root URL, then likely its group should share that prefix. For example, in 
    the above case some u3 = 'espn.com/nfl/story/this-nfl-team-wins' should go
    in a different group (if u1 was root URL).
    """
    def strip(u):
      return u.replace('https://', '').replace('http://', '').replace('www.', '')
  
    u1, u2 = strip(u1), strip(u2)
    min_len = min(len(u1), len(u2))
    for i in range(min_len):
      if i >= len(u1) or i >= len(u2):
        break
      if u1[i] != u2[i]:
        break
  
    return i  

class Group:
  """A group of URLs with a similar URL pattern."""
  def __init__(self, url, dists):
    self.id = random.randint(0, 100000000)
    self.group = [url]
    self.within_group_dist = 0
    self.dists = dists

  def cache_key(self):
    return '{}_{}'.format(self.id, self.length())

  def length(self):
    return len(self.group)

  def is_mergeable(self, other_group, dist):
    max_dist = None
    if self.length() == 1 and other_group.length() == 1:
      # Both singletons.
      max_dist = 2
    elif self.length() == 1 or other_group.length() == 1:
      # One is a singleton.
      max_dist = max(self.within_group_dist, other_group.within_group_dist) + 1
    else:
      # Neither are singletons.
      max_dist = min(self.within_group_dist, other_group.within_group_dist) + 1
    return dist <= max_dist

  def merge(self, other_group):
    self.group.extend(other_group.group)
    self.within_group_dist = self.distance(self)

  def distance(self, other_group):
    max_dist = -1
    for u1 in self.group:
      for u2 in other_group.group:
        dist = self.dists[u1][u2]
        max_dist = max(max_dist, dist)
    return max_dist

class UrlGrouper:
  """A class that groups URLs by similar URL pattern."""
  def __init__(self, urls, root_url):
    # Parse URLs ahead of time to not have to repeat work.
    self.urls = [ParsedUrl(u, root_url) for u in urls]

  def group(self):
    # Get distance between each pair of urls.
    dists = defaultdict(lambda: defaultdict(int))
    for i in range(len(self.urls)):
      for j in range(i + 1, len(self.urls)):
        u1, u2 = self.urls[i], self.urls[j]
        dists[u1.url][u2.url] = self.distance(u1, u2)
        dists[u2.url][u1.url] = dists[u1.url][u2.url]
    
    groups = [Group(u.url, dists) for u in self.urls]
    dist_cache = defaultdict(lambda: {})

    while True:
      group_dists = []
      for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
          g1, g2 = groups[i], groups[j]
          k1, k2 = g1.cache_key(), g2.cache_key()
          dist = dist_cache[k1].get(k2, None)
          if dist == None:
            dist = g1.distance(g2)
            dist_cache[k1][k2] = dist
            dist_cache[k2][k1] = dist
          group_dists.append((dist, i, j))

      group_dists.sort()
      merged = False
      indices_to_delete = set()
      for (dist, i, j) in group_dists:
        if i in indices_to_delete or j in indices_to_delete:
          continue
        g1, g2 = groups[i], groups[j]
        if g1.is_mergeable(g2, dist):
          g1.merge(g2)
          indices_to_delete.add(j)
          merged = True

      if not merged:
        break

      new_groups = []
      for i in range(len(groups)):
        if i in indices_to_delete:
          continue
        new_groups.append(groups[i])
      groups = new_groups

    return [g.group for g in groups]

  def distance(self, url1, url2):
    # Check the domain first, off domain are certainly far away
    if (url1.domain != url2.domain):
        return 1000
    
    # Check the lengths. Different Lengths are certainly far away
    if len(url1.sections) != len(url2.sections):
        return 1000

    dist = 0
    for i in range(len(url1.sections)):
      section1, section2 = url1.sections[i], url2.sections[i]
      dist += self.section_distance(section1, section2)

    # Compare whether each URL's prefix is shared with the input URL.
    if url1.root_url_shared_prefix_len != url2.root_url_shared_prefix_len:
      dist += 2

    return dist

  def section_distance(self, section1, section2):
    if section1.section == section2.section:
      return 0
    elif section1.all_nums and section2.all_nums:
      return 0
    elif section1.all_chars and section2.all_chars:
      kw1, kw2 = '/{}/'.format(section1.section), '/{}/'.format(section2.section)
      if ((kw1 in POST_KEYWORDS and kw2 not in POST_KEYWORDS) or 
          (kw2 in POST_KEYWORDS and kw1 not in POST_KEYWORDS)):
        return 4
      else:
        return 1
    elif section1.all_chars_or_nums and section2.all_chars_or_nums:
      return 1
    else:
      punc1, punc2 = section1.punc, section2.punc
      if punc1 == punc2 and section1.without_punc_all_chars_or_nums and section2.without_punc_all_chars_or_nums:
        return 0
      elif punc1 == punc2:
        return 1
      elif ('.' in punc1 and '.' not in punc2) or ('.' in punc2 and '.' not in punc1):
        return 4
      elif ('-' in punc1 and '_' in punc2) or ('-' in punc2 and '_' in punc1):
        return 2
      elif section1.without_punc_all_chars_or_nums and section2.without_punc_all_chars_or_nums:
        return 1

      return 4
