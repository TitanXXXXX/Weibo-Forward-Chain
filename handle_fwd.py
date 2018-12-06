from selenium import webdriver
import time,pickle
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

TIME_OUT = 10
WAIT_RENDER = 2
source= 'https://weibo.com/2120188435/H5loCfy90'

class fwd_node(object):
    def __init__(self,parent_name,usr_info,href_self=None,like_quant=0,subfwd_quant=0):
        '''
        :param parent_name: name of parent
        :param usr_info: a dictionary info of user, there are three categeries: usr_name, usr_id, usr_blog
        :param href_self: a href of the user about the event
        :param like_quant: quantity of the like
        :param subfwd_quant: quantity of forwarding
        '''
        self.parent_name = parent_name
        self.href_self = href_self
        self.usr_info = usr_info
        self.like_quant = like_quant
        self.subfwd_quant = subfwd_quant
    def change_like_quant(self,new_like_quant):
        self.like_quant = new_like_quant
    def change_subfwd_quant(self,new_subfwd_quant):
        self.subfwd_quant = new_subfwd_quant

def handle_one_fwd(parent_name,item):
    '''
    tackle with each fwd and return a fwd instance
    :param parebt_name: the parent node user name
    :param item: the div html element that has the form div[action-type='feed_list_item']
    :return: a list that has the child node at the first. if the child node is special
            which means it does not has the href for his self about the event, then the
            list will also contain the grandson nodes following
    '''

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

    href_self = item.find_element_by_css_selector("a[node-type='feed_list_item_date']").get_attribute('href')


    fwd_text_span = item.find_element_by_css_selector("span[node-type='text']")
    # judge whether this forward is child forward, if it is not, return an empty list
    # else, tackle the info in it
    '''
    problem mark
    '''
    if "//@" in fwd_text_span.text:
        a_users_at = fwd_text_span.find_elements_by_css_selector("a[extra-data='type=atname']")
        before_delimeter_str = fwd_text_span.text.split("//@")[0]
        a_parent_location = before_delimeter_str.count('@')
        parent_name = a_users_at[a_parent_location].get_attribute('usercard').split("=")[1]
        # print(parent_name)
    fwd_instance = fwd_node(parent_name, usr_info, href_self, subfwd_like_quant, subfwd_quant)

    return fwd_instance

def handle_one_page(parent_name,page_of_fwds):
    '''
    tackle with one page of fwds
    :param parent_name: parent name
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

    counter = 0
    # handle all forwards on this page
    for item in fwd_page_list:
        if counter%10 == 0:
            print("          begin to hanlde forward "+str(counter) +" on this page...")
        item_result = handle_one_fwd(parent_name,item)
        fwd_instances_list.append(item_result)
        counter += 1

    return fwd_instances_list

def handle_one_web(source_web):
    '''
    the function to handle a source web that contains the original event
    :param source_web:
    :return: tuple(root_usr,fwd_list), which root_usr is a fwd_node instance of the root user and
            fwd_list is the list of all fwds
    '''
    print("Begin to handle "+source_web)

    options = webdriver.ChromeOptions()
    options.add_argument('-headless')
    options.add_argument('--disable-gpu')
    browser = webdriver.Chrome(executable_path='./chromedriver',chrome_options=options)


    #get the page source
    browser.get(source_web)
    browser.implicitly_wait(TIME_OUT)

    #find the button for forward details and then click
    fwd_click_items = browser.find_element_by_class_name('WB_handle')
    fwd_click_item = fwd_click_items.find_element_by_css_selector("a[action-type='fl_forward']")

    fwd_quant = int(fwd_click_item.find_elements_by_tag_name('em')[1].text)
    like_item = fwd_click_items.find_element_by_css_selector("a[action-type='fl_forward']")
    like_quant = int(like_item.find_elements_by_tag_name('em')[1].text)

    fwd_click_item.click()

    #find the root user name
    src_info_div = browser.find_element_by_css_selector("div[class='WB_info']")
    a_info = src_info_div.find_element_by_tag_name('a')
    root_id = a_info.get_attribute('usercard').split("&")[0].split("=")[1]
    root_name = a_info.text
    root_user_info = {
        'usr_name': root_name,
        'usr_id': root_id,
        'usr_blog': a_info.get_attribute('href')
    }


    counter = 0
    fwds_list = []
    while(1):
        #wait for render
        time.sleep(WAIT_RENDER)
        # get the list of forwards
        fwd_page_css_slecct = "div[class='list_ul'][node-type='feed_list']"
        fwd_page = browser.find_element_by_css_selector(fwd_page_css_slecct)

        print("     Begin to handle page " + str(counter) + "...")
        #get the list of forwards on this page
        result = handle_one_page(root_name,fwd_page)

        #whethter this is a empty page
        if result == 1:
            break
        #conbine result of this page with previous pages
        fwds_list = fwds_list + result

        try:
            # find the button to next page
            page_div = browser.find_element_by_class_name('W_pages')
            next_page_button = page_div.find_element_by_partial_link_text(u'下一页')
        except Exception as e:
            print("All pages has been handled.")
            break
        try:
            '''drag into view and then click the  button'''
            intoview_helper = browser.find_element_by_css_selector("img[alt='二维码']")
            browser.execute_script("arguments[0].scrollIntoView();", intoview_helper)
            # time.sleep(WAIT_RENDER)
            # wait until it's clickable
            wait = WebDriverWait(browser, TIME_OUT)
            wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'W_pages')))
            next_page_button.click()
            counter += 1
        except Exception as e:
            time.sleep(TIME_OUT)
            next_page_button.click()
            counter += 1
    # close the browser
    browser.delete_all_cookies()
    browser.close()

    root_user = fwd_node("Root",root_user_info,source_web,like_quant,fwd_quant)

    return (root_user,fwds_list)


# with open('./NBA.pkl','wb') as fp:
#     pickle.dump(fwds_list,fp,pickle.HIGHEST_PROTOCOL)
