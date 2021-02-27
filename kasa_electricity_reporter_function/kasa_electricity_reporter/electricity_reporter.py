import json
from datetime import datetime, timedelta
from enum import Enum
import collections

from tplinkcloud import TPLinkDeviceManager
from newrelic import NewRelicInsightsApi

class PowerReportType(Enum):
    current = 1
    day = 2
    month = 3

    def __str__(self):
        return self.name

class ElectricityReporter:

    def __init__(
        self, 
        tplink_kasa_config, 
        newrelic_config,
        report_type, 
        report_offset=None, 
        test_mode=True
    ):
        self.report_type = report_type
        self.report_offset = report_offset
        self.test_mode = test_mode
        self.MAX_DEVICE_DATA_GATHER_ATTEMPTS = 3
        self.MAX_DEVICE_DATA_REPORT_ATTEMPTS = 3

        self._device_manager = TPLinkDeviceManager(
            tplink_kasa_config.username, 
            tplink_kasa_config.password, 
            tplink_cloud_api_host=tplink_kasa_config.api_url
        )
        self._newrelic_api = NewRelicInsightsApi(
            newrelic_config.account_id,
            newrelic_config.insights.insert_api_key,
            query_api_url=newrelic_config.insights.query_api_url,
            insert_api_url=newrelic_config.insights.insert_api_url,
            verbose=True
        )

    def get_and_report_device_data(self, devices_like=None):
        if devices_like:
            devices = self._device_manager.find_devices(devices_like)
            print(f'Found {len(devices)} TP Link devices matching the search for devices like: "{devices_like}"')
        else:
            devices = self._device_manager.get_devices()
            print(f'Found {len(devices)} TP Link devices')
        
        for device in devices:

            data = None
            data_fetch_attempts = 0
            while not data and data_fetch_attempts < self.MAX_DEVICE_DATA_GATHER_ATTEMPTS:
                data, all_data = self._get_device_data(device)
                data_fetch_attempts += 1

            if not data:
                print(f'Failed to get "{self.report_type.name}" data after {self.MAX_DEVICE_DATA_GATHER_ATTEMPTS} '\
                    f'attempts for device: {device.get_alias()}')
                continue            
            print(f'Finished getting "{self.report_type.name}" data for device: {device.get_alias()}')

            report_result = None
            report_attempts = 0
            while not report_result and report_attempts < self.MAX_DEVICE_DATA_REPORT_ATTEMPTS:
                report_result = self._report_device_data(device, data)
                if all_data:
                    self._report_device_all_data(device, all_data)
                report_attempts += 1
            
            if not report_result:
                print(f'Failed to report "{self.report_type.name}" data after {self.MAX_DEVICE_DATA_REPORT_ATTEMPTS} '\
                    f'attempts for device: {device.get_alias()}')
                continue
            print(f'Finished reporting "{self.report_type.name}" data for device: {device.get_alias()}')
            print()

    def _get_device_data(self, device):
        print(f'Getting "{self.report_type.name}" data for device: {device.get_alias()}')
        if self.report_type == PowerReportType.current:
            return (device.get_power_usage_realtime(), None)
        elif self.report_type == PowerReportType.day:
            date = datetime.today() - timedelta(days=self.report_offset)
            past_usage_data = device.get_power_usage_day(date.year, date.month)
            for day_usage in past_usage_data:
                if day_usage.day == date.day and day_usage.month == date.month and day_usage.year == date.year:
                    return (day_usage, past_usage_data)
            return (None, None)
        elif self.report_type == PowerReportType.month:
            today = datetime.today()
            if today.month > self.report_offset:
                month = today.month - self.report_offset
                year = today.year
            elif today.month == self.report_offset:
                month = 12
                year = today.year - 1
            elif today.month < self.report_offset:
                month = 11 - (self.report_offset - today.month)
                year = today.year - 1
            past_usage_data = device.get_power_usage_month(year)
            for month_usage in past_usage_data:
                if month_usage.month == month and month_usage.year == year:
                    return (month_usage, past_usage_data)
            return (None, None)

    def _report_device_data(self, device, data):
        print(f'Reporting "{self.report_type.name}" data for device: {device.get_alias()}')
        insert_result = None
        event_type = None
        event = {
            'device_id': device.device_id,
            'model_type': device.model_type.name
        }
        if device.child_id:
            event['child_id'] = device.child_id
        event.update(json.loads(json.dumps(device.device_info, default=lambda x: x.__dict__)))
        event.update(json.loads(json.dumps(data, default=lambda x: x.__dict__)))

        if self.report_type == PowerReportType.current:
            event_type = 'TPLinkEMeterDevicePowerCurrent'
        elif self.report_type == PowerReportType.day:
            event_type = 'TPLinkEMeterDevicePowerDaySummary'
        elif self.report_type == PowerReportType.month:
            event_type = 'TPLinkEMeterDevicePowerMonthSummary'
        
        # If testing, don't report the actual event types
        if self.test_mode:
            event_type = f'Test{event_type}'

        insert_result = self._newrelic_api.insert_event(event_type, event, flatten=True)
        if not insert_result:
            print(f'Failed to insert {event_type} event with "{self.report_type.name}" data: '\
                f'{json.dumps(event, indent=2)}')
        else:
            print(f'Inserted {event_type} event')
        return insert_result

    def _report_device_all_data(self, device, all_data):
        print(f'Reporting "{self.report_type.name}" data for device: {device.get_alias()}')
        insert_result = None
        event_type = None
        event = {
            'device_id': device.device_id,
            'model_type': device.model_type.name
        }
        if device.child_id:
            event['child_id'] = device.child_id
        event.update(json.loads(json.dumps(device.device_info, default=lambda x: x.__dict__)))


        if self.report_type == PowerReportType.day:
            event_type = 'TPLinkEMeterDevicePowerDayAllSummary'
            for data in all_data:
                event[f'wh.{data.year}.{data.month}.{data.day}'] = float(data.energy_wh)
        elif self.report_type == PowerReportType.month:
            event_type = 'TPLinkEMeterDevicePowerMonthAllSummary'
            for data in all_data:
                event[f'wh.{data.year}.{data.month}'] = float(data.energy_wh)
        
        # If testing, don't report the actual event types
        if self.test_mode:
            event_type = f'Test{event_type}'

        insert_result = self._newrelic_api.insert_event(event_type, event, flatten=True)
        if not insert_result:
            print(f'Failed to insert {event_type} event with "{self.report_type.name}" data: '\
                f'{json.dumps(event, indent=2)}')
        else:
            print(f'Inserted {event_type} event')
        return insert_result
