import json
from pathlib import Path
import requests

INDEX_URL = (
    "https://dotnetcli.blob.core.windows.net/"
    "dotnet/release-metadata/releases-index.json"
)

BUCKET = Path("bucket")
BUCKET.mkdir(exist_ok=True)

session = requests.Session()


def get_json(url):
    r = session.get(url, timeout=60)
    r.raise_for_status()
    return r.json()


def write_manifest(name, manifest):
    with open(BUCKET / name, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")


# -----------------------------
# URL HELPERS
# -----------------------------

def runtime_url(version, arch):
    return (
        "https://dotnetcli.blob.core.windows.net/dotnet/"
        f"Runtime/{version}/dotnet-runtime-{version}-win-{arch}.exe"
    )


def desktop_runtime_url(version, arch):
    return (
        "https://dotnetcli.blob.core.windows.net/dotnet/"
        f"WindowsDesktop/{version}/windowsdesktop-runtime-{version}-win-{arch}.exe"
    )


def sdk_zip_url(version, arch):
    return (
        "https://dotnetcli.blob.core.windows.net/dotnet/"
        f"Sdk/{version}/dotnet-sdk-{version}-win-{arch}.zip"
    )


# -----------------------------
# INSTALLER SCRIPT (EXE ONLY)
# -----------------------------

def installer_script():
    return [
        "Expand-DarkArchive \"$dir\\$fname\" \"$dir\\extracted\" -Removal",
        "Get-ChildItem \"$dir\\extracted\\AttachedContainer\\*.msi\" | ForEach-Object { Expand-MsiArchive $_ \"$dir\" }",
        "Move-Item \"$dir\\dotnet\\*\" \"$dir\" -Force",
        "@('dotnet', 'extracted') | ForEach-Object { Remove-Item \"$dir\\$_\" -Recurse }"
    ]


# -----------------------------
# LOAD INDEX
# -----------------------------

index = get_json(INDEX_URL)

for channel in index["releases-index"]:

    v = channel["channel-version"]
    sdk_version = channel.get("latest-sdk")
    runtime_version = channel.get("latest-runtime")

    print(f"Processing {v}")

    # =========================================================
    # 1. RUNTIME (BASE)
    # =========================================================
    if runtime_version:

        runtime_manifest = {
            "version": runtime_version,
            "description": f".NET Runtime {v}",
            "homepage": "https://dotnet.microsoft.com/",
            "license": "MIT",

            "architecture": {
                "32bit": {
                    "url": runtime_url(runtime_version, "x86")
                },
                "64bit": {
                    "url": runtime_url(runtime_version, "x64")
                }
            },

            "depends": "dark",
            "bin": "dotnet.exe",

            "installer": {
                "script": installer_script()
            },

            "checkver": {
                "url": INDEX_URL,
                "jsonpath": (
                    "$.releases-index"
                    f"[?(@['channel-version']=='{v}')]"
                    "['latest-runtime']"
                )
            },

            "autoupdate": {
                "architecture": {
                    "32bit": {
                        "url": runtime_url("$version", "x86")
                    },
                    "64bit": {
                        "url": runtime_url("$version", "x64")
                    }
                },
                "hash": {
                    "mode": "extract",
                    "url": "https://dotnetcli.blob.core.windows.net/dotnet/checksums/$version-sha.txt"
                }
            }
        }

        write_manifest(f"dotnet-runtime-{v}.json", runtime_manifest)

    # =========================================================
    # 2. DESKTOP RUNTIME (WPF / WINFORMS)
    # =========================================================
    if runtime_version:

        desktop_manifest = {
            "version": runtime_version,
            "description": f".NET Desktop Runtime {v}",
            "homepage": "https://dotnet.microsoft.com/",
            "license": "MIT",

            "architecture": {
                "32bit": {
                    "url": desktop_runtime_url(runtime_version, "x86")
                },
                "64bit": {
                    "url": desktop_runtime_url(runtime_version, "x64")
                }
            },

            "depends": "dark",
            "bin": "dotnet.exe",

            "installer": {
                "script": installer_script()
            },

            "checkver": {
                "url": INDEX_URL,
                "jsonpath": (
                    "$.releases-index"
                    f"[?(@['channel-version']=='{v}')]"
                    "['latest-runtime']"
                )
            },

            "autoupdate": {
                "architecture": {
                    "32bit": {
                        "url": desktop_runtime_url("$version", "x86")
                    },
                    "64bit": {
                        "url": desktop_runtime_url("$version", "x64")
                    }
                },
                "hash": {
                    "mode": "extract",
                    "url": "https://dotnetcli.blob.core.windows.net/dotnet/checksums/$version-sha.txt"
                }
            }
        }

        write_manifest(f"dotnet-desktop-runtime-{v}.json", desktop_manifest)

    # =========================================================
    # 3. SDK (ZIP ONLY — CRITICAL FIX)
    # =========================================================
    if sdk_version:

        sdk_manifest = {
            "version": sdk_version,
            "description": f".NET SDK {v}",
            "homepage": "https://dotnet.microsoft.com/",
            "license": "MIT",

            "architecture": {
                "32bit": {
                    "url": sdk_zip_url(sdk_version, "x86")
                },
                "64bit": {
                    "url": sdk_zip_url(sdk_version, "x64")
                }
            },

            # IMPORTANT:
            # ZIP is auto-extracted by Scoop (NO MSI, NO SCRIPT)
            "bin": "dotnet.exe",

            "env_set": {
                "DOTNET_ROOT": "$dir"
            },

            "checkver": {
                "url": INDEX_URL,
                "jsonpath": (
                    "$.releases-index"
                    f"[?(@['channel-version']=='{v}')]"
                    "['latest-sdk']"
                )
            },

            "autoupdate": {
                "architecture": {
                    "32bit": {
                        "url": sdk_zip_url("$version", "x86")
                    },
                    "64bit": {
                        "url": sdk_zip_url("$version", "x64")
                    }
                },
                "hash": {
                    "mode": "extract",
                    "url": "https://dotnetcli.blob.core.windows.net/dotnet/checksums/$version-sha.txt"
                }
            }
        }

        write_manifest(f"dotnet-sdk-{v}.json", sdk_manifest)

print("Done.")