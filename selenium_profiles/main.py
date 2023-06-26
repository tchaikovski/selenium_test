from selenium.webdriver import ChromeOptions
from selenium import webdriver
from collections import defaultdict
import requests

user_agent_new = {
    'options': {'gpu': False, 'window_size': {'x': 384, 'y': 700}},
    'cdp': {'touch': True, 'maxtouchpoints': 10, 'cores': 8,
            'patch_version': True,
            'emulation': {'mobile': True, 'width': 384, 'height': 700,
                          'deviceScaleFactor': 4,
                          'screenOrientation': {'type': 'portraitPrimary',
                                                'angle': 0}},
            'useragent': {'platform': 'Linux aarch64',
                          'acceptLanguage': 'en-US',
                          'userAgent': 'Mozilla/5.0 (Linux; Android 11; HD1913) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Mobile Safari/537.36',
                          'userAgentMetadata': {'brands': [
                              {'brand': 'Google Chrome', 'version': '105'},
                              {'brand': 'Not)A;Brand', 'version': '8'},
                              {'brand': 'Chromium', 'version': '105'}],
                              'fullVersionList': [
                                  {'brand': 'Google Chrome',
                                   'version': '105.0.5195.136'},
                                  {'brand': 'Not)A;Brand',
                                   'version': '8.0.0.0'},
                                  {'brand': 'Chromium',
                                   'version': '105.0.5195.136'}],
                              'fullVersion': '105.0.5195.136',
                              'platform': 'Android',
                              'platformVersion': '11.0.0',
                              'architecture': '',
                              'model': 'HD1913',
                              'mobile': True, 'bitness': '',
                              'wow64': False}}}}


def return_profile(user_agent_new):
    profile = defaultdict(lambda: None)
    profile.update(user_agent_new)
    return profile  # yet supported: "Android", "Windows"


profile = return_profile(user_agent_new)

#


#
class Chrome:
    # noinspection PyDefaultArgument
    def __init__(
            self, profile: dict = None, chrome_binary: str = None,
            executable_path: str = None,
            options=None, dublicate_policy: str = "warn-add",
            safe_dublicates: list = ["--add-extension"],
            uc_driver: bool or None = None,
            # seleniumwire_options: dict or bool or None = None
            ):

        from utils.cdp_tools import cdp_tools
        from utils.profiles import options as options_handler

        # initial attributes
        self.cdp = None
        self._started = None
        self.kwargs = {}

        self.uc_driver = uc_driver
        self.executable_path = executable_path
        self.cdp_tools = cdp_tools
        self.chrome_binary = chrome_binary
        self.profile = defaultdict(lambda: None)
        self.profile.update(profile)
        print(self.profile)
        self.driver = webdriver.Chrome
        if not options:
            options = webdriver.ChromeOptions()

        # options-manager
        self.options = options_handler(options, self.profile["options"],
                                       dublicate_policy=dublicate_policy,
                                       safe_dublicates=safe_dublicates)
        # add options to kwargs
        self.kwargs.update({"options": self.options.Options})

    def start(self):

        if self._started:
            raise TypeError("webdriver.Chrome() object can't be re-used")

        # Actual start of chrome
        self.driver = self.driver(**self.kwargs)
        self._started = True

        # cdp tools

        self.cdp_tools = self.cdp_tools(self.driver)

        self.cdp_tools.evaluate_on_document_identifiers.update(
            {1:  # we know that it is there:)
                 """(function () {window.cdc_adoQpoasnfa76pfcZLmcfl_Array = window.Array;
                 window.cdc_adoQpoasnfa76pfcZLmcfl_Object = window.Object;
                 window.cdc_adoQpoasnfa76pfcZLmcfl_Promise = window.Promise;
                 window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy = window.Proxy;
                 window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol = window.Symbol;
                 }) ();"""})

        from utils.profiles import cdp as cdp_handler
        self.cdp = cdp_handler(self.driver, self.cdp_tools)
        self.cdp.apply(cdp_profile=self.profile["cdp"])
        self.add_funcs_to_driver()

        # Return actual driver
        return self.driver

    def add_funcs_to_driver(self):

        # add selenium-profiles utils to driver
        class utils(object):
            pass

            def apply(self, profile: dict):
                """
                apply options after driver allready started
                :param profile: selenium-profiles options
                """
                from selenium_profiles.utils.utils import valid_key
                valid_key(profile.keys(), ["cdp", "options"],
                          "profile (selenium-profiles)")
                if "options" in profile.keys():
                    warnings.warn(
                        'profile["options"] can\'t be applied when driver allready started')
                if "cdp" in profile.keys():
                    # noinspection PyUnresolvedReferences
                    self.cdp.apply(profile["cdp"])

        utils = utils()

        # our profile
        utils.__setattr__("profile", self.profile)

        # add selenium-interceptor
        # from selenium_interceptor.interceptor import cdp_listener
        # utils.__setattr__("cdp_listener", cdp_listener(driver=self.driver))

        # add my functions
        utils.__setattr__("get_profile", self.get_profile)
        utils.__setattr__("export_profile", self.export_profile)
        utils.__setattr__("get_profile", self.get_profile)
        utils.__setattr__("cdp", self.cdp)

        # from utils import actions, \
        #     TouchActionChain

        # requests.fetch
        # requests = requests(self.driver)
        # utils.__setattr__("fetch", requests.fetch)

        # actions = actions(self.driver)
        # actions.__setattr__("TouchActionChain", TouchActionChain)
        # utils.__setattr__("actions", actions)

        self.driver.profiles = utils

        # patch driver functions
        self.driver.get_cookies = self.cdp_tools.get_cookies
        self.driver.add_cookie = self.cdp_tools.add_cookie
        self.driver.get_cookie = self.cdp_tools.get_cookie
        self.driver.delete_cookie = self.cdp_tools.delete_cookie
        self.driver.delete_all_cookies = self.cdp_tools.delete_all_cookies

    def export_profile(self, to_path=None):
        import shutil
        self.ensure_started()

        if not to_path:  # default path
            from selenium_profiles.utils.utils import sel_profiles_path
            to_path = sel_profiles_path() + "files/user_dir"

        # noinspection PyUnresolvedReferences
        shutil.copytree(self.driver.user_data_dir, to_path)

    def get_profile(self):
        from selenium_profiles.utils.utils import read
        self.ensure_started()

        js = read('utils/js/export_profile.js', sel_root=True)

        # noinspection PyArgumentList
        return self.driver.execute_async_script(js)

    def ensure_started(self):
        if not self._started:
            raise TypeError("driver needs to be started first :)")



options = ChromeOptions()
mydriver = Chrome(profile, options=options, uc_driver=False)

driver = mydriver.start()
# get url
driver.get('https://user-agent-client-hints.glitch.me/')  # test fingerprint

input("Press ENTER to exit: ")
driver.quit()  # Execute on the End!
