import json
from typing import Any
from typing import Dict
from typing import Optional

from rich.table import Table

from ..authclient import AuthClient
from ..config import settings
from ..interface import BaseInterface
from ..interface import PrintInterface
from ..interface import RichConsoleInterface
from ..interface import RichJsonInterface
from ..response import check_response
from fractal.common.models import DatasetRead
from fractal.common.models import DatasetUpdate
from fractal.common.models import ResourceCreate
from fractal.common.models import ResourceRead


async def dataset_add_resource(
    client: AuthClient,
    *,
    project_id: int,
    dataset_id: int,
    path: str,
    glob_pattern: Optional[str] = "",
    **kwargs,
) -> BaseInterface:
    resource = ResourceCreate(path=path, glob_pattern=glob_pattern)

    res = await client.post(
        f"{settings.BASE_URL}/project/{project_id}/{dataset_id}",
        json=resource.dict(),
    )
    new_resource = check_response(
        res, expected_status_code=201, coerce=ResourceRead
    )
    return RichJsonInterface(retcode=0, data=new_resource.dict())


async def dataset_edit(
    client: AuthClient,
    *,
    project_id: int,
    dataset_id: int,
    dataset_update_dict: Dict[str, Any],
) -> BaseInterface:

    metadata_filename = dataset_update_dict.get("metadata")
    if metadata_filename == "none":
        dataset_update_dict.update(meta={})
    elif metadata_filename is not None:
        meta = json.loads(metadata_filename)
        dataset_update_dict.update(meta=meta)

    dataset_update = DatasetUpdate(**dataset_update_dict)
    payload = dataset_update.dict(exclude_unset=True)
    if not payload:
        return PrintInterface(retcode=1, output="Nothing to update")

    res = await client.patch(
        f"{settings.BASE_URL}/project/{project_id}/{dataset_id}",
        json=dataset_update.dict(exclude_unset=True),
    )
    new_dataset = check_response(
        res, expected_status_code=200, coerce=DatasetRead
    )
    return RichJsonInterface(retcode=0, data=new_dataset.dict())


async def dataset_show(
    client: AuthClient, *, project_id: int, dataset_id: int, **kwargs
) -> BaseInterface:
    res = await client.get(
        f"{settings.BASE_URL}/dataset/{project_id}/{dataset_id}"
    )
    from devtools import debug
    from rich.console import Group


    debug(res.json())
    dataset = check_response(res, expected_status_code=200, coerce=DatasetRead)

    if kwargs.get("json", False):
        return RichJsonInterface(retcode=0, data=dataset.dict())
    else:
        table = Table(title="Dataset")
        table.add_column("Id", style="cyan", no_wrap=True)
        table.add_column("Name", justify="right", style="green")
        table.add_column("Type", style="white")
        table.add_column("Meta", justify="center")
        table.add_column("Read only", justify="center")

        table.add_row(
            str(dataset.id),
            dataset.name,
            dataset.type,
            json.dumps(dataset.meta, indent=2),
            "✅" if dataset.read_only else "❌",
        )
        table_res = Table(title="Resources")
        table_res.add_column("Resource List", justify="center", style="yellow")
        table_res.add_row(*dataset.resource_list)
        group = Group(table, table_res)
        return RichConsoleInterface(retcode=0, data=group)
