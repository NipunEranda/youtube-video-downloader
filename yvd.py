from pytubefix import YouTube
import subprocess
import os
import os.path
import sys
import concurrent.futures
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import json
from PIL import Image, ImageTk
from urllib.request import urlopen
from io import BytesIO
import threading
import random

# Tools
def remove_duplicates(list):
    K = "qualityLabel"
    memo = set()
    res = []
    for sub in list:
        
        # testing for already present value
        if sub[K] not in memo:
            res.append(sub)
            
            # adding in memo if new value
            memo.add(sub[K])
            
    return res

def download_video(index, downloads):
    downloads[index]['yt_video_stream'].download(output_path='temp', filename=downloads[index]['tempVideoName'])
    
def download_audio(index, downloads):
    downloads[index]['yt_audio_stream'].download(output_path='temp', filename=downloads[index]['tempAudioName'])

class YT:
    def __init__(self, root, url):
        self.root = root
        self.url = url
        self.yt = YouTube(self.url, on_progress_callback=self.on_download_progress, use_oauth=True, allow_oauth_cache=True)
        self.downloadBtnList = []
        self.tempVideoName = ''
        self.tempAudioName = ''
        self.last_row = 3
        self.videoDownloadProgress = 0
        self.audioDownloadProgress = 0
        self.downloads = []
        
        if self.yt.vid_info.get('streamingData') != None:
            filteredQualities = [x for x in self.yt.vid_info.get('streamingData').get('adaptiveFormats') if x.get('qualityLabel') != None and 'p' in x.get('qualityLabel') and 'HDR' not in x.get('qualityLabel')]
            self.qualityList = remove_duplicates(filteredQualities)
        else:
            self.qualityList = [{ "qualityLabel":'144p' }, { "qualityLabel":'240p' }, { "qualityLabel":'360p' }, { "qualityLabel":'480p' }, { "qualityLabel":'720p' }, { "qualityLabel":'1080p' }]
        
        if(self.yt.title):
            u = urlopen(self.yt.thumbnail_url)
            raw_data = u.read()
            u.close()
            
            im = Image.open(BytesIO(raw_data))
            photo = ImageTk.PhotoImage(im)

            thumbnail = Label(root, image=photo)
            thumbnail.image = photo
            thumbnail.grid(row=2, padx=20, pady=10)
            
            for index, quality in enumerate(self.qualityList, start=0):
                Button(root, text=f"Download {quality.get('qualityLabel')}", padx=40, pady=5, command=lambda i=index: self.download_video(f"{self.qualityList[i].get('qualityLabel').split("p")[0]}p")).grid(row=index + 3, column=0, columnspan=2, padx=5, pady=10)
                self.last_row = self.last_row + 1
                
        
        root.eval('tk::PlaceWindow . center')
                
    
    def combine_audio_video(self, video_file, audio_file, output_file):
        subprocess.run(f"ffmpeg.exe -i {video_file} -i {audio_file} -c copy \"{output_file}\"")
        # subprocess.call(f"ffmpeg -y -i {video_file} -i {audio_file} -c copy \"{output_file}\"", shell=True)
        os.remove(video_file)
        os.remove(audio_file)
        
    def on_download_progress(self, stream, chunk, bytes_remaining):
        downloadIndex = self.downloads.index([d for d in self.downloads if stream.itag == d['yt_video_stream'].itag or stream.itag == d['yt_audio_stream'].itag][0])
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = (bytes_downloaded / total_size) * 100
        
        if(percentage > 0):
            if(stream.type == 'audio'):
                # self.downloads[downloadIndex]['videoDownloadLabel'] = percentage
                self.downloads[downloadIndex]['audioDownloadLabel'].config(text=percentage)
            else:
                # self.downloads[downloadIndex]['videoDownloadProgress'] = percentage
                self.downloads[downloadIndex]['videoDownloadLabel'].config(text=percentage)
                
        
    def runAll(self, id):
        try:
            download = [d for d in self.downloads if d['id'] == id][0]
            downloadIndex = self.downloads.index(download)
            self.downloads[downloadIndex]['processes'] = []
            
            self.downloads[downloadIndex]['yt_video_stream'] = self.yt.streams.filter(only_video=True, mime_type="video/mp4", res=download['resolution']).first()
            self.downloads[downloadIndex]['yt_audio_stream'] = self.yt.streams.filter(only_audio=True, mime_type="audio/mp4").order_by("bitrate").desc().first()
            if self.downloads[downloadIndex]['yt_video_stream'] and self.downloads[downloadIndex]['yt_audio_stream']:
                self.downloads[downloadIndex]['tempVideoName'] = f"{self.downloads[downloadIndex]['yt_video_stream'].title.replace(";", "_").replace(" ", "_").replace("'", "_").replace("`", "_").replace(",", "_").replace("‘", "_").replace("’", "_").replace("/", "-").replace("\\", "-").replace(":", "-").replace("*", "-").replace("?", "-").replace("\"", "-").replace("<", "-").replace(">", "-").replace("|", "-")}-{self.downloads[downloadIndex]['resolution']}.mp4"
                self.downloads[downloadIndex]['tempAudioName'] = f"{self.downloads[downloadIndex]['yt_audio_stream'].title.replace(";", "_").replace(" ", "_").replace("'", "_").replace("`", "_").replace(",", "_").replace("‘", "_").replace("’", "_").replace("/", "-").replace("\\", "-").replace(":", "-").replace("*", "-").replace("?", "-").replace("\"", "-").replace("<", "-").replace(">", "-").replace("|", "-")}-{self.downloads[downloadIndex]['resolution']}.mp3"
                
                
                self.downloads[downloadIndex]['audioDownloadLabel'] = Label(self.root, text=f"Audio: {0}", padx=5, pady=5)
                self.downloads[downloadIndex]['audioDownloadLabel'].grid(row=self.last_row + 1, column=0, columnspan=2, padx=5, pady=10)
                self.last_row = self.last_row + 1
                
                self.downloads[downloadIndex]['videoDownloadLabel'] = Label(self.root, text=f"Video: {0}", padx=5, pady=5)
                self.downloads[downloadIndex]['videoDownloadLabel'].grid(row=self.last_row + 1, column=0, columnspan=2, padx=5, pady=10)
                self.last_row = self.last_row + 1
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # Run func1 and func2 in parallel with their respective arguments
                    future1 = executor.submit(download_video, downloadIndex, self.downloads)
                    future2 = executor.submit(download_audio, downloadIndex, self.downloads)

                    # Wait for the results (if needed)
                    result1 = future1.result()
                    result2 = future2.result()
                
                
                self.combine_audio_video(f"temp/{self.downloads[downloadIndex]['tempVideoName']}", f"temp/{self.downloads[downloadIndex]['tempAudioName']}", f"downloads/{self.downloads[downloadIndex]['yt_video_stream'].title.replace("/", "-").replace("\\", "-").replace(":", "-").replace("*", "-").replace("?", "-").replace("\"", "-").replace("<", "-").replace(">", "-").replace("|", "-")}-{self.downloads[downloadIndex]['resolution']}.mp4")
                print("Video Downloaded")
        except Exception as e:
            print(e)

    def download_video(self, resolution):
        self.selectedResolution = resolution
        id = random.randint(100, 100000)
        self.downloads.append({ "id": id, "url": self.url, "resolution": resolution })
        uploadThread = threading.Thread(target=self.runAll, args=(id, ))
        uploadThread.start()

            
        
