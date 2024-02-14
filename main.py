import requests, datetime, pytumblr, os, argparse, sys
from PIL import Image
from rich.progress import (BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn)
 
 ##Custom Progress Bar##
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

total_iterations = 13

TUMBLR_CONSUMER_KEY = os.getenv("TUMBLR_CONSUMER_KEY")
TUMBLR_CONSUMER_SECRET_KEY = os.getenv("TUMBLR_CONSUMER_SECRET_KEY")
TUMBLR_OAUTH_TOKEN = os.getenv("TUMBLR_OAUTH_TOKEN")
TUMBLR_OAUTH_SECRET = os.getenv("TUMBLR_OAUTH_SECRET")

TMDB_API = os.getenv("TMDB_API")
API_URL = "https://api.themoviedb.org/3/"
IMAGE_URL = 'https://image.tmdb.org/t/p/original'

BLOG_NAME = os.getenv("BLOG_NAME")

IMAGE_HEIGHT = 500
IMAGE_WIDTH = 700

current_year = datetime.datetime.now()
parser = argparse.ArgumentParser(description="Publish post on Tumblr using tmdb")
parser.add_argument("IMDB_ID", action="store", help="Insert iMBd ID. Format: tt[ID]")
parser.add_argument("-f", action="store_true",dest="fav",default=False, help="Tag movie as favourite")
args = parser.parse_args()
fav = args.fav

###Tumblr###

client = pytumblr.TumblrRestClient(TUMBLR_CONSUMER_KEY,
                                   TUMBLR_CONSUMER_SECRET_KEY,
                                   TUMBLR_OAUTH_TOKEN,
                                   TUMBLR_OAUTH_SECRET)


def request_movie():    
    r = requests.get(API_URL + "find/" + IMDB_ID + "?api_key=" + TMDB_API + "&external_source=imdb_id")
    json_list = r.json()
    json_list = json_list.get("movie_results")

    tags_dict = {}
    try:
        for k, v in json_list[0].items():
            if k == "id":
                tags_dict.update({k:v})
            elif k == "title":
                tags_dict.update({k:v})
            elif k == "original_title":
                tags_dict.update({k:v})
            elif k == "poster_path":
                tags_dict.update({k:v})
        if args.fav == True:
            tags_dict.update({"fav": "Fav"})
    except IndexError:
        print("Wrong ID. Try again") 
        sys.exit(2)
    
    progress.update(task, advance=1)
    return(tags_dict)

def request_imagen_and_resizing():
    r = requests.get(IMAGE_URL + request_movie().get("poster_path"))
    filename = request_movie().get("poster_path").split('/')[-1]
    file = open(filename, 'wb')
    file.write(r.content)
    file.close()
    path = os.getcwd()
    fullpath = (path + '/'+ filename)
    #resizing
    image = Image.open(fullpath)
    new_image = image.resize((IMAGE_HEIGHT,IMAGE_WIDTH))
    new_image.save(fullpath)
    
    progress.update(task, advance=1)
    return(fullpath)

def request_director():
    r = requests.get(API_URL + "movie/" + str(request_movie().get("id")) + "/credits?api_key=" + TMDB_API)
    json_list_credits = r.json()
    json_list_credits = json_list_credits.get("crew")
    director_list = []
    for i in json_list_credits:
        if i['job'] == 'Director':
            director_list.append((i['name']))
    
    progress.update(task, advance=1)
    return director_list    

def tags():
    tag_list = []
    for k, v in request_movie().items():
        if k == "title":
            tag_list.append(v)
        elif k == "fav":
            tag_list.append(v)
        elif k == "original_title":
            tag_list.append(v)
    tag_list.append(request_director()[0])
    tag_list.append(str(current_year.year))
    
    progress.update(task, advance=1)
    return(tag_list)

def post_tumblr():
    client.create_photo(BLOG_NAME, state="published",caption=request_movie().get("title"), tags=tags(), data=request_imagen_and_resizing())
    os.remove(request_imagen_and_resizing())
    progress.update(task, advance=1)
    print(request_movie().get("title"))
    #Print the URL of you latest post
    posts_url_dict = client.posts(BLOG_NAME)  
    post_url = (posts_url_dict["posts"][0])
    print(post_url["post_url"])
        
    
if __name__ == "__main__":
    with progress_bar as progress:
        task = progress.add_task("[green]Posting...", total=total_iterations)
        IMDB_ID = args.IMDB_ID        
        post_tumblr()