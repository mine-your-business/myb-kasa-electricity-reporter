import os

class Configuration:

    def __init__(self, file_path=None):
        self.tplink_kasa = TPLinkKasa()
        self.newrelic = NewRelic()

class TPLinkKasa:

    def __init__(self):
        self.username = os.environ.get('TPLINK_KASA_USERNAME')
        self.password = os.environ.get('TPLINK_KASA_PASSWORD')
        self.api_url = os.environ.get('TPLINK_KASA_API_URL')

class NewRelicInsights:

    def __init__(self):
        self.insert_api_key = os.environ.get('NEWRELIC_INSIGHTS_INSERT_API_KEY')
        self.query_api_url = os.environ.get('NEWRELIC_INSIGHTS_QUERY_API_URL')
        self.insert_api_url = os.environ.get('NEWRELIC_INSIGHTS_INSERT_API_URL')

class NewRelic:

    def __init__(self):
        self.account_id = os.environ.get('NEWRELIC_ACCOUNT_ID')
        self.insights = NewRelicInsights()
