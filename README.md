# FGB Metdata Injector

A simple command line tool that inserts specific metadata into a Flatgeobuf.

```
> python inject-metadata.py --help

Usage: inject-metadata.py [OPTIONS] FGB_FILE_PATH METADATA_FILE_PATH

Options:
  --help  Show this message and exit.
```

Provide a JSON file in the following format:

```
{
  "index_column": "NUTS_ID",
  "rendered_columns": [
    "Tree cover",
    ...
  ]
}
```

The program will check the specified columns exist in the input Flatgeobuf, and then write it into the
header metadata block.

Note: The `rendered_columns` field is specified as a list, but Flatgeobuf metadata can only be simple
key-values pairs of strings, so the list is serialized as a quoted and escaped comma-separated string.

Note: The input file gets overwritten, so existing metadata will be lost.

TODO:
- Refuse to overwrite existing metadata by default.
- Add a switch to either extend or overwrite any existing metadata.
