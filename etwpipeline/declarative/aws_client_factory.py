from uuid import uuid4

import boto3


class AWSClientFactory:
    def __init__(
        self,
        assume_role_arn=None,
        assume_role_external_id=None,
        **boto_extra_args,
    ):
        self.extra_args = boto_extra_args.copy() if boto_extra_args else {}
        if assume_role_arn:
            sts_client = boto3.client("sts")
            assume_role_args = {
                "RoleArn": assume_role_arn,
                "RoleSessionName": str(uuid4()),
            }
            if assume_role_external_id:
                assume_role_args["ExternalId"] = assume_role_external_id
            credentials = sts_client.assume_role(**assume_role_args)["Credentials"]
            self.extra_args["aws_access_key_id"] = credentials["AccessKeyId"]
            self.extra_args["aws_secret_access_key"] = credentials["SecretAccessKey"]
            self.extra_args["aws_session_token"] = credentials["SessionToken"]

    def make_client(self, service_name):
        session = boto3.Session(**self.extra_args)
        return session.client(service_name)
