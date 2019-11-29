from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from gmplot import gmplot
import requests
from bs4 import BeautifulSoup
import re
import plotly
import plotly.plotly as py
import plotly.graph_objs as go
import time


# =================== Shortest Path =================== #

def shortest_path(start, goal, edges):
    memo = []

    queue = [[start]]
    queue_cost = [distances[(start, goal)]]

    best_path = None
    best_score = float("inf")

    while min(queue_cost) < best_score:
        i = queue_cost.index(min(queue_cost))
        path = queue.pop(i)
        cost = queue_cost.pop(i)

        # print(path, cost)

        if path[-1] in memo:
            continue

        memo.append(path[-1])

        # print("^" * 50)

        if path[-1] == goal:
            if cost < best_score:
                best_path = path
                best_score = cost
            continue

        for edge in edges:
            if edge[0] == path[-1] and edge[1] not in path:
                new_path = path + [edge[1]]
                new_cost = cost - distances[(path[-1], goal)] + edges[edge]
                if edge[1] != goal:
                    new_cost += distances[(edge[1], goal)]
                queue.append(new_path)
                queue_cost.append(new_cost)

    return best_path


# =================== Initialization =================== #

print(">>> Connecting to 'geopy' ...\n")

try:
    geolocator = Nominatim(user_agent="Flight Search")
except:
    print(">>> Connection Failed!\nPlease Try Running the Code Later.\n")
    quit()

# =================== Get Cities' Location =================== #

print(">>> Loading Cities ...\n")

cities = ["London", "Delhi", "New York", "Singapore", "Shanghai", "Kuala Lumpur"]  # , "Paris", "Tokyo",
          # "Barcelona", "Moscow", "Dubai", "Rome", "Hong Kong", "Beijing", "Berlin", "Istanbul"]

locations = [geolocator.geocode(city) for city in cities]

print("\n".join(["{} ({} : {})".format(loc.address, loc.latitude, loc.longitude) for loc in locations]))

# =================== Center Map =================== #

center = ((min(locations, key=lambda loc: loc.latitude).latitude +
           max(locations, key=lambda loc: loc.latitude).latitude) / 2,
          (min(locations, key=lambda loc: loc.longitude).longitude +
           max(locations, key=lambda loc: loc.longitude).longitude) / 2)

gmap = gmplot.GoogleMapPlotter(* center, 3)

# =================== Mark Cities =================== #

for loc in locations[:-1]:

    gmap.marker(loc.latitude, loc.longitude, 'red')

gmap.marker(locations[-1].latitude, locations[-1].longitude, 'green')

# =================== Calculate distances =================== #

distances = {}
avg_dst = 0

for i, loc_1 in enumerate(locations):
    for j, loc_2 in enumerate(locations):
        if loc_1 != loc_2:
            loc_from = (loc_1.latitude, loc_1.longitude)
            loc_to = (loc_2.latitude, loc_2.longitude)
            distance = geodesic(loc_from, loc_to).km
            avg_dst += distance
            distances[(cities[i], cities[j])] = distance

avg_dst /= len(distances)

paths = {edge: dst for edge, dst in distances.items() if dst < avg_dst}
print("=" * 100)

# =================== Draw Airlines Between Cities =================== #

for city_1, city_2 in paths:
    loc_1 = locations[cities.index(city_1)]
    loc_2 = locations[cities.index(city_2)]
    gmap.plot([loc_1.latitude, loc_2.latitude], [loc_1.longitude, loc_2.longitude], '#748F87', edge_width=2)

destination = "New York"

flight_path = shortest_path("Kuala Lumpur", destination, paths)

flight_path_lats, flight_path_lons = zip(*[(locations[cities.index(city)].latitude,
                                            locations[cities.index(city)].longitude) for city in flight_path])

gmap.plot(flight_path_lats, flight_path_lons, '#FFD700', edge_width=5)

# print(distances)
# print("average distance = {}".format(avg_dst))
# print(len(paths))

print("The best root to {} is {}.\n".format(destination, " -> ".join(flight_path)))

# Draw
gmap.draw("my_map.html")


# =================== Getting News =================== #

print(">>> Collecting News ...\n")

def frequency(string, ignore=None, get_bothe=False):
    words = re.findall(r"[a-z]+", string.lower())
    result = {}
    rest = {}

    for word in words:
        if ignore and word in ignore:
            if get_bothe:
                rest[word] = rest.get(word, 0) + 1
            continue

        result[word] = result.get(word, 0) + 1

    if get_bothe:
        return result, rest

    return result


