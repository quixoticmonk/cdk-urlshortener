import textwrap
from aws_cdk import (
    core,
    aws_lambda as _lambda,
    aws_apigateway as _api_gw,
    aws_logs as _logs
)

from aws_cdk.aws_apigateway import (MethodLoggingLevel, EndpointType,
                                    AccessLogFormat, LogGroupLogDestination,
                                    JsonSchemaVersion, JsonSchemaType,
                                    MethodResponse, PassthroughBehavior)

LOG_INFO = MethodLoggingLevel.INFO
LOG_ERROR = MethodLoggingLevel.ERROR
LOG_RETENTION_PERIOD = _logs.RetentionDays.ONE_WEEK


class GatewayConstruct(core.Construct):
    def __init__(self, scope: core.Construct, construct_id: str, stage: str,
                 lambda_fn_alias: _lambda.IAlias, lambda_fn_alias2: _lambda.IAlias, gw_context: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id)


        _create_model_props = {
            "short_url": {
                "type": JsonSchemaType.STRING
            }
        }
        _retrieve_model_props = {
            "location": {
                "type": JsonSchemaType.STRING
            },
            "status_code": {
                "type": JsonSchemaType.INTEGER
            }
        }

        gw = dict(self.node.try_get_context(gw_context))
        api_log_group = self._create_api_log_group(gw)
        gateway = self._create_rest_api(api_log_group, gw, stage)
        _passthrough_behavior = PassthroughBehavior.WHEN_NO_TEMPLATES

        _create_response_model = self._create_response_model(
            gateway, "CreateResponseModel", _create_model_props)
        _retrieve_response_model = self._create_response_model(
            gateway, "RetrieveResponseModel", _retrieve_model_props)
        _create_response_template = self._create_response_template()

        _retrieve_response_template = self._create_retrieve_response_template()
        _create_request_template = self._create_request_template()
        _retrieve_request_template = self._retrieve_request_template()

        _create_lambda_integ = self._create_lambda_integration(lambda_fn_alias, _passthrough_behavior,
                                                               _create_response_template,
                                                               _create_request_template,
                                                               "200"
                                                               )
        _retrieve_lambda_integ = self._retrieve_lambda_integration(lambda_fn_alias2, _passthrough_behavior,
                                                                 _retrieve_response_template,
                                                                 _retrieve_request_template,
                                                                 "301"
                                                                 )

        _create_resource = gateway.root.add_resource("create")

        _create_resource.add_method(
            "POST",
            _create_lambda_integ,
            api_key_required=False,
            method_responses=[
                MethodResponse(
                    status_code='200',
                    response_models={
                        'application/json': _create_response_model}
                ),
                MethodResponse(
                    status_code='400'
                )
            ]
        )
        _retrieve_resource_root = gateway.root.add_resource("t")
        _retrieve_resource = _retrieve_resource_root.add_resource("{short_id}")

        _retrieve_resource.add_method(
            "GET",
            _retrieve_lambda_integ,
            api_key_required=False,
            method_responses=[
                MethodResponse(
                    status_code='301',
                    response_parameters={
                        'method.response.header.Location': True,
                        'proxy': True
                    },
                )
            ]
        )

        _create_resource.add_cors_preflight(
            allow_origins=[gw["gw_origins_cors"]],
            allow_methods=[gw["gw_origins_cors_method"]]
        )

        _retrieve_resource.add_cors_preflight(
            allow_origins=[gw["gw_origins_cors"]],
            allow_methods=[gw["gw_origins_cors_method"]]
        )

        core.CfnOutput(self, "ApiGwUrl", value=gateway.url)

        core.CfnOutput(self,
                       "ApiGWLogGroup",
                       value=api_log_group.log_group_name)

        self.apigw = gateway

    def _create_request_template(self):
        return textwrap.dedent(
            """
        #set($inputRoot = $input.path('$'))
        {
            "body": {
                "long_url" : "$inputRoot.long_url"    
            }
        }
        """
        )

    def _retrieve_request_template(self):
        return textwrap.dedent(
            """
            {
                "short_id": "$input.params('short_id')"
            }
            """
        )

    def _create_lambda_integration(self, lambda_fn_alias, _passthrough_behavior, _response_template, _request_template, _status_code):
        return _api_gw.LambdaIntegration(
            lambda_fn_alias,
            proxy=False,
            passthrough_behavior=_passthrough_behavior,
            integration_responses=[
                _api_gw.IntegrationResponse(
                    status_code=_status_code,
                    response_templates={
                        "application/json": _response_template
                    }
                )
            ],
            request_templates={
                "application/json": _request_template
            }
        )

    def _retrieve_lambda_integration(self, lambda_fn_alias, _passthrough_behavior, _response_template, _request_template, _status_code):
        return _api_gw.LambdaIntegration(
            lambda_fn_alias,
            proxy=False,
            passthrough_behavior=_passthrough_behavior,
            integration_responses=[
                _api_gw.IntegrationResponse(
                    status_code=_status_code,
                    response_parameters={
                        'method.response.header.Location': "integration.response.body.location"
                    }
                )
            ],
            request_templates={
                "application/json": _request_template
            },
            request_parameters={
                'proxy': "method.request.path.proxy"
            }
        )

    def _create_rest_api(self, api_log_group, gw, stage):
        return _api_gw.RestApi(
            self,
            gw["gw_name"],
            rest_api_name=gw["gw_name"],
            deploy_options={
                "description": gw["gw_stage_description"],
                "logging_level": LOG_INFO,
                "tracing_enabled": True,
                "stage_name": stage,
                "access_log_destination": LogGroupLogDestination(api_log_group),
                "access_log_format":
                    AccessLogFormat.json_with_standard_fields(caller=False,
                                                              http_method=True,
                                                              ip=True,
                                                              protocol=True,
                                                              request_time=True,
                                                              resource_path=True,
                                                              response_length=True,
                                                              status=True,
                                                              user=True),
                "metrics_enabled": True,
            },
            endpoint_configuration={
                "types": [
                    EndpointType.REGIONAL
                ]
            },
            deploy=True,
            cloud_watch_role=True,
            description=gw["gw_description"],
        )

    def _create_api_log_group(self, gw):
        return _logs.LogGroup(
            self,
            gw["gw_log_group_name"],
            log_group_name="/aws/apigateway/" + gw["gw_log_group_name"],
            retention=LOG_RETENTION_PERIOD,
            removal_policy=core.RemovalPolicy.DESTROY)

    def _create_response_model(self, gateway, model_name, props):
        return gateway.add_model(
            model_name,
            content_type="application/json",
            model_name=model_name,
            schema={
                "schema": JsonSchemaVersion.DRAFT4,
                "title": model_name,
                "type": JsonSchemaType.OBJECT,
                "properties": props

            }
        )

    @staticmethod
    def _create_response_template():
        return textwrap.dedent(
            """
                #set($inputRoot = $input.path('$'))
                {
                         "short_id" : "$inputRoot.short_id"    
                }
                """
        )

    @staticmethod
    def _create_retrieve_response_template():
        return textwrap.dedent(
            """
                #set($inputRoot = $input.path('$'))
                {
                         "location" : $inputRoot.location     
                }
                """
        )

    @property
    def main_api(self) -> _api_gw.IRestApi:
        return self.apigw
