# TODO - Meshtastic API

## Web UI

* [ ] Screen to list nodes
* [ ] Screen to view individual nodes
* [ ] Support DMs in channel viewer
* [ ] View packet by ID / UUID (no matter what type it is)

## Web Storage

* [ ] 

## Bot

* [ ] Store own messages in the database
* [ ] Start using API for persistence

## Build
* [ ] Build and smoke test docker image on pull request - copy from MeshBotUI
* [ ] Add version number and /status endpoint

## Done

* [x] Show reactions against the specific message
* [x] fix: respond to "test ..." as well as "test"
* [x] Store message replies in the database
* [x] Text color of messages
* [x] Fix 0 channel (get from the raw packet)
* [x] Channels are zero indexed (update the UI)
