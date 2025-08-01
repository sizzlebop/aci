from abc import ABC, abstractmethod

from aci.common.db.sql_models import LinkedAccount
from aci.common.exceptions import NoImplementationFound
from aci.common.logging_setup import get_logger
from aci.common.schemas.function import FunctionExecutionResult
from aci.common.schemas.security_scheme import (
    APIKeyScheme,
    APIKeySchemeCredentials,
    NoAuthScheme,
    NoAuthSchemeCredentials,
    OAuth2Scheme,
    OAuth2SchemeCredentials,
)

logger = get_logger(__name__)


class AppConnectorBase(ABC):
    """
    Base class for all app connectors.
    """

    # Note: security_scheme might not be necessary in most cases because we probably use some sdks
    # that handles credentials differently per App. It can be useful if inside the connector we still
    # need to construct the raw http request object.
    def __init__(
        self,
        linked_account: LinkedAccount,
        security_scheme: OAuth2Scheme | APIKeyScheme | NoAuthScheme,
        security_credentials: OAuth2SchemeCredentials
        | APIKeySchemeCredentials
        | NoAuthSchemeCredentials,
    ):
        self.linked_account = linked_account
        self.security_scheme = security_scheme
        self.security_credentials = security_credentials

    @abstractmethod
    def _before_execute(self) -> None:
        """
        This method is called in the beginning of the execute method.
        """
        pass

    def execute(self, method_name: str, function_input: dict) -> FunctionExecutionResult:
        """
        This method is the main entry point for executing a function.
        """
        logger.info(
            f"Executing via connector, method_name={method_name}, "
            f"class_name={self.__class__.__name__}"
        )
        self._before_execute()
        method = getattr(self, method_name, None)
        if not method:
            logger.error(
                f"Method not found, method_name={method_name}, class_name={self.__class__.__name__}"
            )
            raise NoImplementationFound(
                f"Method={method_name} not found in class={self.__class__.__name__}"
            )

        try:
            logger.info(
                f"Executing method, method_name={method_name}, class_name={self.__class__.__name__}"
            )
            result = method(**function_input)
            return FunctionExecutionResult(success=True, data=result)
        except Exception as e:
            logger.exception(
                f"Error executing method, method_name={method_name}, "
                f"class_name={self.__class__.__name__}, error={e}"
            )
            return FunctionExecutionResult(success=False, error=str(e))
