from selenium import webdriver
import time,pickle
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

TIME_OUT = 10
WAIT_RENDER = 2
source_web = 'https://weibo.com/2120188435/H5loCfy90'

class fwd_node(object):
    def __init__(self,parent_id,usr_info,href_self=None,like_quant=0,subfwd_quant=0):
        '''
        :param parent_id: href to parent
        :param usr_info: a dictionary info of user, there are three categeries: usr_name, usr_id, usr_blog
        :param href_self: a href of the user about the event
        :param like_quant: quantity of the like
        :param subfwd_quant: quantity of forwarding
        '''
        self.parent_id = parent_id
        self.href_self = href_self
        self.usr_info = usr_info
        self.like_quant = like_quant
        self.subfwd_quant = subfwd_quant
    def change_like_quant(self,new_like_quant):
        self.like_quant = new_like_quant
    def change_subfwd_quant(self,new_subfwd_quant):
        self.subfwd_quant = new_subfwd_quant


def handle_one_fwd(parebt_id,item):
    '''
    tackle with each fwd and return a fwd instance
    :param parebt_id: the parent node user id
    :param item: the div html element that has the form div[action-type='feed_list_item']
    :return: a list that has the child node at the first. if the child node is special
            which means it does not has the href for his self about the event, then the
            list will also contain the grandson nodes following
    '''

    fwd_text = item.find_element_by_css_selector("span[node-type='text']").text

    #judge whether this forward is child forward, if it is not, return an empty list
    #else, tackle the info in it
    if "//@" in fwd_text:
        print(fwd_text)
        return []
    else:
        # get related element a for each type of info
        a_usr = item.find_element_by_css_selector("a[href *= 'https://weibo.com/'][node-type='name']")
        # form the structure of data stored
        usr_info = {
            'usr_name': a_usr.text,
            'usr_id': a_usr.get_attribute('usercard').split('=')[1],
            'usr_blog': a_usr.get_attribute('href')
        }

        # get the element a for the like and forward
        a_subfwd = item.find_element_by_css_selector("a[action-type='feed_list_forward']")
        a_subfwd_like = item.find_element_by_css_selector("a[action-type='forward_like'][title='赞']")

        # get forward quantity
        if a_subfwd.text == u'转发':
            subfwd_quant = 0
        else:
            subfwd_quant = int(a_subfwd.text.split(' ')[1])
            # subfwd_quant = 0

        # get like quantity
        if a_subfwd_like.find_elements_by_tag_name('em')[1].text == u'赞':
            subfwd_like_quant = 0
        else:
            subfwd_like_quant = int(a_subfwd_like.find_elements_by_tag_name('em')[1].text)

        # define the list for grandson nodes
        grandson_fwds_list = []
        if (subfwd_quant):
            # align the a_usr with the top
            browser.execute_script("arguments[0].scrollIntoView();", item)
            time.sleep(WAIT_RENDER)
            # wait until it's clickable
            wait = WebDriverWait(browser, TIME_OUT)
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[action-type='feed_list_forward']")))

            # click the subforward element a
            a_subfwd.click()
            # wait to render
            time.sleep(WAIT_RENDER)

            try:
                # get the href of this user for this event
                a_all_subfwds = browser.find_element_by_partial_link_text(u'查看所有')
                # a_all_subfwds = browser.find_element_by_css_selector("a[class='WB_cardmore S_txt1 S_line1 clearfix']")
                href_self = a_all_subfwds.get_attribute('href')

            # if error raised, the child node is a special node
            except Exception as e:
                print(usr_info['usr_name'] + " has no link for all forwards.")
                # give the href_self value of the child node
                href_self = 'UNKNOWN'

                # find the div elements for the list of grandsons
                grandsons_div = browser.find_element_by_css_selector("div[node-type='forward_link_default']")
                grandson_div_list = grandsons_div.find_elements_by_css_selector("div[node-type='forward_link_item']")

                # tackle with each grandson node
                for grandson in grandson_div_list:
                    # get element a about the user info
                    a_info = grandson.find_element_by_css_selector(
                        "div[class='WB_face W_fl']").find_element_by_tag_name('a')
                    grandson_info = {
                        'usr_name': a_info.get_attribute('title'),
                        'usr_id': None,
                        'usr_blog': 'https://' + a_info.get_attribute('href')
                    }

                    # get the element a about the forward again info
                    a_fwd_again = grandson.find_element_by_css_selector(
                        "a[class='S_txt1'][action-type='forward_again']")
                    a_grandson_like = grandson.find_element_by_css_selector("a[class='S_txt1'][title='赞']")
                    # get the grandson forward quantity
                    if a_fwd_again.text == u'转发':
                        grandson_fwd_quant = 0
                    else:
                        grandson_fwd_quant = int(a_fwd_again.text.split(' ')[1])

                    # get the grandson like quantity
                    if a_grandson_like.find_elements_by_tag_name('em')[1].text == u'赞':
                        grandson_like_quant = 0
                    else:
                        grandson_like_quant = int(a_grandson_like.find_elements_by_tag_name('em')[1].text)
                    # get the list of grandsons
                    grandson_fwds_list.append(
                        fwd_node(usr_info['usr_id'], grandson_info, like_quant=grandson_like_quant,
                                 subfwd_quant=grandson_fwd_quant))

            # find the close button
            a_close = browser.find_element_by_css_selector("a[class='W_ficon ficon_close S_ficon'][node-type='close']")
            a_close.click()
        else:
            href_self = None

        # conbine the child node and the grandson list if it exists to a lists
        fwd_instance = fwd_node(parebt_id, usr_info, href_self, subfwd_like_quant, subfwd_quant)
        return [fwd_instance,] + grandson_fwds_list

