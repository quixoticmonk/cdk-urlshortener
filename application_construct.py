from aws_cdk import (core as cdk, aws_lambda as _lambda)




class AppConstruct(cdk.Construct):
    def __init__(self, scope: cdk.Construct, construct_id: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id)
