import requests, datetime, pytumblr, os, argparse, sys, re, click
from tqdm import tqdm
from PIL import Image

parser = argparse.ArgumentParser(description="Publish post on Tumblr using tmdb")
parser.add_argument("IMDB_ID", action="store", help="Insert iMBd ID. Format: tt[ID]")
args = parser.parse_args()

class TheMovieDBApi:
    API_URL = "https://api.themoviedb.org/3/"
    
    def __init__(self, api_key):
        self.api_key = api_key

    def find(self, imdb_id):
        url = "{}find/{}?api_key={}&external_source=imdb_id".format(
            self.API_URL,
            imdb_id,
            self.api_key
        )
        response = requests.get(url)
        return response.json()

    def credits(self, movie_id):
        url = "{}movie/{}/credits?api_key={}".format(
            self.API_URL,
            movie_id,
            self.api_key
        )
        response = requests.get(url)
        return response.json()

class App:
    def __init__(
        self, 
        api_key, 
        blog_name,
        tumblr_consumer_key, 
        tumblr_consumer_secret_key, 
        tumblr_oauth_token,
        tumblr_oauth_secret
    ):
        self.theMovieDBApi = TheMovieDBApi(api_key)
        self.blog_name = blog_name
        self.tumblr_consumer_key = tumblr_consumer_key
        self.tumblr_consumer_secret_key = tumblr_consumer_secret_key
        self.tumblr_oauth_token = tumblr_oauth_token
        self.tumblr_oauth_secret = tumblr_oauth_secret

    def download(self, url, fname):
        resp = requests.get(url, stream=True)
        total = int(resp.headers.get('content-length', 0))
        with open(fname, 'wb') as file, tqdm(
            total=total,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in resp.iter_content(chunk_size=1024):
                size = file.write(data)
                bar.update(size)

    def download_poster(self, movie):
        filename = "{}{}".format(
            re.sub('[^a-zA-Z0-9\.]', '_', movie["title"]),
            os.path.splitext(movie["poster_path"])[1]
        ).lower()
        url = "https://image.tmdb.org/t/p/original{}".format(
            movie["poster_path"]
        )
        self.download(url, filename)
        return "{}/{}".format(os.getcwd(), filename)

    def resize_image(self, path_image):
        image = Image.open(path_image)
        new_image = image.resize((500,700))
        new_image.save(path_image)

    def filterTags(self, movie):
        keys = ["title", "original_title", "fav"]
        jobs = ["Director"]

        tags_list = list(set([
            movie[key] for key in movie
            if key in keys
        ]))
    
        credits = self.theMovieDBApi.credits(movie["id"])
        for crew in credits["crew"]:
            if crew["job"] in jobs:
                tags_list.append(crew["name"])

        tags_list.append(str(datetime.datetime.now().year))
        return tags_list
    
    def post_tumblr(self, imdb_id):
        try:
            movie = self.theMovieDBApi.find(imdb_id)["movie_results"][0]
            title = movie["title"]
            tags = self.filterTags(movie)
            print("Title: {}".format(title))
            print("Tags:")
            for tag in tags:
                print("  #{}".format(tag))
            print("")
            print("Download Poster:")
            image_path = self.download_poster(movie)
            print("Resize Poster:")
            self.resize_image(image_path)
            print("")
            if click.confirm('All ready to publish?', default=True):
                try:
                    client = pytumblr.TumblrRestClient(
                        self.tumblr_consumer_key,
                        self.tumblr_consumer_secret_key,
                        self.tumblr_oauth_token,
                        self.tumblr_oauth_secret
                    )
                    client.create_photo(
                        self.blog_name, 
                        state="published",
                        caption=title, 
                        tags=tags, 
                        data=image_path
                    )
                    posts_url_dict = client.posts(blog_name)  
                    post_url = posts_url_dict["posts"][0]["post_url"]
                    print(post_url)
                except:
                    print("An error occurred when interacting with tumblr :(")
            os.remove(image_path)
        except:
            print("An unexpected error occurred :(")

if __name__ == "__main__":
    app = App(
        os.getenv("TMDB_API"), 
        os.getenv("BLOG_NAME"),
        os.getenv("TUMBLR_CONSUMER_KEY"),
        os.getenv("TUMBLR_CONSUMER_SECRET_KEY"),
        os.getenv("TUMBLR_OAUTH_TOKEN"),
        os.getenv("TUMBLR_OAUTH_SECRET")
    )
    app.post_tumblr(args.IMDB_ID)