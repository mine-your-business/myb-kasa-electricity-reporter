import pytest
import boto3
import botocore
import os

@pytest.fixture(scope='module')
def lambda_client():
    # Create Lambda SDK client to connect to appropriate Lambda endpoint
    return boto3.client('lambda',
        region_name=os.environ.get('AWS_SAM_REGION'),
        endpoint_url="http://127.0.0.1:3001",
        use_ssl=False,
        verify=False,
        config=botocore.client.Config(
            signature_version=botocore.UNSIGNED,
            read_timeout=60,
            retries={'max_attempts': 0},
        )
    )

@pytest.mark.usefixtures('lambda_client')
class TestKasaCurrentElecFn(object):

    def test_function_returns_success(self, lambda_client):

        # Invoke your Lambda function as you normally usually do. The function will run
        # locally if it is configured to do so
        response = lambda_client.invoke(FunctionName="KasaCurrentElecFn")

        # Verify the response
        assert response.get('FunctionError') is None
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200
        assert response.get('StatusCode') == 200
        assert response.get('Payload') is not None
        assert bool(response['Payload'].read()) is True


@pytest.mark.usefixtures('lambda_client')
class TestKasaDailyElecFn(object):

    def test_function_returns_success(self, lambda_client):

        # Invoke your Lambda function as you normally usually do. The function will run
        # locally if it is configured to do so
        response = lambda_client.invoke(FunctionName="KasaDailyElecFn")

        # Verify the response
        assert response.get('FunctionError') is None
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200
        assert response.get('StatusCode') == 200
        assert response.get('Payload') is not None
        assert bool(response['Payload'].read()) is True
