from selenium import webdriver
from time import sleep
from enum import Enum
from selenium.webdriver.common.keys import Keys
from random import uniform

class LikeStatus(Enum):
    LIKED_ALREADY = 0
    LIKED_NEW     = 1
    LIKE_ERROR    = 2


def randomSleep(a):
    time_to_sleep = uniform(a, a+0.7)
    sleep(time_to_sleep)


class InstaBot:
    def __init__(self, username, pw):
        self.driver = webdriver.Chrome()
        self.username = username
        self.driver.get("https://instagram.com")
#        randomSleep(2)
#        self.driver.find_element_by_xpath("//a[contains(text(), 'Log in')]")\
#            .click()
        randomSleep(2)
        self.driver.find_element_by_xpath("//input[@name=\"username\"]")\
            .send_keys(username)
        self.driver.find_element_by_xpath("//input[@name=\"password\"]")\
            .send_keys(pw)
        self.driver.find_element_by_xpath('//button[@type="submit"]')\
            .click()
        randomSleep(4)
        self.driver.find_element_by_xpath("//button[contains(text(), 'Not Now')]")\
            .click()
        randomSleep(2)

    def get_unfollowers(self):
        self.driver.find_element_by_xpath("//a[contains(@href,'/{}')]".format(self.username))\
            .click()
        randomSleep(2)
        self.driver.find_element_by_xpath("//a[contains(@href,'/following')]")\
            .click()
        following = self._get_names()
        self.driver.find_element_by_xpath("//a[contains(@href,'/followers')]")\
            .click()
        followers = self._get_names()
        not_following_back = [user for user in following if user not in followers]
        print(not_following_back)

    def _get_names(self):
        randomSleep(2)
        sugs = None
        try:
            sugs = self.driver.find_element_by_xpath('//h4[contains(text(), Suggestions)]')
        except:
            print("No suggestions")
        if sugs is not None:
            self.driver.execute_script('arguments[0].scrollIntoView()', sugs)
            randomSleep(2)
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
        self.driver.find_element_by_xpath("//a[contains(@href,'/{}')]".format(self.username))\
            .click()
        randomSleep(2)
        self.driver.find_element_by_xpath("//a[contains(@href,'/following')]")\
            .click()
        following = self._get_names()

        for name in following:
            self.like_n_photos_of_user(name, num_photos)

    def _like_single_photo(self, photo_url):

        ret_val = LikeStatus.LIKED_NEW
        try:
            self.driver.execute_script(f"window.open('{photo_url}');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            randomSleep(1)

            svg_path = "//*[local-name() = 'svg']"
            aria = self.driver.find_element_by_xpath(svg_path)
            #aria_items = self.driver.execute_script('var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;', aria)

            #print(aria_items)
            aria_attr = aria.get_attribute('aria-label')
            #print(f"Aria attribute = {aria_attr}")
            is_liked = aria_attr == 'Unlike'

            if not is_liked:

                like_button_path = '//*[@id="react-root"]/section/main/div/div[1]/article/div[2]/section[1]/span[1]/button'

                like_button = self.driver.find_element_by_xpath(like_button_path)
                like_button.click()
                randomSleep(1)
            else:
                #print("This photo is already liked")
                ret_val = LikeStatus.LIKED_ALREADY

            self.driver.close()
        except Exception as e:
            print(str(e))
            ret_val = LikeStatus.LIKE_ERROR
            self.driver.close()
        
        self.driver.switch_to.window(self.driver.window_handles[0])

        return ret_val

    def like_n_photos_of_user(self, user, n=-1): # -1 = infinite

        num_of_new_likes = 0

        pics = self._get_all_photos_of_user(user, n)
        
        #i = 0
        for pic in pics:
            #print("Opening a new tab")
            #self.driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL, 't')
            #self.driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL, Keys.TAB)
            if self._like_single_photo(pic) == LikeStatus.LIKED_NEW:
                num_of_new_likes += 1

            #i+=1
            #if i > 2:
            #    break

        print(f"Liked {num_of_new_likes} out of a total of {len(pics)} photos")

    def _get_all_photos_of_user(self, user, n=-1):
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


    def _scroll_page_and_get_photos(self, speed=8):
        # Returns a set of photo links while scrolling through the profile

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

    def _scroll_page_infinite(self, speed=8):
        current_scroll_position, new_height= 0, 1
        while current_scroll_position <= new_height:
            current_scroll_position += speed
            self.driver.execute_script("window.scrollTo(0, {});".format(current_scroll_position))
            randomSleep(1)
            new_height = self.driver.execute_script("return document.body.scrollHeight")

    def search(self, what):
        search_path = '//*[@id="react-root"]/section/nav/div[2]/div/div/div[2]/input'
        self.driver.find_element_by_xpath(search_path).send_keys(what)
        self.driver.find_element_by_xpath(search_path).send_keys(Keys.ENTER)
        self.driver.find_element_by_xpath(search_path).send_keys(Keys.ENTER)

        randomSleep(2)

        first_option_path = '//*[@id="react-root"]/section/nav/div[2]/div/div/div[2]/div[2]/div[2]/div/a[1]'
        self.driver.find_element_by_xpath(first_option_path).click()

    def like_n_photos_in_hashtag(self, tag, n):
        self.search(tag)

        num_of_new_likes = 0

        pics = self._scroll_page_and_get_n_photos(speed=1000, num_photos=n)
        
        #i = 0
        for pic in pics:
            #print("Opening a new tab")
            #self.driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL, 't')
            #self.driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL, Keys.TAB)
            if self._like_single_photo(pic) == LikeStatus.LIKED_NEW:
                num_of_new_likes += 1

            #i+=1
            #if i > 2:
            #    break

        print(f"Liked {num_of_new_likes} out of a total of {len(pics)} photos")

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

            # TEMPORARY
            #break

        return pic_set




#from secrets import get_user
import secrets

#uname, pw = secrets.get_user('dummy')
#uname, pw = secrets.get_user('real')
uname, pw = secrets.get_user('alt')


my_bot = InstaBot(uname, pw)

#my_bot.get_unfollowers()
#my_bot.like_n_photos_of_user("chefelirandahan")
#my_bot.like_n_photos_of_user("damirbar")
#my_bot.like_n_photos_of_user("stavhi")
#my_bot.like_n_photos_of_user("sefishalom")
#my_bot.like_n_photos_of_user("chenlevyy")
#my_bot.like_n_photos_of_user("lance210", 10)


#my_bot.search('#likeforlike')

my_bot.like_n_photos_in_hashtag('#meme', 1000)


#my_bot.like_all_following_photos(10)
