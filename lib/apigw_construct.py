import textwrap
from aws_cdk import (
    core,
    aws_lambda as _lambda,
    aws_apigateway as _api_gw,
    aws_logs as _logs,
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

        gw = dict(self.node.try_get_context(gw_context))

        # # api gateway log groups

        api_log_group = _logs.LogGroup(
            self,
            gw["gw_log_group_name"],
            log_group_name="/aws/apigateway/" + gw["gw_log_group_name"],
            retention=LOG_RETENTION_PERIOD,
            removal_policy=core.RemovalPolicy.DESTROY)

        # # api gateway to handle post requests
        gateway = _api_gw.RestApi(
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
                    EndpointType.REGIONAL if gw["gw_endpoint_type"]
                                             == "regional" else EndpointType.EDGE
                ]
            },
            deploy=True,
            cloud_watch_role=True,
            description=gw["gw_description"],
        )

        _create_response_model = gateway.add_model(
            "CreateResponseModel",
            content_type="application/json",
            model_name="CreateResponseModel",
            schema={
                "schema": JsonSchemaVersion.DRAFT4,
                "title": "CreateResponseModel",
                "type": JsonSchemaType.OBJECT,
                "properties": {
                    "short_url": {
                        "type": JsonSchemaType.STRING
                    }
                }

            }
        )

        _retrieve_response_model = gateway.add_model(
            "RetrieveResponseModel",
            model_name="RetrieveResponseModel",
            schema={
                "schema": JsonSchemaVersion.DRAFT4,
                "title": "RetrieveResponseModel",
                "type": JsonSchemaType.OBJECT,
                "properties": {
                    "long_url": {
                        "type": JsonSchemaType.STRING
                    },
                    "status_code": {
                        "type": JsonSchemaType.INTEGER
                    }
                }

            }
        )

        passthrough_behavior = PassthroughBehavior.WHEN_NO_TEMPLATES

        _create_response_template = textwrap.dedent(
            """
                    #set($inputRoot = $input.path('$'))
                    {
                             "short_id" : $inputRoot.short_id    
                    }
                    """
        )

        _retrieve_response_template = textwrap.dedent(
            """
                    #set($inputRoot = $input.path('$'))
                    {
                             "long_url" : $inputRoot.long_url     
                    }
                    """
        )

        _create_lambda_integ = _api_gw.LambdaIntegration(
            lambda_fn_alias,
            proxy=False,
            passthrough_behavior=passthrough_behavior,
            integration_responses=[
                _api_gw.IntegrationResponse(
                    status_code="200",
                    response_templates={
                        "application/json": _create_response_template
                    }
                )
            ],
            request_templates={
                "application/json": textwrap.dedent(
                    """
                    #set($inputRoot = $input.path('$'))
                    {
                        "body": {
                            "long_url" : "$inputRoot.long_url"    
                        }
                    }
                    """
                )
            }
        )

        _retrieve_lambda_integ = _api_gw.LambdaIntegration(
            lambda_fn_alias2,
            proxy=False,
            passthrough_behavior=passthrough_behavior,
            integration_responses=[
                _api_gw.IntegrationResponse(
                    status_code="200",
                    response_templates={
                        "application/json": _retrieve_response_template
                    }
                )
            ],
            request_templates={
                "application/json": textwrap.dedent(
                    """
                    {
                        "short_id": "$input.params('short_id')"
                    }
                    """
                )
            }
        )

        _create_resource = gateway.root.add_resource("create")

        _create_resource.add_method(
            "POST",
            _create_lambda_integ,
            api_key_required=False,
            method_responses=[
                MethodResponse(
                    status_code='200',
                    response_models={'application/json': _create_response_model}
                ),
                MethodResponse(
                    status_code='400'
                )
            ]
        )

        _retrieve_resource = gateway.root.add_resource("{short_id}")

        _retrieve_resource.add_method(
            "GET",
            _retrieve_lambda_integ,
            api_key_required=False,
            method_responses=[
                MethodResponse(
                    status_code='301',
                    response_models={'application/json': _retrieve_response_model}
                ),
                MethodResponse(
                    status_code='400'
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

        # # Outputs

        core.CfnOutput(self, "ApiGwUrl", value=gateway.url)

        core.CfnOutput(self,
                       "ApiGWLogGroup",
                       value=api_log_group.log_group_name)

        self.apigw = gateway

    @property
    def main_api(self) -> _api_gw.IRestApi:
        return self.apigw
