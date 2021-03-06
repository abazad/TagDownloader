# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
import requests, json, urllib
# Create your views here.

client_id = #"add client id here"
client_secret = #"add client secret here"

insta_auth_url = "https://api.instagram.com/oauth/authorize/?client_id=" + client_id
insta_auth_url += "&redirect_uri=http://localhost:8000/authenticate/&response_type=code&scope=public_content"
		

def authenticate(request):
	if request.GET.get('code'):
		code = request.GET.get('code')
		request.session['is_authenticated'] = True
		request.session['code'] = code
		print ("authenticated and got the code, now getting token")
		access_token_get_url = "https://api.instagram.com/oauth/access_token"
		data = {
			"client_id": client_id,
			"client_secret": client_secret,
			"grant_type": "authorization_code",
			"redirect_uri": "http://localhost:8000/authenticate/",
			"code": code,
			}
		response = requests.post(access_token_get_url, data).json()
		request.session["access_token"] = response["access_token"]
		return HttpResponseRedirect("/")
	else:
		return HttpResponse("Something went wrong in authentication")

@csrf_exempt
def index(request):
	auth = request.session.get('access_token')
	if auth is None:
		#redirect to authenticate and get access token
		print ("redirecting to authentication")
		return HttpResponseRedirect(insta_auth_url)
	else:
		if request.method == "GET": 
			template = loader.get_template('downloader/search.html')
			context = {
				"search": True,
			}
			return HttpResponse(template.render(context, request))
		else:
			access_token = auth
			if request.POST.get('tag') and not request.POST.get("location"):
				tag = request.POST.get('tag')
				get_tag_count_url = "https://api.instagram.com/v1/tags/"+tag+"?access_token="+access_token
				response = requests.get(get_tag_count_url)
				if response.json()["meta"]['code'] == 200:
					item_count = response.json()["data"]["media_count"]
					tag = response.json()["data"]["name"]
					context = {
						"getlocation": True,
						"tag": tag,
						"item_count": item_count,
					}
					template = loader.get_template('downloader/search.html')
					return  HttpResponse(template.render(context, request))
				else:
					# error with current access token, needs to reauthenticate
					error = response.json()["meta"]["error_type"]
					error_message = response.json()["meta"]["error_message"]
					if error == "OAuthPermissionsException":
						#first show error msg and then ask if reauth needed or not
						#this will be added later
						print ("redirecting to authentication")
						return HttpResponseRedirect(insta_auth_url)
			elif request.POST.get("location"):
				location = request.POST.get("location")
				tag = request.POST.get("tag")
				count = 10 #number of count of images bro
				get_tag_content_url = "https://api.instagram.com/v1/tags/"+tag+"/media/recent?access_token="+access_token+"&count="+str(count)
				response = requests.get(get_tag_content_url).json()
				
				image_urls = []
				get_media_url = "https://api.instagram.com/v1/media/"
				if response["meta"]["code"] == 200:
					for i in response["data"]:
						image_urls.append({
							"name": i["id"],
							"url": i["images"]["standard_resolution"]["url"]
							})

					outputresp = "Files with following url have been downloaded and saved at "+location+"<br>"

					for i in image_urls:
						testfile = urllib.URLopener()
						testfile.retrieve(i["url"], location+"/"+i["name"]+".jpg")
						outputresp += i["url"]+"<br>"

					return HttpResponse(outputresp)
				else:
					return HttpResponse("Something went Wrong with fetching the image urls")