class PlaceholderText:
    def __init__(self, root, urlSearch):


        # Placeholder text
        self.placeholder = "Enter your text here..."

        # Insert placeholder text
        urlSearch.insert(END, self.placeholder)

        # Bind focus and unfocus events
        urlSearch.bind("<FocusIn>", self.clear_placeholder)
        urlSearch.bind("<FocusOut>", self.add_placeholder)

    def clear_placeholder(self, event=None):
        """Clear placeholder when text widget gets focus"""
        current_text = urlSearch.get("1.0", END).strip()
        if current_text == self.placeholder:
            urlSearch.delete("1.0", END)

    def add_placeholder(self, event=None):
        """Add placeholder when text widget loses focus and is empty"""
        current_text = urlSearch.get("1.0", END).strip()
        if not current_text:
            urlSearch.insert(END, self.placeholder)

def initiateSearch(root):
    url = urlSearch.get("1.0","end-1c")
    if(url != "" and url != "Enter your text here..."):
        YTD = YT(root, url)
    else:
        messagebox.showinfo("showinfo", "URL is not valid!")

def main():
    # Create temp and downloads folders if doesn't exists
    if not os.path.exists("temp"):
        os.makedirs("temp")
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    
    root.title("Youtube Video Downloader")
    root.resizable(False, False)
    root.eval('tk::PlaceWindow . center')

    global urlSearch, searchBtn
    
    searchBtn = Button(root, text="Search", padx=40, pady=5, command=lambda: initiateSearch(root))
    searchBtn.grid(row=1, column=0, columnspan=2, padx=5, pady=10)
    
    urlSearch = Text(root,  height = 1, width = 40, padx=10, pady=10)
    urlSearch.grid(row=0, column=0, columnspan=2, pady=10, padx=10)
    PlaceholderText(root, urlSearch)  
    
def removeFolder(dir_path):
    # List all files in the directory
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        
        # Check if it is a file (not a subdirectory)
        if os.path.isfile(file_path):
            os.remove(file_path)  # Remove the file
            print(f"Deleted file: {filename}")  
            
    os.rmdir(dir_path)
    
def cleanTemp():
    removeFolder("temp")
    root.quit()

if __name__ == "__main__":
    global root
    # multiprocessing.freeze_support()
    root = Tk()
    
    main()
    
    root.protocol("WM_DELETE_WINDOW", cleanTemp)
    root.mainloop()