def handle_one_page(parent_id,page_of_fwds):
    '''
    tackle with one page of fwds
    :param parent_id: parent id
    :param page_of_fwds: the div element has the attribue div[class='list_ul'][node-type='feed_list']
    :return: a list of lists, the element of the return list is a list which contains child node and
            grandson nodes if they exist
    '''
    try:
        fwd_page_list = page_of_fwds.find_elements_by_css_selector("div[action-type='feed_list_item']")
    except Exception as e:
        print(e)
        print('There is no forward!')
        return 1
    fwd_instances_list = []

    # handle all forwards on this page
    for item in fwd_page_list:
        # '''drag into view and then click the subforwar button'''
        # # align the a_usr with the top
        # browser.execute_script("arguments[0].scrollIntoView();", item)
        # time.sleep(WAIT_RENDER)
        # # wait until it's clickable
        # wait = WebDriverWait(browser, TIME_OUT)
        # wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[action-type='feed_list_forward']")))

        item_result = handle_one_fwd(parent_id,item)
        if item_result != []:
            fwd_instances_list.append(item_result)
    return fwd_instances_list


options = webdriver.ChromeOptions()
# options.add_argument('-headless')
# options.add_argument('--disable-gpu')
browser = webdriver.Chrome(executable_path='./chromedriver',chrome_options=options)


#get the page source
browser.get(source_web)
browser.implicitly_wait(TIME_OUT)

#find the button for forward details and then click
fwd_click_items = browser.find_element_by_class_name('WB_handle')
fwd_click_item = fwd_click_items.find_element_by_css_selector("a[action-type='fl_forward']")
fwd_click_item.click()

#find the root user id
src_info_img = browser.find_element_by_css_selector("img[class='W_face_radius']")
root_id = src_info_img.get_attribute('usercard').split('&')[0].split('=')[1]

fwds_list = []
while(1):
    #wait for render
    time.sleep(WAIT_RENDER)
    # get the list of forwards
    fwd_page_css_slecct = "div[class='list_ul'][node-type='feed_list']"
    fwd_page = browser.find_element_by_css_selector(fwd_page_css_slecct)

    #get the list of forwards on this page
    result = handle_one_page(root_id,fwd_page)

    #whethter this is a empty page
    if result == 1:
        break
    #conbine result of this page with previous pages
    fwds_list = fwds_list + result

    #find the button to next page
    page_div = browser.find_element_by_class_name('W_pages')
    try:
        next_page_button = page_div.find_element_by_partial_link_text(u'下一页')
    except Exception as e:
        print("All pages has been handled.")
        break
    try:
        next_page_button.click()
    except Exception as e:
        time.sleep(TIME_OUT)
        next_page_button.click()

with open('./NBA.pkl','wb') as fp:
    pickle.dump(fwds_list,fp,pickle.HIGHEST_PROTOCOL)
#close the browser
# browser.delete_all_cookies()
# browser.close()
count = 0
for i in fwds_list:
    if fwds_list[i][0].usr_info['usr_name'] == '運動能力比較強的一號位':
        print(i)