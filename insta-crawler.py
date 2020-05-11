# Standard imports
from time import sleep
from enum import Enum
from random import uniform
import argparse

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.keys import Keys



class LikeStatus(Enum):
    LIKED_ALREADY = 0
    LIKED_NEW     = 1
    LIKE_ERROR    = 2


def randomSleep(a):
    # Random sleeping for a less bot-like behavior
    time_to_sleep = uniform(a, a+0.7)
    sleep(time_to_sleep)


class InstaCrawler:
    def __init__(self, username, pw):
        # Log into <username> account

        self.driver = webdriver.Chrome()
        self.username = username
        self.driver.get("https://instagram.com")
        randomSleep(2)

        self.driver.find_element_by_xpath("//input[@name=\"username\"]")\
            .send_keys(username)
        self.driver.find_element_by_xpath("//input[@name=\"password\"]")\
            .send_keys(pw)
        self.driver.find_element_by_xpath('//button[@type="submit"]')\
            .click()
        randomSleep(4)

        # Click "Not Now" when Instagram asks to turn on the notifications
        self.driver.find_element_by_xpath("//button[contains(text(), 'Not Now')]")\
            .click()
        randomSleep(2)


    def get_non_followback_users(self):
        # Get a list of profiles which you follow but do not follow you back

        self.driver.find_element_by_xpath("//a[contains(@href,'/{}')]".format(self.username))\
            .click()
        randomSleep(2)

        self.driver.find_element_by_xpath("//a[contains(@href,'/following')]")\
            .click()
        randomSleep(2)
        following = self._get_names()

        self.driver.find_element_by_xpath("//a[contains(@href,'/followers')]")\
            .click()
        randomSleep(2)
        followers = self._get_names()

        not_following_back = [user for user in following if user not in followers]
        print(not_following_back)

    def _get_names(self):
        sugs = None

        # There isn't always the "suggested profiles to follow" on Instagram
        try:
            sugs = self.driver.find_element_by_xpath('//h4[contains(text(), Suggestions)]')
        except:
            print("No suggestions")
        if sugs is not None:
            self.driver.execute_script('arguments[0].scrollIntoView()', sugs)
            randomSleep(2)

        # Scroll until you hit the bottom
        scroll_box = self.driver.find_element_by_xpath("/html/body/div[4]/div/div[2]")
        last_ht, ht = 0, 1
        while last_ht != ht:
            last_ht = ht
            randomSleep(1)
            ht = self.driver.execute_script("""
                arguments[0].scrollTo(0, arguments[0].scrollHeight); 
                return arguments[0].scrollHeight;
                """, scroll_box)

        links = scroll_box.find_elements_by_tag_name('a')
        names = [name.text for name in links if name.text != '']

        # close button
        self.driver.find_element_by_xpath("/html/body/div[4]/div/div[1]/div/div[2]/button")\
            .click()
        return names

    def like_all_following_photos(self, num_photos=-1):
        # Like <num_photos> photos of every user you follow
        # The default value (-1) is infinity, meaning every photo
        self.driver.find_element_by_xpath("//a[contains(@href,'/{}')]".format(self.username))\
            .click()
        randomSleep(2)
        self.driver.find_element_by_xpath("//a[contains(@href,'/following')]")\
            .click()
        following = self._get_names()

        for name in following:
            self.like_n_photos_of_user(name, num_photos)


    def _follow_within_photo(self, photo_url):
        # Follow a profile from the context of a photo
        # TODO: Modify LikeStatus name to a more generic name to fit here

        ret_val = LikeStatus.LIKED_NEW
        try:
            self.driver.get(f"{photo_url}")
            randomSleep(1)

            follow_button_path = '//*[@id="react-root"]/section/main/div/div[1]/article/header/div[2]/div[1]/div[2]/button'

            follow_button = self.driver.find_element_by_xpath(follow_button_path)

            is_followed = follow_button.text == 'Following'

            if not is_followed:

                follow_button.click()
                randomSleep(1)
            else:
                #print("This photo is already liked")
                ret_val = LikeStatus.LIKED_ALREADY

            #self.driver.close()
        except Exception as e:
            print(str(e))
            ret_val = LikeStatus.LIKE_ERROR
            #self.driver.close()
        
        #self.driver.switch_to.window(self.driver.window_handles[0])

        return ret_val

    def _open_new_tab(self, url):
        self.driver.execute_script(f"window.open('{url}');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        
    def _close_current_tab(self, url):
        self.driver.close()

    def _goto_tab_n(self, i):
        try:
            self.driver.switch_to.window(self.driver.window_handles[i])
        except:
            print(f"Error trying to reach tab {i}")

    def _get_all_attributes_of_element(self, elem):
        elem_items = self.driver.execute_script('var items = {}; for (index = 0; index < arguments[0].attributes.length; \
                ++index) { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;', \
                elem)
        return elem_items

    def _like_single_photo(self, photo_url):

        ret_val = LikeStatus.LIKED_NEW
        try:
            self.driver.get(photo_url)
            randomSleep(1)

            # The SVG contains the "aria-attr" of "Like" or "Unlike". This is how you determine if you have already
            #     liked this photo before
            svg_path = "//*[local-name() = 'svg']"
            aria = self.driver.find_element_by_xpath(svg_path)

            aria_attr = aria.get_attribute('aria-label')
            is_liked = aria_attr == 'Unlike'

            if not is_liked:

                like_button_path = '//*[@id="react-root"]/section/main/div/div[1]/article/div[2]/section[1]/span[1]/button'

                like_button = self.driver.find_element_by_xpath(like_button_path)
                like_button.click()
                randomSleep(1)
            else:
                ret_val = LikeStatus.LIKED_ALREADY

        except Exception as e:
            print(str(e))
            ret_val = LikeStatus.LIKE_ERROR
        

        return ret_val

    def like_n_photos_of_user(self, user, n=-1):
        # Like <n> photos of a given profile.
        # The default value of n (-1) is infinity, meaning every photo

        num_of_new_likes = 0

        pics = self._get_n_photos_of_user(user, n)
        
        for pic in pics:
            if self._like_single_photo(pic) == LikeStatus.LIKED_NEW:
                num_of_new_likes += 1

        print(f"Liked {num_of_new_likes} out of a total of {len(pics)} photos")

    def _get_n_photos_of_user(self, user, n=-1):
        # Get <n> links of the photos of a user.
        # This is done by scrolling and getting every photo in parallel. Why? Because when you open a user's
        #     page, you get more photos as you scroll down, BUT you also lose the upper photos as you scroll down.

        self.driver.get(f"https://instagram.com/{user}")
        randomSleep(2)

        if n == -1:
            pics = self._scroll_page_and_get_photos(speed=1000)
        else:
            pics = self._scroll_page_and_get_n_photos(speed=1000, num_photos=n)

        print(f"The number of photos found is {len(pics)}")
        for elem in pics:
            print(elem)

        return pics


    def _scroll_page_and_get_photos(self, speed=1000):
        # Returns a set of photo links while scrolling through the profile
        # TODO: Need to refactor this one with _scroll_page_infinite

        pic_set = set()
        current_scroll_position, new_height= 0, 1
        print(f"current_scroll_position={current_scroll_position} new_height={new_height}")
        while current_scroll_position <= new_height:
            pic_links = self.driver.find_elements_by_xpath("//*[starts-with(@href, '/p/')]")
            
            pic_set.update([elem.get_property('href') for elem in pic_links])
            current_scroll_position += speed
            self.driver.execute_script("window.scrollTo(0, {});".format(current_scroll_position))
            randomSleep(1.5)
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            # TEMPORARY
            #break

        return pic_set

    def _scroll_page_infinite(self, speed=1000):
        # Scroll a page until you hit the bottom

        current_scroll_position, new_height= 0, 1
        while current_scroll_position <= new_height:
            current_scroll_position += speed
            self.driver.execute_script("window.scrollTo(0, {});".format(current_scroll_position))
            randomSleep(1)
            new_height = self.driver.execute_script("return document.body.scrollHeight")

    def search(self, what):
        # Search a user or a hashtag

        search_path = '//*[@id="react-root"]/section/nav/div[2]/div/div/div[2]/input'
        self.driver.find_element_by_xpath(search_path).send_keys(what)
        self.driver.find_element_by_xpath(search_path).send_keys(Keys.ENTER)
        self.driver.find_element_by_xpath(search_path).send_keys(Keys.ENTER)

        randomSleep(2)

        first_option_path = '//*[@id="react-root"]/section/nav/div[2]/div/div/div[2]/div[2]/div[2]/div/a[1]'
        self.driver.find_element_by_xpath(first_option_path).click()

    def like_n_photos_in_hashtag(self, tag, n):
        # TODO: refactor this one and "like_n_photos_of_user"
        self.search(tag)

        num_of_new_likes = 0

        pics = self._scroll_page_and_get_n_photos(speed=1000, num_photos=n)
        
        for pic in pics:
            if self._like_single_photo(pic) == LikeStatus.LIKED_NEW:
                num_of_new_likes += 1

        print(f"Liked {num_of_new_likes} out of a total of {len(pics)} photos")

    def follow_n_profiles_in_hashtag(self, tag, n):
        # Search a hashtag, collect n first photos and follow the poster

        self.search(tag)
        randomSleep(1)
        num_of_new_likes = 0

        pics = self._scroll_page_and_get_n_photos(speed=1000, num_photos=n)
        
        for pic in pics:
            if self._follow_within_photo(pic) == LikeStatus.LIKED_NEW:
                num_of_new_likes += 1

        print(f"Followed {num_of_new_likes} new profiles out of a total of {len(pics)} profiles")

    def _scroll_page_and_get_n_photos(self, speed=1000, num_photos=10):
        # Returns a set of photo links while scrolling through the profile

        pic_set = set()
        current_scroll_position, new_height= 0, 1
        while current_scroll_position <= new_height and len(pic_set) < num_photos:
            pic_links = self.driver.find_elements_by_xpath("//*[starts-with(@href, '/p/')]")
            
            pic_set.update([elem.get_property('href') for elem in pic_links if elem])
            current_scroll_position += speed
            self.driver.execute_script("window.scrollTo(0, {});".format(current_scroll_position))
            randomSleep(1)
            new_height = self.driver.execute_script("return document.body.scrollHeight")

        return pic_set



import secrets
#uname, pw = secrets.get_user('dummy')
#uname, pw = secrets.get_user('real')
uname, pw = secrets.get_user('alt')
my_bot = InstaCrawler(uname, pw)


def main():
    parser = argparse.ArgumentParser(description='Instagram bot')

    wo_args = parser.add_argument_group('w/o args')
    w_args  = parser.add_argument_group('w/ args')

    w_args.add_argument('-u', '--like-user-photos', help='The user to like his/her photos (can be limited by -n)')
    w_args.add_argument('-t', '--like-hashtag-photos', help='The hashtag to like photos by (can be limited by -n)')
    w_args.add_argument('-f', '--follow-hashtag-profiles', help='Follow n profiles hashtag (can be limited by -n, default=100)')
    
    wo_args.add_argument('-a', '--like-following-photos', action="store_true", help='Like photos of profiles you follow (can be limited by -n)')

    w_args.add_argument('-n', '--number', type=int, help='Number of photos to like')


    args = parser.parse_args()

    n = -1
    if args.number:
        n = args.number

    if args.like_following_photos:
        my_bot.like_all_following_photos(n)
        return

    if args.like_user_photos:
        user_to_like = args.like_user_photos
        my_bot.like_n_photos_of_user(user_to_like, n)
        return

    if args.like_hashtag_photos:
        hashtag_to_like = args.like_hashtag_photos
        my_bot.like_n_photos_of_user('#' + hashtag_to_like, n)
        return
    
    if args.follow_hashtag_profiles:
        if n < 0 or n > 100 :
            n = 100
        hashtag_to_follow = args.follow_hashtag_profiles
        my_bot.follow_n_profiles_in_hashtag('#' + hashtag_to_follow, n)

if __name__ == '__main__':
    main()


