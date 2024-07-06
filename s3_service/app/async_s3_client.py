from aiobotocore.session import get_session
from botocore.exceptions import NoCredentialsError, ClientError
import logging
from contextlib import asynccontextmanager


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/app.log")
    ]
)
logger = logging.getLogger(__name__)

class AsyncS3Client:
    def __init__(self, endpoint_url, access_key, secret_key, bucket_name):
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        # self.region_name = region_name
        self.session = get_session()
        self.config = {
            "aws_access_key_id": self.access_key,
            "aws_secret_access_key": self.secret_key,
            "endpoint_url": self.endpoint_url,
            # "region_name": self.region_name,
        }

    @asynccontextmanager
    async def _get_s3_client(self):
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    async def upload_file(self, file_path, object_name):
        async with self._get_s3_client() as s3:
            try:
                with open(file_path, 'rb') as f:
                    await s3.put_object(
                        Bucket=self.bucket_name,
                        Key=object_name,
                        Body=f,
                    )
                logging.info(f"File {file_path} uploaded to {object_name} in bucket {self.bucket_name}")
                return {"status": "success", "message": f"File {object_name} uploaded successfully"}
            except NoCredentialsError:
                logging.error("Credentials not available")
                return {"status": "error", "message": "Credentials not available"}
            except ClientError as e:
                logging.error(f"Client error: {e}")
                return {"status": "error", "message": str(e)}
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                return {"status": "error", "message": str(e)}

    async def delete_file(self, object_name: str):
        async with self._get_s3_client() as s3:
            logging.info(f"started {object_name} deleted from bucket {self.bucket_name} for {self.endpoint_url}")
            try:
                await s3.delete_object(Bucket=self.bucket_name, Key=object_name)
                logging.info(f"File {object_name} deleted from bucket {self.bucket_name}")
                return {"status": "success", "message": f"File {object_name} deleted successfully"}
            except NoCredentialsError:
                logging.error("Credentials not available")
                return {"status": "error", "message": "Credentials not available"}
            except ClientError as e:
                logging.error(f"Client error: {e}")
                return {"status": "error", "message": str(e)}