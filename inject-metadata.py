import csv
from io import StringIO
import json
from pathlib import Path

import click
from osgeo import ogr
from pydantic import BaseModel, ValidationError, field_serializer


class MissingColumn(Exception):
    pass


class Metadata(BaseModel):
    index_column: str
    rendered_columns: list[str]

    # FGB metadata fields can only be strings.
    @field_serializer("rendered_columns")
    def serialize_rendered_columns(self, v, _):
        # Use CSV which handles quoting and escaped characters better than I can.
        s = StringIO()
        csv_writer = csv.writer(s, quotechar="'", quoting=csv.QUOTE_ALL, lineterminator="")
        csv_writer.writerow(v)
        return s.getvalue()


@click.command()
@click.argument("fgb_file_path", type=click.Path(exists=True))
@click.argument("metadata_file_path", type=click.Path(exists=True))
def inject_metadata(fgb_file_path: str, metadata_file_path: str):
    fgb_file_path = Path(fgb_file_path)
    metadata_file_path = Path(metadata_file_path)

    try:
        j = json.load(metadata_file_path.open())
        metadata = Metadata.model_validate(j)
    except ValidationError as e:
        raise

    if not fgb_file_path.exists():
        raise FileNotFoundError(f"Input file '{fgb_file_path}' not found")
    if fgb_file_path.suffix != ".fgb":
        raise ValueError(f"Input file '{fgb_file_path}' is not a FlatGeobuf file")
    if not metadata_file_path.exists():
        raise FileNotFoundError(f"Metadata file '{metadata_file_path}' not found")

    src_ds = ogr.Open(fgb_file_path)
    src_layer = src_ds.GetLayer()

    # Check columns exist in the input file.
    defn = src_layer.GetLayerDefn()

    if defn.GetFieldIndex(metadata.index_column) == -1:
        raise MissingColumn(f"Index column '{metadata.index_column}' not found in {fgb_file_path}")

    for column in metadata.rendered_columns:
        if defn.GetFieldIndex(column) == -1:
            raise MissingColumn(f"Column '{column}' not found in {fgb_file_path}")

    # Overwrite the input file.
    driver = ogr.GetDriverByName("FlatGeobuf")
    dst_ds = driver.CreateDataSource(fgb_file_path)
    dst_ds.CopyLayer(src_layer, src_layer.GetName())

    print(f"Metadata injected into {fgb_file_path}")
    print(f"{metadata}")

    # We serialize the metadata to a string to take advantage of Pydantic's field serializer,
    # then load it back up as a regular Python object so OGR can set the metadata.
    dst_ds.SetMetadata(json.loads(metadata.model_dump_json()))

    dst_ds = None
    src_ds = None


if __name__ == "__main__":
    inject_metadata()
