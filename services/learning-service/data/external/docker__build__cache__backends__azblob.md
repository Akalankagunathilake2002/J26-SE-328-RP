<!-- role: DevOps Engineer -->
<!-- topic: Docker Build: Cache -->
<!-- source: Docker Documentation -->
<!-- license: Apache-2.0 -->
<!-- url: https://docs.docker.com/build/cache/backends/azblob/ -->
# Azure Blob Storage cache

Manage build cache with Azure blob storage

The `azblob` cache store uploads your resulting build cache to
Azure's blob storage service.

This cache storage backend is not supported with the default `docker` driver.
To use this feature, create a new builder using a different driver. See
Build drivers for more information.

## Synopsis

```console
$ docker buildx build --push -t / \
  --cache-to type=azblob,name=[,parameters...] \
  --cache-from type=azblob,name=[,parameters...] .
```

The following table describes the available CSV parameters that you can pass to
`--cache-to` and `--cache-from`.

| Name                | Option                  | Type        | Default | Description                                        |
| ------------------- | ----------------------- | ----------- | ------- | -------------------------------------------------- |
| `name`              | `cache-to`,`cache-from` | String      |         | Required. The name of the cache image.             |
| `account_url`       | `cache-to`,`cache-from` | String      |         | Base URL of the storage account.                   |
| `secret_access_key` | `cache-to`,`cache-from` | String      |         | Blob storage account key, see authentication. |
| `mode`              | `cache-to`              | `min`,`max` | `min`   | Cache layers to export, see cache mode.       |
| `ignore-error`      | `cache-to`              | Boolean     | `false` | Ignore errors caused by failed cache exports.      |

## Authentication

The `secret_access_key`, if left unspecified, is read from environment variables
on the BuildKit server following the scheme for the
Azure Go SDK.
The environment variables are read from the server, not the Buildx client.

## Further reading

For an introduction to caching see Docker build cache.

For more information on the `azblob` cache backend, see the
BuildKit README.
