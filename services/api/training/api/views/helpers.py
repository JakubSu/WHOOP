from typing import Any, cast

from rest_framework.serializers import BaseSerializer


def validated_data_as_dict(serializer: BaseSerializer[Any]) -> dict[str, Any]:
    return cast(dict[str, Any], serializer.validated_data)
