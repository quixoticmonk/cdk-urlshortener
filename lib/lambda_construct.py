from aws_cdk import (core as cdk, aws_lambda as _lambda, aws_rds as rds)

from aws_cdk.core import Duration

from aws_cdk.aws_lambda import (
    Runtime,
    Code,
    Function,
    Tracing,
)


class LambdaConstruct(cdk.Construct):
    def __init__(self, scope: cdk.Construct, construct_id: str,
                 lambda_context: str, **kwargs) -> None:
        super().__init__(scope, construct_id)

        fn = dict(self.node.try_get_context(lambda_context))

        rds.DatabaseInstance.from_database_instance_attributes()

        lambda_fn = Function(
            self,
            fn["fn_name"],
            function_name=fn["fn_name"],
            runtime=Runtime.PYTHON_3_8,
            handler=fn["fn_handler"],
            code=Code.from_asset(fn["fn_path"]),
            tracing=Tracing.ACTIVE,
            current_version_options={
                "removal_policy": cdk.RemovalPolicy.RETAIN
            },
            retry_attempts=fn["fn_retry_attempts"],
            timeout=Duration.seconds(fn["fn_timeout"]),
            reserved_concurrent_executions=fn["fn_reserved_concurrency"])

        lambda_fn_alias = lambda_fn.current_version.add_alias(fn["fn_alias"])

        # # Outputs

        cdk.CfnOutput(self,
                      fn["fn_name"] + 'Arn',
                      value=lambda_fn.function_arn)

        self._function = lambda_fn
        self._function_alias = lambda_fn_alias

    @property
    def main_function(self) -> _lambda.Function:
        return self._function

    @property
    def main_function_alias(self) -> _lambda.IAlias:
        return self._function_alias
