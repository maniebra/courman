"""DRF-style mixins for the list/retrieve/create/update/destroy logic shared
by our simple resources (iam's users/roles/actions, courses).

A concrete view combines the mixins it needs with `GenericCrudView`, which
holds the repository functions + messages (DRF's `GenericAPIView` holding
`queryset`/`serializer_class`, roughly). Routers still register their own
endpoints explicitly - path, method, auth, response schema, and pagination
stay local to each app's views.py; only the action bodies are shared here.
"""

from collections.abc import Awaitable, Callable
from typing import Any, ClassVar

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Model
from ninja import Schema
from ninja.errors import HttpError


async def aget_or_404[T](coro: Awaitable[T], message: str = "Not found") -> T:
    """Await a repository call and turn its DoesNotExist into an HTTP 404."""
    try:
        return await coro
    except ObjectDoesNotExist:
        raise HttpError(404, message)


class GenericCrudView[ModelT: Model]:
    """Config a resource's CRUD mixins need. Set these as class attributes
    on a subclass, e.g. `get_fn = staticmethod(UserRepository.get_user)`.

    `ModelT` is a real generic parameter because it flows into the actual
    function signatures below (`get_fn` returns one, `delete_fn` takes one).
    `schema`/`create_schema`/`update_schema` are plain attrs instead of three
    more type parameters (DRF's `serializer_class`, roughly): the mixins only
    ever call `.dict()` on a payload and hand a model instance to a response
    schema, so nothing here is generic *over* the schema type - the router
    just needs the class to hand the schema back for `response=`.
    """

    schema: ClassVar[type[Schema]]
    create_schema: ClassVar[type[Schema]]
    update_schema: ClassVar[type[Schema]]

    list_fn: ClassVar[Callable[[], Any]]
    get_fn: ClassVar[Callable[[int], Awaitable[ModelT]]]
    create_fn: ClassVar[Callable[..., Awaitable[ModelT]]]
    update_fn: ClassVar[Callable[..., Awaitable[ModelT]]]
    delete_fn: ClassVar[Callable[[ModelT], Awaitable[None]]]

    not_found_message: ClassVar[str] = "Not found"
    conflict_message: ClassVar[str] = "Already exists"
    deleted_message: ClassVar[str] = "Deleted"

    async def get_object(self, obj_id: int) -> ModelT:
        return await aget_or_404(self.get_fn(obj_id), self.not_found_message)


class ListModelMixin:
    def list(self) -> Any:
        return self.list_fn()


class RetrieveModelMixin:
    async def retrieve(self, obj_id: int) -> Any:
        return await self.get_object(obj_id)


class CreateModelMixin:
    async def create(self, payload: Schema) -> Any:
        try:
            return await self.create_fn(**payload.dict())
        except IntegrityError:
            raise HttpError(409, self.conflict_message)


class UpdateModelMixin:
    async def update(self, obj_id: int, payload: Schema) -> Any:
        obj = await self.get_object(obj_id)
        try:
            return await self.update_fn(obj, **payload.dict(exclude_unset=True))
        except IntegrityError:
            raise HttpError(409, self.conflict_message)


class DestroyModelMixin:
    async def destroy(self, obj_id: int) -> dict[str, str]:
        obj = await self.get_object(obj_id)
        await self.delete_fn(obj)
        return {"detail": self.deleted_message}


# --- combined views, DRF's generics.py / ModelViewSet equivalents -----------


class ReadOnlyModelCrudView[ModelT: Model](ListModelMixin, RetrieveModelMixin, GenericCrudView[ModelT]):
    """list + retrieve only. Mirrors DRF's `ReadOnlyModelViewSet`."""


class ModelCrudView[ModelT: Model](
    ListModelMixin,
    RetrieveModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericCrudView[ModelT],
):
    """The full list/retrieve/create/update/destroy combo. Mirrors DRF's
    `ModelViewSet`. Every resource we have today needs all five, so this is
    the one actually used - `ReadOnlyModelCrudView` is here for the shape
    the day a read-only resource shows up."""