news = {"London": "https://www.theguardian.com/politics/2019/may/27/michael-gove-to-pledge-free-citizenship-for-3m-eu-nationals",
        "Shanghai": "http://tinyurl.com/y33yugz2",
        "New York": "https://www.nytimes.com/2019/05/27/us/politics/female-veterans-memorial.html?rref=politics&amp;module=Ribbon&amp;version=context&amp;region=Header&amp;action=click&amp;contentCollection=Politics&amp;pgtype=Multimedia",
        "Singapore": "http://tinyurl.com/y53tr8ej",
        "Delhi": "https://timesofindia.indiatimes.com/india/kamal-nath-govt-withdraws-mining-rights-of-panchayats/articleshow/69528076.cms"}

with open("stop_words", "r") as swf:
    sw = swf.read()

stop_words = sw.split("\n")

news_words = {}
news_freq = {}
news_sw_freq = {}

for city in news:
    resp = requests.get(news[city])
    html = resp.text
    soup = BeautifulSoup(html, features="html.parser")
    tags = soup.find_all(["p", "div"])

    text = " ".join(" ".join(repr(line) for line in tag.stripped_strings) for tag in tags)

    news_words[city] = re.findall(r"[a-z]+", text.lower())
    news_freq[city], news_sw_freq[city] = frequency(text, ignore=stop_words, get_bothe=True)

# print(news_freq)

# =================== (Word Count / Stop Words) Plot =================== #

print(">>> Processing News ...\n")

plotly.tools.set_credentials_file(username='Mox93', api_key='176VEammrMZGAG9BdBmM')

trace1 = go.Bar(x=list(news_freq.keys()),
                y=[sum(news_freq[city].values()) for city in news_freq.keys()],
                name='Word Count')

trace2 = go.Bar(x=list(news_sw_freq.keys()),
                y=[sum(news_sw_freq[city].values()) for city in news_sw_freq.keys()],
                name='Stop Words')

data = [trace1, trace2]
layout = go.Layout(barmode='stack')

fig = go.Figure(data=data, layout=layout)
py.plot(fig, filename='stacked-bar')


# =================== Evaluate Words =================== #

def eval_word(word, word_map):
    for t in word_map:
        if word in word_map[t]:
            return t
    return "Neutral"


type_files = ["Positive","Negative"]

word_types = {}

for file_name in type_files:
    with open(file_name, "r") as file:
        content = file.read()

    word_types[file_name] = re.findall(r"[a-z]+", content.lower())

news_eval = {}
news_eval_freq = {}

for city, words in news_words.items():
    news_eval[city] = [eval_word(word, word_types) for word in words]
    news_eval_freq[city] = frequency(" ".join(news_eval[city]))

# print(news_eval_freq)

# =================== (Negative / Positive) Plot =================== #

trace1 = go.Bar(x=list(news_eval_freq.keys()),
                y=[news_eval_freq[city]['positive'] for city in news_eval_freq.keys()],
                name='Positive', marker=dict(color='#557304'))

trace2 = go.Bar(x=list(news_eval_freq.keys()),
                y=[news_eval_freq[city]['neutral'] for city in news_eval_freq.keys()],
                name='Neutral', marker=dict(color='#4A90E2'))

trace3 = go.Bar(x=list(news_eval_freq.keys()),
                y=[news_eval_freq[city]['negative'] for city in news_eval_freq.keys()],
                name='Negative', marker=dict(color='#F34040'))

data = [trace1, trace2, trace3]
layout = go.Layout(barmode='stack')

fig_1 = go.Figure(data=data, layout=layout)
time.sleep(3)
py.plot(fig_1, filename='stacked-bar')

# =================== Sentiment Analysis =================== #

country_sentiment = {city: max(["positive", "negative"], key=lambda ev: news_eval_freq[city][ev])+" political situation"
                     for city in news_eval_freq}

print(country_sentiment)

# =================== Probability of Paths =================== #

print("\n>>> Finding all Paths ...\n")


def measure_len(path, edges):
    result = 0
    start = path[:-1]
    end = path[1:]
    for s, e in zip(start, end):
        result += edges[(s, e)]

    return result


def all_paths(start, goal, edges):
    queue = [(start,)]
    path_list = {}

    while queue:
        # print(len(queue))
        path = queue.pop()

        for edge in edges:
            if edge[0] == path[-1] and edge[1] not in path:
                new_path = path + (edge[1],)
                if edge[1] == goal:
                    dist = measure_len(new_path, edges)
                    path_list[new_path] = dist
                    # print(new_path)
                else:
                    queue.append(new_path)

    return path_list


avl_paths = all_paths("Kuala Lumpur", destination, paths)

net_dist = sum(list(avl_paths.values()))

net_prob = sum([1 - dist / net_dist for dist in avl_paths.values()])

avl_paths_porb = {path: (1 - dist / net_dist) / net_prob for path, dist in avl_paths.items()}

print("The Probability for Each Path is:\n{}".format("\n".join("{} {}".format(path, prob)
                                                               for path, prob in avl_paths_porb.items())))

