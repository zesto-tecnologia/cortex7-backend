from typing import List
from fastapi import HTTPException

from fastapi import UploadFile


def validate_files(
    field,
    nullable: bool,
    multiple: bool,
    max_size: int,
    accepted_types: List[str],
):

    if field:
        files: List[UploadFile] = field if multiple else [field]
        for each_file in files:
            if (max_size * 1024 * 1024) < each_file.size:
                raise HTTPException(
                    400,
                    detail=f"File '{each_file.filename}' exceeded max upload size of {max_size} MB",
                )
            elif each_file.content_type not in accepted_types:
                raise HTTPException(
                    400,
                    detail=f"File '{each_file.filename}' not accepted. Accepted types: {accepted_types}",
                )

    elif not (field or nullable):
        raise HTTPException(400, detail="File must be provided.")
