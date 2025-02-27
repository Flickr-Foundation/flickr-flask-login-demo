from typing import Any, Optional, Protocol

from flask.testing import FlaskClient

from app import User

class UserMixin(Protocol):
    @property
    def is_authenticated(self) -> bool: ...

class LoginManager:
    def __init__(self) -> None: ...
    def init_app(self, app: Any) -> None: ...
    def user_loader(self, callback: Any) -> Any: ...
    login_view: str

def login_user(
    user: Any,
    remember: Optional[bool] = None,
    duration: Optional[Any] = None,
    force: Optional[bool] = None,
) -> bool: ...
def logout_user() -> None: ...
def login_required(func: Any) -> Any: ...

current_user: User

class FlaskLoginClient(FlaskClient): ...
