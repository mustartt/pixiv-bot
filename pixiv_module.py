from pixivapi import Client

from pixivapi.errors import LoginError
from pixivapi.models import Illustration
from pixivapi.enums  import ContentType, RankingMode, SearchTarget, Size, Sort, Visibility
from pixivapi.common import HEADERS, format_bool, parse_qs, require_auth

from PIL import Image
from io import BytesIO

from typing import Callable
import json

AUTH_URL = 'https://oauth.secure.pixiv.net/auth/token'
BASE_URL = 'https://app-api.pixiv.net'
FILTER = 'for_ios'

class ExtendedClient(Client):
    @require_auth
    def search_popular_preview(self, word: str,
                               search_target=SearchTarget.TAGS_EXACT):
        """
        Search for popular previews at /v1/search/popular-preview/illust.

        :param str word: The search term.
        :param SearchTarget search_target: The target for the search term.
        
        :return: A dictionary containing the searched illustrations.
        .. code-block:: python
           {
               'illustrations': [Illustration, ...]
           }
        :rtype: dict
        :raises requests.RequestException: If the request fails.
        :raises BadApiResponse: If the response is not valid JSON.
        """
        response = self._request_json(
            method='get',
            url=f"{BASE_URL}/v1/search/popular-preview/illust",
            params={
                'word': word,
                'search_target': search_target.value,
                'sort': 'popular_desc',
                'filter': FILTER
            })

        return {
            'illustrations': [
                Illustration(**illust, client=self)
                for illust in response['illusts']
            ]
        }
    
    @require_auth
    def search_popular(self, word: str,
                       search_target=SearchTarget.TAGS_PARTIAL,
                       duration=None,
                       offset=None):
        """
        Search the illustrations by popularity. A maximum of 30 illustrations are
        returned in one response.

        :param str word: The search term.
        :param SearchTarget search_target: The target for the search term.
        :param Duration duration: An optional max-age for the illustrations.
        :param int offset: The number of illustrations to offset by.
        
        :return: A dictionary containing the searched illustrations, the
            offset for the next page of search images (``None`` if there
            is no next page), and the search span limit.
        .. code-block:: python
           {
               'illustrations': [Illustration, ...],  # List of illustrations.
               'next': 30,  # Offset to get the next page of illustrations.
               'search_span_limit': 31536000,
           }
        :rtype: dict
        :raises requests.RequestException: If the request fails.
        :raises BadApiResponse: If the response is not valid JSON.
        """
        
        response = self._request_json(
            method='get',
            url=f"{BASE_URL}/v1/search/illust",
            params={
                'word': word,
                'search_target': search_target.value,
                'sort': 'popular_desc',
                'duration': duration.value if duration else None,
                'offset': offset,
                'filter': FILTER,
            })

        return {
            'illustrations': [
                Illustration(**illust, client=self)
                for illust in response['illusts']
            ],
            'next': parse_qs(response['next_url'], param='offset'),
            'search_span_limit': response['search_span_limit'],
        }

    def download_byte_stream(self, url: str, referer='https://pixiv.net') -> BytesIO:
        """
        This function returns the the BytesIO object of file at url.
        uses the client's access token if available.
        
        :param str url:     The URL to the file.
        :param str referer: The Referer header.

        :return io.BytesIO 

        :rtype io.BytesIO   IO Buffered Bytes Stream
        """

        response = self.session.get(
            url=url, headers={'Referer': referer}, stream=True
        )

        return BytesIO(response.content)

    def download_image(self, url: str, referer='https://pixiv.net') -> Image:
        """
        This function returns the an image object of file at url.
        ueses the client's access token if available.
        
        :param str url:     The URL to the file.
        :param str referer: The Referer header.

        :return Image

        :rtype PIL.Image    Pillow Image Object
        """

        return Image.open(self.download_byte_stream(url, referer))


    def get_illust_byte_streams(self, illust: Illustration, size=Size.LARGE):
        """
        Load the illustration to an array of BytesIO. If illustration has
        only a single page, the array of BytesIO with be length of one
        
        :param pixivapi.models.Illustration illust: The illustration will be downloaded
            to this directory.
        :param Size size: The size of the image to download.

        :rtype List[io.BytesIO]: Array of Images
        
        :raises requests.RequestException: If the request fails.
        """

        referer = (
            'https://www.pixiv.net/member_illust.php?mode=medium'
            f'&illust_id={illust.id}'
        )

        image_arr = []

        if illust.meta_pages:
            for page in illust.meta_pages:
                img = self.download_byte_stream(page[size], referer=referer)
                image_arr.append(img)
        else:
            img = self.download_byte_stream(illust.image_urls[size], referer=referer)
            image_arr.append(img)

        return image_arr

    

    def get_illust_images(self, illust: Illustration, size=Size.LARGE):
        """
        Load the illustration to an array of Images. If illustration has
        only a single page, the array of Images with be length of one
        
        :param pixivapi.models.Illustration illust: The illustration will be downloaded
            to this directory.
        :param Size size: The size of the image to download.

        :rtype List[Pillow.Image]: Array of Images
        
        :raises requests.RequestException: If the request fails.
        """

        referer = (
            'https://www.pixiv.net/member_illust.php?mode=medium'
            f'&illust_id={illust.id}'
        )

        image_arr = []

        if illust.meta_pages:
            for page in illust.meta_pages:
                img = self.download_image(page[size], referer=referer)
                image_arr.append(img)
        else:
            img = self.download_image(illust.image_urls[size], referer=referer)
            image_arr.append(img)

        return image_arr
            
    def search_autocomplete(self, word: str, ver='v2'):
        """
        Get autocompleted tags for the given search query word. Contains translated
        tags and English Tags.

        :param str word: The search term
        :param str ver:  The search query version

        :return: A List containing a dictionary with the translated tags and english tags

        .. code-block:: python
        [{
            'name': 'Translated Tag',
            'translated_name': 'English Tag'
        }]

        :rtype list
        """
        
        response = self._request_json(
            method='get',
            url=f"{BASE_URL}/{ver}/search/autocomplete",
            params={
                'word': word
                }
            )

        return response['tags']
        



class PixivModule:
    def __init__(self, username: str, password: str,
                 write_refresh: Callable[[str], None], refresh_token=None) -> None:
        """
        Create pixiv-api client with the correct authentication
            - attempts refresh_token first
            - on failure, use username and password to authenticate
                - on failure, raise Authentication Error 
        """

        self.client = ExtendedClient()
        
        try:
            print("Attempting login with refresh token: ", end="")
            self.client.authenticate(refresh_token)
            print("Sucess")
        except LoginError:
            print("Login Failed using username and password.")
            try:
                self.client.login(username, password)
                new_token = self.client.refresh_token
                write_refresh(new_token) #save token
            except LoginError:
                raise Exception("Authentication Error")

    def get_client(self) -> Client:
        """Returns the pixiv-api client"""
        return self.client



    





































    


    
            
        

