#!/usr/bin/env python3

from aws_cdk import core as cdk
from lib.apigw_construct import GatewayConstruct
from lib.lambda_construct import LambdaConstruct
from lib.dynamo_construct import DbConstruct
from application_construct import AppConstruct

from cdk_watchful import Watchful


class AppStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        wf = Watchful(self, 'watchful')
        wf.watch_scope(self)

        _fn1 = LambdaConstruct(self, "createshortUrl", "lambda1")
        _fn2 = LambdaConstruct(self, "getUrl", "lambda2")
        GatewayConstruct(self, "urlshortenerGateway", "dev", _fn1.main_function_alias, _fn2.main_function_alias, "gw")
        _db = DbConstruct(self, "urltable", "db")
        AppConstruct(self, "appConstruct", _fn1.main_function,
                     _fn2.main_function, _db.main_table)


app = cdk.App()
AppStack(app, "app")

app.synth()
