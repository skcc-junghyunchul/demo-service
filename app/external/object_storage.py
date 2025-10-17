import boto3
import json
from app.api.v1.multi_resource import set_multi_resource, get_multi_resource, update_multi_resource, delete_multi_resource
from app.enums.storage_resource import StorageType
from app.enums.bucket_resource import BucketType
from app import logger
import botocore.config
import io
from botocore.exceptions import ClientError
import config
from config import multi_tenant_resource


async def download_object_to_stream(company_code, object_name, local_file_path):
    try:
        if company_code in StorageType.__members__:
            resource_name = StorageType[company_code].value
        else:
            raise ValueError(f"Invalid company_code: {company_code}")

        # llm_resource_value = get_multi_resource(resource_name)
        llm_resource_value = multi_tenant_resource[resource_name]
        resource_value_dict = json.loads(llm_resource_value['resource_value'])

        service_name = resource_value_dict.get('service_name')
        endpoint_url = resource_value_dict.get('endpoint_url')
        region_name = resource_value_dict.get('region_name')
        access_key = resource_value_dict.get('access_key')
        secret_key = resource_value_dict.get('secret_key')
        bucket_name = resource_value_dict.get('bucket_name')

        # logger.info(f"S3 Config - Service: {service_name}, Endpoint: {endpoint_url}, Region: {region_name}, Bucket: {bucket_name}",extra={"tenant":company_code})
        # logger.info(f"Downloading object: {object_name} -> {local_file_path}",extra={"tenant":company_code})

        s3 = boto3.client(
            service_name,
            endpoint_url=endpoint_url,
            region_name=region_name,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
            # verify=False
        )

        # 객체 존재 여부 확인
        try:
            s3.head_object(Bucket=bucket_name, Key=object_name)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.error(f"Object not found in S3: {bucket_name}/{object_name}",extra={"tenant":company_code})
                raise FileNotFoundError(f"Object not found: {object_name}")
            else:
                logger.error(f"Error checking object existence: {str(e)}",extra={"tenant":company_code})
                raise

        file_obj = io.BytesIO()
        s3.download_fileobj(bucket_name, object_name, file_obj)
        file_obj.seek(0)

        mime_type = "application/octet-stream"
        return file_obj.read(), mime_type

    except Exception as e:
        logger.exception(f"Failed to download object: {object_name}. Reason: {str(e)}",extra={"tenant":company_code})
        raise

    
    # object storage 샘플 접속정보
    # service_name = 's3'
    # endpoint_url = 'https://kr.object.ncloudstorage.com'
    # region_name = 'kr-standard'
    # access_key = 'ncp_iam_BPAMKR2BJFiK2BFn1o6p'
    # secret_key = 'ncp_iam_BPKMKR7yhS1hSsNmnSVwgg8KSCQ9j4a7iC'
    # bucket_name = 'ithd-test'
    # object_name = 'DYWT_v1.1_20241120.pdf'
    # local_file_path = '/tmp/DYWT_v1.1_20241120.pdf'
    
    
    
async def create_bucket(company_code):
    
    try:
        if company_code in BucketType.__members__:
            bucket_name = BucketType[company_code].value
        else:
            raise ValueError(f"Invalid company_code: {company_code}")
            
        # llm_resource_value = get_multi_resource("ihd_chatbot_backend_default_object_storage")
        llm_resource_value = multi_tenant_resource["ihd_chatbot_backend_default_object_storage"]
        resource_value_dict = json.loads(llm_resource_value['resource_value'])

        service_name = resource_value_dict.get('service_name')
        endpoint_url = resource_value_dict.get('endpoint_url')
        region_name = resource_value_dict.get('region_name')
        access_key = resource_value_dict.get('access_key')
        secret_key = resource_value_dict.get('secret_key')
        
        
        s3 = boto3.client(service_name, endpoint_url=endpoint_url, aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key)

        s3.create_bucket(Bucket=bucket_name)
        
    except Exception as e:
        logger.exception(f"Failed to create bucket: {bucket_name}. Reason: {str(e)}",extra={"tenant":company_code})
        raise


async def delete_bucket(company_code):
    
    try:
        if company_code in BucketType.__members__:
            bucket_name = BucketType[company_code].value
        else:
            raise ValueError(f"Invalid company_code: {company_code}")
            
        # llm_resource_value = get_multi_resource("ihd_chatbot_backend_default_object_storage")
        llm_resource_value = multi_tenant_resource["ihd_chatbot_backend_default_object_storage"]
        resource_value_dict = json.loads(llm_resource_value['resource_value'])

        service_name = resource_value_dict.get('service_name')
        endpoint_url = resource_value_dict.get('endpoint_url')
        region_name = resource_value_dict.get('region_name')
        access_key = resource_value_dict.get('access_key')
        secret_key = resource_value_dict.get('secret_key')
        
        
        s3 = boto3.client(service_name, endpoint_url=endpoint_url, aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key)

        s3.delete_bucket(Bucket=bucket_name)
        
    except Exception as e:
        logger.exception(f"Failed to create bucket: {bucket_name}. Reason: {str(e)}",extra={"tenant":company_code})
        raise
    

async def upload_file(company_code, object_name, local_file_path):

    try:
        if company_code in StorageType.__members__:
            resource_name = StorageType[company_code].value
        else:
            raise ValueError(f"Invalid company_code: {company_code}")

        # llm_resource_value = get_multi_resource(resource_name)
        llm_resource_value = multi_tenant_resource[resource_name]
        resource_value_dict = json.loads(llm_resource_value['resource_value'])

        service_name = resource_value_dict.get('service_name')
        endpoint_url = resource_value_dict.get('endpoint_url')
        region_name = resource_value_dict.get('region_name')
        access_key = resource_value_dict.get('access_key')
        secret_key = resource_value_dict.get('secret_key')
        bucket_name = resource_value_dict.get('bucket_name')


        s3 = boto3.client(service_name, endpoint_url=endpoint_url, aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key)

        # bucket_name = 'sample-bucket'

        # create folder
        # object_name = 'sample-folder/'

        # s3.put_object(Bucket=bucket_name, Key=object_name)

        # upload file
        s3.upload_file(local_file_path, bucket_name, object_name)

    except Exception as e:
        logger.exception(f"Failed to upload file: {object_name}. Reason: {str(e)}",extra={"tenant":company_code})
        raise
    