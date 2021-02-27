import os

from .configuration import Configuration
from .electricity_reporter import ElectricityReporter, PowerReportType

def lambda_handler(event, context):
    """Lambda function reacting to EventBridge events

    Parameters
    ----------
    event: dict, required
        Event Bridge Scheduled Events Format

        Event doc: https://docs.aws.amazon.com/eventbridge/latest/userguide/event-types.html#schedule-event-type

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    """
    print(os.environ.get('RUN_MODE'))
    dry_run = os.environ.get('RUN_MODE') == 'test'
    print(f'Running in {"dry run" if dry_run else "production"} mode')

    config = Configuration()

    devices_like = os.environ.get('DEVICES_LIKE')
    if not devices_like:
        print(f'Need to specify devices')
        return

    report_offset = None
    report_type = None
    report_type_name = os.environ.get('MEASURE_CADENCE')
    offset = os.environ.get('MEASURE_OFFSET')
    if report_type_name == PowerReportType.current.name:
        report_type = PowerReportType.current
        if offset:
            print(f'WARNING: offset value {offset} will not be used for report type: {report_type_name}')
    elif report_type_name == PowerReportType.day.name:
        report_type = PowerReportType.day
        if not offset or int(offset) < 2 or int(offset) > 30:
            print(f'Measure offset is not a valid value. Must be 2 <= Offset <= 30')
            return
        report_offset = int(offset)
    else:
        print(f'Report "{report_type_name}" not recognized')
        print(f'Options for report include: {[PowerReportType.current.name, PowerReportType.day.name]}')
        return

    reporter = ElectricityReporter(
        tplink_kasa_config=config.tplink_kasa, 
        newrelic_config=config.newrelic,
        report_type=report_type, 
        report_offset=report_offset, 
        test_mode=dry_run
    )
    reporter.get_and_report_device_data(devices_like)

    # We got here successfully!
    return True
