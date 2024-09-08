import requests
import datetime
import pytumblr
import os
import argparse
import sys
from dotenv import load_dotenv
from PIL import Image
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn
)

# Custom Progress Bar
progress_bar = Progress(
    TextColumn("[blue]Posting..."),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    MofNCompleteColumn(),
    TextColumn("•"),
    TimeElapsedColumn(),
    TextColumn("•"),
    TimeRemainingColumn(),
)

total_iterations = 5

# Environment Variables
load_dotenv()
TUMBLR_CONSUMER_KEY = os.getenv("TUMBLR_CONSUMER_KEY")
TUMBLR_CONSUMER_SECRET_KEY = os.getenv("TUMBLR_CONSUMER_SECRET_KEY")
TUMBLR_OAUTH_TOKEN = os.getenv("TUMBLR_OAUTH_TOKEN")
TUMBLR_OAUTH_SECRET = os.getenv("TUMBLR_OAUTH_SECRET")
TMDB_API = os.getenv("TMDB_API")
BLOG_NAME = os.getenv("BLOG_NAME")

API_URL = "https://api.themoviedb.org/3/"
IMAGE_URL = 'https://image.tmdb.org/t/p/original'

IMAGE_HEIGHT = 700
IMAGE_WIDTH = 500

current_year = datetime.datetime.now().year

parser = argparse.ArgumentParser(description="Publish post on Tumblr using tmdb")
parser.add_argument("IMDB_ID", action="store", help="Insert IMDb ID. Format: tt[ID]")
parser.add_argument("-f", action="store_true", dest="fav", default=False, help="Tag movie as favourite")
args = parser.parse_args()
fav = args.fav
IMDB_ID = args.IMDB_ID

# Tumblr Client
client = pytumblr.TumblrRestClient(
    TUMBLR_CONSUMER_KEY,
    TUMBLR_CONSUMER_SECRET_KEY,
    TUMBLR_OAUTH_TOKEN,
    TUMBLR_OAUTH_SECRET
)

def request_movie():
    try:
        r = requests.get(API_URL + "find/" + IMDB_ID + "?api_key=" + TMDB_API + "&external_source=imdb_id")
        r.raise_for_status()
        json_list = r.json().get("movie_results", [])
        if not json_list:
            raise ValueError("No movie found for the given IMDb ID.")
        
        movie_info = json_list[0]
        tags_dict = {
            "id": movie_info.get("id"),
            "title": movie_info.get("title"),
            "original_title": movie_info.get("original_title"),
            "poster_path": movie_info.get("poster_path")
        }
        if fav:
            tags_dict["fav"] = "Fav"
        progress.update(task, advance=1)
        return tags_dict
    except requests.RequestException as e:
        print(f"HTTP error occurred: {e}")
        sys.exit(1)
    except ValueError as e:
        print(e)
        sys.exit(2)

def request_image_and_resize(movie_info):
    try:
        r = requests.get(IMAGE_URL + movie_info["poster_path"])
        r.raise_for_status()
        filename = movie_info["poster_path"].split('/')[-1]
        with open(filename, 'wb') as file:
            file.write(r.content)
        
        # Resizing the image
        image = Image.open(filename)
        new_image = image.resize((IMAGE_WIDTH, IMAGE_HEIGHT))
        new_image.save(filename)
        progress.update(task, advance=1)
        return filename
    except requests.RequestException as e:
        print(f"HTTP error occurred: {e}")
        sys.exit(1)
    except IOError as e:
        print(f"Error handling image: {e}")
        sys.exit(1)

def request_director(movie_id):
    try:
        r = requests.get(API_URL + "movie/" + str(movie_id) + "/credits?api_key=" + TMDB_API)
        r.raise_for_status()
        crew_list = r.json().get("crew", [])
        directors = [person["name"] for person in crew_list if person["job"] == "Director"]
        progress.update(task, advance=1)
        return directors
    except requests.RequestException as e:
        print(f"HTTP error occurred: {e}")
        sys.exit(1)

def create_tags(movie_info, directors):
    tag_list = [
        movie_info.get("title"),
        movie_info.get("original_title"),
        directors[0] if directors else None,
        str(current_year)
    ]
    if fav:
        tag_list.append("Fav")
    progress.update(task, advance=1)
    return [tag for tag in tag_list if tag]

def post_tumblr():
    movie_info = request_movie()
    image_path = request_image_and_resize(movie_info)
    directors = request_director(movie_info["id"])
    tags = create_tags(movie_info, directors)
    
    client.create_photo(BLOG_NAME, state="published", caption=movie_info.get("title"), tags=tags, data=image_path)
    os.remove(image_path)
    progress.update(task, advance=1)
    
    
    posts_url_dict = client.posts(BLOG_NAME)
    post_url = posts_url_dict["posts"][0].get("post_url")
    return movie_info.get("title"), post_url

if __name__ == "__main__":
    with progress_bar as progress:
        task = progress.add_task("[green]Posting...", total=total_iterations)
        movie_title, movie_url = post_tumblr()
    # Print the movie name and link after the progress bar ends
    print(f"{movie_title}")
    print(f"{movie_url}")
