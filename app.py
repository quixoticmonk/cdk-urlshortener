#!/usr/bin/env python3

from aws_cdk import core as cdk
from lib.apigw_construct import GatewayConstruct
from lib.lambda_construct import LambdaConstruct
from lib.dynamo_construct import DbConstruct


class AppStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        _fn1 = LambdaConstruct(self, "createshortUrl", "lambda1")
        _fn2 = LambdaConstruct(self, "getUrl", "lambda2")
        # GatewayConstruct()
        # DbConstruct()


app = cdk.App()
AppStack(app, "cdkinit")

app.synth()
