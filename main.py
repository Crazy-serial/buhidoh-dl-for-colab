from locale import strcoll
import requests, os, glob, re
from bs4 import BeautifulSoup
from natsort import natsorted
while True:
    try:
        import img2pdf
    except:
        os.system("pip install img2pdf")
    else:
        break


class Scraper:
    def __init__(self):
        self.header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36"}
        self.artworks_urls = []
        self.artwork_imgs = []
        self.artwork_title = ""
        self.artwork_id = 0
        self.artwork_tags = []

    def get_artworks(self, max_urls:int=14, search_query:str=""):
        artworks_urls = []
        leave = False
        page = 1
        while True:
            if leave:
                break
            if search_query != "":
                url = f"http://buhidoh.net/page/{page}?s={search_query}"
            elif search_query == "":
                url = f"http://buhidoh.net/page/{page}"
            print(url)

            response = requests.get(url, headers=self.header)
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, "html.parser")
            for i in soup.find_all("a"):
                href = i.get("href")
                if (
                    href.startswith("http")
                    and "http://buhidoh.net/blog-entry-6146.html" != href
                    and "http://buhidoh.net/blog-entry-" in href
                    and i.get("target") != "_self"
                    and not "#" in href
                    and not "date" in href
                ):
                    if not href in artworks_urls:
                        print(href)
                        artworks_urls.append(href)
                    if len(artworks_urls) == max_urls:
                        leave = True
                        break
            page += 1
        self.artworks_urls = artworks_urls
        return self.artworks_urls

    def get_about_artworks(self, url):
        artwork_tags = []
        artwork_imgs = []
        response = requests.get(url, headers=self.header)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        self.artwork_title = soup.find("title").text
        self.artwork_id = int(url.replace("http://buhidoh.net/blog-entry-", "").replace(".html", ""))
        for i in soup.find_all("a"):
            rel = i.get("rel")
            if rel != None:
                if rel[0] == "tag":
                    artwork_tags.append(i.text)
        self.artwork_tags = artwork_tags
        for i in soup.find_all("img"):
            if "file.buhidoh.net" in str(i) and "setting" not in str(i):
                img_url = i.get("src")
                artwork_imgs.append(img_url)
        self.artwork_imgs = artwork_imgs
        return artwork_imgs

    def download_image(self, urls, output_path, overwrite=False):
        file_url = {}
        imgs = len(urls) - 1
        if not output_path.endswith("/"):
            output_path += "/"
        if not os.path.isdir(output_path):
            os.makedirs(output_path)
        for i in range(len(urls)):
            file_name = output_path + urls[i].split("/")[-1]
            file_url[file_name] = urls[i]
            if not os.path.isfile(file_name):
                urlData = requests.get(urls[i], headers=self.header).content
                with open(file_name, mode="wb") as f:
                    f.write(urlData)
            pro_bar = ("=" * i) + (" " * (imgs - i))
            print("\r[{0}] {1}/{2}".format(pro_bar, i, imgs), end="")
        print(" Complete !")
        return output_path


class Tool:
    def __init__(self):
        self.glob = glob
        self.img2pdf = img2pdf
        self.os = os

    def image_to_pdf(self, image_directory, save_pdf, overwrite=False):
        if not overwrite:
            if self.os.path.isfile(save_pdf):
                print("pdf exists")
                return False
        output_dir = os.path.dirname(save_pdf)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        image_list = natsorted(self.glob.glob(image_directory + "/*"))
        try:
            pdf = self.img2pdf.convert(image_list)
        except:
            print(f"ConvertError: {save_pdf}")
            return False
        with open(save_pdf, "wb") as f:
            f.write(pdf)
        return True
    
    def pdf_name_gen(self, id, tags):
        pdf_name = str(id)
        for i in tags:
          if "（" in i:
            r = ""
            for r in re.findall(r'\（.*\）', i):
              tag = i.replace(r, "")
          else:
            tag = i
          pdf_name += "_" + tag
          pdf_name = pdf_name.replace("/", "")
        return pdf_name

    def save_downloaded_url(self, url):
        txt_file = "downloaded.txt"
        try:
            with open(txt_file, "r") as f:
                lines = f.read().split()
        except:
            pass
        else:
            if not url in lines:
                with open(txt_file, "a") as f:
                    f.write(url+"\n")
    
    def downloaded_lists(self):
        txt_file = "downloaded.txt"
        with open(txt_file, "r") as f:
            lines = f.read().split()
        return lines

if __name__ == "__main__":
    img_dir = "/content/img/{}"
    bu = Scraper()
    tool = Tool()
    query = input("検索（無くても可）>>> ")
    artworks = int(input("何作品欲しい？>>> "))
    urls = bu.get_artworks(artworks, query)

    for url in urls:
        if not url in tool.downloaded_lists():
            bu.get_about_artworks(url)
            print("http://buhidoh.net/blog-entry-" + str(bu.artwork_id) + ".html")
            bu.download_image(bu.artwork_imgs, img_dir.format(bu.artwork_id))
            pdf_name = tool.pdf_name_gen(bu.artwork_id, bu.artwork_tags)
            tool.image_to_pdf(img_dir.format(bu.artwork_id), f"./pdf/{pdf_name}.pdf")
            tool.save_downloaded_url(url)
