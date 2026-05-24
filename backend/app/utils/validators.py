from fastapi import HTTPException, UploadFile

ALLOWED_EXTENSIONS = {".csv", ".txt"}


def validate_file_extension(file: UploadFile) -> None:
    filename = file.filename or ""

    if "." not in filename:
        raise HTTPException(
            status_code=400,
            detail="File must have an extension: .csv or .txt",
        )

    extension = "." + filename.rsplit(".", 1)[-1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only .csv and .txt files are supported",
        )


def validate_xyz_columns(columns: list[str]) -> None:
    required_columns = {"x", "y", "z"}
    existing_columns = {column.lower() for column in columns}

    missing_columns = required_columns - existing_columns

    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(sorted(missing_columns))}",
        )