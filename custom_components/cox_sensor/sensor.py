import logging

from datetime import datetime
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.util import Throttle


REQUIREMENTS = ['requests']

CONF_USERNAME="username"
CONF_PASSWORD="password"

ICON = 'mdi:cloud-braces'

url="https://idm.east.cox.net/idm/coxnetlogin"

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = datetime(hours=6) #timedelta

def setup_platform(hass, config, add_entities, discovery_info=None):
    username = str(config.get(CONF_USERNAME))
    password = str(config.get(CONF_PASSWORD))
    add_entities([cox_sensor(username, password, SCAN_INTERVAL)], True)

class cox_sensor(Entity):
    def __init__(self, username, password, interval):
        self._username = username
        self._password = password
        self.update = Throttle(interval)(self._update)

    def _update(self):
        import requests
        try:
            data = {
            'username': self._username,
            'password': self._password,
            'rememberme': 'true',
            'emaildomain': '@cox.net',
            'targetFN': 'COX.net',
            'onsuccess': 'https://www.cox.com/resaccount/home.cox',
            'post': 'Submit'
            }
            r = requests.Session()
            r.post(url, data=data, verify=False)
            r.get("https://www.cox.com/internet/mydatausage.cox")
            datausage = r.get("https://www.cox.com/internet/ajaxDataUsageJSON.ajax", verify=False)
            datausagejson = datausage.json()
            currentusage = datausagejson['modemDetails'][0]['dataUsed']['totalDataUsed'].replace("&#160;"," ")
            dataplan = datausagejson['modemDetails'][0]['dataPlan'].replace("&#160;"," ")
            serviceperiod = datausagejson['modemDetails'][0]['servicePeriod'].split('-')
            serviceend = datetime.strptime(serviceperiod[1], '%m/%d/%y')
            remainingdays = abs((datetime.today() - serviceend).days)
            lastupdatedbycox = datausagejson['modemDetails'][0]['lastUpdatedDate']
            self._state = currentusage
            self._attributes = {}
            self._attributes['dataplan'] = dataplan
            self._attributes['remaining_days'] = remainingdays
            self._attributes['service_end'] = serviceend
            self._attributes['last_update'] = lastupdatedbycox
        except Exception as err:
            _LOGGER.error(err)


    @property
    def name(self):
        name = "cox_sensor"
        return name

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return ICON

    @property
    def device_state_attributes(self):
        """Return the attributes of the sensor."""
        return self._attributes

    @property
    def should_poll(self):
        """Return the polling requirement for this sensor."""
        return True

