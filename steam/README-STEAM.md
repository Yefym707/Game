# Steam build guide

This folder contains templates and notes for uploading builds to Steam.

## Installing `steamcmd`

1. Download the tool from <https://developer.valvesoftware.com/wiki/SteamCMD>.
2. Extract the archive and ensure the `steamcmd` binary is available in your `PATH`.

## AppID and DepotIDs

* Obtain the AppID of the game and the DepotIDs for each platform from the Steamworks dashboard.
* Export them before running the upload script:

```
export STEAM_APP_ID="<appid>"
export STEAM_DEPOT_WIN="<depotid>"
export STEAM_DEPOT_MAC="<depotid>"
export STEAM_DEPOT_LINUX="<depotid>"
```

## Keeping the account safe

Never store credentials in the repository.  Instead define these environment
variables before uploading:

```
export STEAM_USERNAME="<login>"
export STEAM_PASSWORD="<password>"
export STEAM_GUARD="<guard code>"
```

The script `scripts/steam_upload.py` reads the variables directly and does not
print them to the console.

